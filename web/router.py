"""Router híbrido: chat libre, pedagogía y documentos institucionales."""
import re
import unicodedata
from dataclasses import dataclass


def normalize(text: str) -> str:
    text = unicodedata.normalize('NFKD', text.lower())
    return ''.join(ch for ch in text if not unicodedata.combining(ch))


@dataclass(frozen=True)
class Route:
    kind: str  # chat, pedagogical, rag, clarify
    scope: str | None = None
    message: str = ''
    reason: str = ''


PEDAGOGICAL = (
    'disena una actividad', 'crea una actividad', 'planea una clase',
    'plan de clase', 'secuencia didactica', 'estrategia pedagogica',
    'rubrica', 'objetivos de aprendizaje', 'actividad didactica',
    'como ensenar', 'material didactico', 'taller de clase',
    'prepara una clase', 'elabora una actividad', 'aprendizaje activo',
    'cuestionario para mis estudiantes', 'examen de python',
    'quiz de python', 'actividad docente', 'actividad pedagogica',
)

# Expresiones documentales específicas; evitar palabras genéricas como 'grado'
# que podrían crear falsos positivos en un chat ordinario.
DOCUMENTARY = (
    'reglamento', 'resolucion', 'normativa', 'norma institucional',
    'politica institucional', 'procedimiento institucional',
    'requisitos', 'creditos academicos', 'credito academico',
    'saber pro', 'graduar', 'graduarme', 'graduarse', 'graduacion', 'titulo profesional',
    'matricula', 'homologacion', 'reintegro', 'admisiones',
    'registro academico', 'calendario academico',
    'derechos del estudiante', 'deberes del estudiante',
    'tramite academico', 'tesis doctoral', 'trabajo de grado',
    'que establece', 'que dice el documento', 'segun la universidad',
    'segun la uao', 'documentos institucionales',
    'informacion institucional', 'consultar informacion institucional',
    'politica de proteccion de datos', 'codigo de etica',
)
GENERAL_DOCUMENTS = (
    'proteccion de datos', 'datos personales', 'codigo de etica',
    'politica institucional', 'politicas institucionales',
)


def contains_phrase(text: str, phrase: str) -> bool:
    return bool(re.search(r'(?<!\w)' + re.escape(phrase) + r'(?!\w)', text))


def route_query(message: str, role: str, *, preferred_scope: str | None = None) -> Route:
    if role not in ('docente', 'estudiante'):
        raise ValueError('Rol inválido.')
    text = normalize(message)
    is_ped = any(contains_phrase(text, p) for p in PEDAGOGICAL)
    is_doc = any(contains_phrase(text, p) for p in DOCUMENTARY)
    is_general = any(contains_phrase(text, p) for p in GENERAL_DOCUMENTS)
    pre = bool(re.search(r'\bpregrado\b|\bpre-grado\b', text))
    post = bool(re.search(r'\bposgrado\b|\bpostgrado\b|\bmaestria\b|\bdoctorado\b|\bespecializacion\b', text))

    # Expresiones documentales de ámbito general, incluso si el usuario no
    # escribe explícitamente 'reglamento'.
    is_doc = is_doc or is_general or pre or post

    if role == 'docente' and is_ped and is_doc:
        return Route('clarify', message='¿Quieres preparar una actividad pedagógica o consultar la normativa institucional?', reason='intencion_ambigua')
    if role == 'docente' and is_ped:
        return Route('pedagogical', reason='solicitud_pedagogica')

    if not is_doc:
        return Route('chat', reason='consulta_general')

    if pre and post:
        return Route('clarify', message='¿Quieres consultar la normativa de pregrado o la de posgrado?', reason='ambos_ambitos')
    if pre:
        return Route('rag', 'pregrado', reason='ambito_explicito')
    if post:
        return Route('rag', 'posgrado', reason='ambito_explicito')
    if is_general:
        return Route('rag', 'general', reason='politica_general')
    if preferred_scope in ('pregrado', 'posgrado', 'general'):
        return Route('rag', preferred_scope, reason='ambito_del_contexto')
    return Route('clarify', message='¿Tu consulta institucional es sobre pregrado, posgrado o una política general de la UAO?', reason='ambito_no_claro')
