"""Interfaz local LAIA. Ejecutar: python -m web.app desde la raíz del repositorio."""
from pathlib import Path
from threading import Lock
import os

from dotenv import load_dotenv
from flask import Flask, jsonify, render_template, request

from core.assistant import Assistant
from core.models.groq_provider import GroqProvider
from core.models.ollama_provider import OllamaProvider
from core.rag.rag_service import RAGService

ROOT = Path(__file__).resolve().parents[1]
load_dotenv(ROOT / '.env')
app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024

# Solo para demo local de un usuario; no exponer en Internet.
_lock = Lock()
_teacher_sessions = {}

def make_provider(name):
    if name == 'groq':
        if not os.getenv('GROQ_API_KEY'):
            raise RuntimeError('Configura GROQ_API_KEY en el archivo .env.')
        return GroqProvider(model='qwen/qwen3.8-27b')
    if name == 'ollama':
        return OllamaProvider(model='gemma3:1b')
    raise ValueError('Proveedor no válido.')

@app.get('/')
def home():
    return render_template('index.html')

@app.post('/api/chat')
def chat():
    payload = request.get_json(silent=True) or {}
    question = str(payload.get('message', '')).strip()
    role = payload.get('role')
    provider_name = payload.get('provider')
    scope = payload.get('scope')
    mode = payload.get('mode')
    if not question or len(question) > 3000:
        return jsonify(error='Escribe una pregunta de 1 a 3000 caracteres.'), 400
    if role not in {'estudiante', 'docente'} or provider_name not in {'groq', 'ollama'}:
        return jsonify(error='Selección de asistente/proveedor no válida.'), 400
    if scope not in {'pregrado', 'posgrado', 'general'}:
        return jsonify(error='Ámbito no válido.'), 400
    try:
        with _lock:
            provider = make_provider(provider_name)
            if role == 'docente' and mode == 'pedagogico':
                # Cada proveedor conserva su propia conversación docente.
                if provider_name not in _teacher_sessions:
                    _teacher_sessions[provider_name] = Assistant(ROOT / 'assistants' / 'docente', provider)
                answer = _teacher_sessions[provider_name].chat(question)
                return jsonify(answer=answer, sources=[], warning='Modo pedagógico: sin recuperación documental.')
            if role == 'estudiante' and mode != 'documental':
                return jsonify(error='El estudiante utiliza exclusivamente el modo documental.'), 400
            if role == 'docente' and mode != 'documental':
                return jsonify(error='Modo inválido.'), 400
            rag = RAGService(provider=provider)
            result = rag.ask(question, scope, assistant_type=role)
            return jsonify(answer=result['answer'], sources=result.get('sources', []), warning=result.get('warning', ''))
    except Exception as exc:
        # No exponer secretos ni trazas internas al navegador.
        app.logger.exception('Error de consulta LAIA')
        return jsonify(error=f'Error de consulta ({type(exc).__name__}). Revisa la terminal del servidor.'), 500

@app.post('/api/reset')
def reset():
    payload = request.get_json(silent=True) or {}
    provider_name = payload.get('provider')
    if provider_name not in {'groq', 'ollama'}:
        return jsonify(error='Proveedor no válido.'), 400
    with _lock:
        assistant = _teacher_sessions.pop(provider_name, None)
        if assistant:
            assistant.reset()
    return jsonify(ok=True)

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=5000, debug=False)
