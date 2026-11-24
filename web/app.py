"""Prototipo web LAIA: python -m web.app desde la raíz del proyecto.

Conserva los asistentes y el RAG existentes; el enrutamiento es interno.
Uso local monousuario únicamente. No desplegar sin autenticación y endurecimiento.
"""
import os
from pathlib import Path
from threading import Lock

from dotenv import load_dotenv
from flask import Flask, jsonify, render_template, request

from core.assistant import Assistant
from core.models.groq_provider import GroqProvider
from core.models.ollama_provider import OllamaProvider
from core.rag.rag_service import RAGService
from core.rag.graph.multidocument_service import MultiDocumentGraphRAGService
from web.router import route_query, normalize

ROOT = Path(__file__).resolve().parents[1]
load_dotenv(ROOT / '.env')
app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024
_lock = Lock()
_teacher_sessions = {}  # solo servidor local monousuario
_pending = {}  # (role, provider) -> {'message', 'reason'}
_last_scope = {}  # (role, provider) -> último ámbito explícito durante la sesión


def make_provider(name):
    if name == 'groq':
        if not os.getenv('GROQ_API_KEY'):
            raise RuntimeError('Configura GROQ_API_KEY en .env.')
        return GroqProvider(model='qwen/qwen3.8-27b')
    if name == 'ollama':
        return OllamaProvider(model='gemma3:1b')
    raise ValueError('Proveedor no válido.')


def _decode_clarification(reply, original, reason):
    """Retorna (mensaje_completo, preferencia_ambito, modo_forzado) o None."""
    answer = normalize(reply).strip().strip('.!')
    scope = {'pregrado': 'pregrado', 'posgrado': 'posgrado',
             'postgrado': 'posgrado', 'general': 'general'}.get(answer)
    if reason in ('ambito_no_claro', 'ambos_ambitos'):
        if scope:
            return original + ' (' + scope + ')', scope, None
        return None
    if reason in ('intencion_ambigua', 'intencion_no_clara'):
        if answer in ('pedagogica', 'pedagogico', 'actividad', 'docencia', 'pedagogia'):
            return original, None, 'pedagogical'
        if answer in ('documental', 'documentos', 'institucional', 'reglamento', 'rag'):
            return original, None, 'rag'
    return None


@app.get('/')
def home():
    return render_template('index.html')


@app.post('/api/chat')
def chat():
    payload = request.get_json(silent=True) or {}
    question = str(payload.get('message', '')).strip()
    role = payload.get('role')
    provider_name = payload.get('provider')
    rag_engine = payload.get('rag_engine', 'naive')
    if not question or len(question) > 3000:
        return jsonify(error='Escribe una pregunta de 1 a 3000 caracteres.'), 400
    if role not in ('estudiante', 'docente') or provider_name not in ('groq', 'ollama') or rag_engine not in ('naive', 'graph'):
        return jsonify(error='Asistente, proveedor o motor RAG no válido.'), 400

    key = (role, provider_name, rag_engine)
    try:
        with _lock:
            force_mode = None
            forced_scope = None
            pending = _pending.pop(key, None)
            if pending:
                decoded = _decode_clarification(question, pending['message'], pending['reason'])
                if decoded:
                    question, forced_scope, force_mode = decoded
                else:
                    # Se trata como una nueva pregunta en lugar de unirla a una aclaración incorrecta.
                    pass
            route = route_query(question, role, preferred_scope=forced_scope or _last_scope.get(key))
            if force_mode:
                route = type(route)(kind=force_mode, scope=forced_scope, reason='aclarado_por_usuario')
            if route.kind == 'clarify':
                _pending[key] = {'message': question, 'reason': route.reason}
                return jsonify(answer=route.message, sources=[], routing='clarification', warning='')

            provider = make_provider(provider_name)
            if route.kind == 'pedagogical':
                if key not in _teacher_sessions:
                    _teacher_sessions[key] = Assistant(ROOT / 'assistants' / 'docente', provider)
                answer = _teacher_sessions[key].chat(question)
                return jsonify(answer=answer, sources=[], routing='pedagogical', warning='')

            # El estudiante nunca cae en el modo generativo sin evidencia.
            if route.scope is None:
                _pending[key] = {'message': question, 'reason': 'ambito_no_claro'}
                return jsonify(answer='¿La consulta es de pregrado o posgrado?', sources=[], routing='clarification')
            rag = (MultiDocumentGraphRAGService(provider=provider)
                   if rag_engine == 'graph' else RAGService(provider=provider))
            result = rag.ask(question, route.scope, assistant_type=role)
            if route.reason in ('ambito_explicito', 'ambito_del_contexto', 'aclarado_por_usuario'):
                _last_scope[key] = route.scope
            return jsonify(answer=result['answer'], sources=result.get('sources', []),
                           warning=result.get('warning', ''), routing='documentary', rag_engine=rag_engine)
    except Exception as exc:
        app.logger.exception('Error de consulta LAIA')
        return jsonify(error=f'Error de consulta ({type(exc).__name__}). Revisa la terminal local.'), 500


@app.post('/api/reset')
def reset():
    payload = request.get_json(silent=True) or {}
    role = payload.get('role')
    provider_name = payload.get('provider')
    rag_engine = payload.get('rag_engine', 'naive')
    if role not in ('estudiante', 'docente') or provider_name not in ('groq', 'ollama') or rag_engine not in ('naive', 'graph'):
        return jsonify(error='Selección inválida.'), 400
    key = (role, provider_name, rag_engine)
    with _lock:
        assistant = _teacher_sessions.pop(key, None)
        if assistant:
            assistant.reset()
        _pending.pop(key, None)
        _last_scope.pop(key, None)
    return jsonify(ok=True)


if __name__ == '__main__':
    app.run(host='127.0.0.1', port=5000, debug=False)
