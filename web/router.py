"""Enrutamiento conservador de consultas LAIA.

No usa LLM, no inventa ámbitos y no decide vigencia de documentos.
"""
import re
import unicodedata
from dataclasses import dataclass


def normalize(text: str) -> str:
    text = unicodedata.normalize('NFKD', text.lower())
    return ''.join(ch for ch in text if not unicodedata.combining(ch))


@dataclass(frozen=True)
class Route:
    kind: str  # pedagogical, rag, clarify
    scope: str | None = None
    message: str = ''
    reason: str = ''


PEDAGOGICAL = (
    'disena una actividad', 'diseñar una actividad', 'crea una actividad',
    'planea una clase', 'plan de clase', 'planificacion de clase',
    'secuencia didactica', 'estrategia pedagogica', 'rubrica',
    'rubrica de evaluacion', 'objetivos de aprendizaje', 'actividad didactica',
    'como ensenar', 'como explicar', 'material didactico', 'taller de clase',
    'prepara una clase', 'elabora una actividad', 'aprendizaje activo',
    'cuestionario para mis estudiantes', 'examen de python', 'quiz de python'
)
DOC_KEYWORDS = (
    'reglamento', 'resolucion', 'normativa', 'norma institucional',
    'politica institucional', 'procedimiento institucional',
    'requisitos', 'credito academico', 'creditos academicos',
    'saber pro', 'grado', 'graduar', 'graduacion', 'titulo profesional',
    'matricula', 'homologacion', 'reintegro', 'admisiones',
    'registro academico', 'calendario academico', 'derechos del estudiante',
    'deberes del estudiante', 'posgrado', 'postgrado', 'pregrado',
    'que establece', 'que dice el documento', 'segun la universidad',
    'segun la uao', 'tesis doctoral', 'trabajo de grado'
)
GENERAL_KEYWORDS = ('proteccion de datos', 'datos personales', 'codigo de etica',
                    'politica institucional', 'politicas institucionales')


def route_query(message: str, role: str, *, preferred_scope: str | None = None) -> Route:
    if role not in ('docente', 'estudiante'):
        raise ValueError('Rol inválido.')
    text = normalize(message)
    normalized_ped = [normalize(item) for item in PEDAGOGICAL]
    is_ped = any(k in text for k in normalized_ped)
    is_doc = any(k in text for k in DOC_KEYWORDS)
    pre = bool(re.search(r'\bpregrado\b|\bpre-grado\b', text))
    post = bool(re.search(r'\bposgrado\b|\bpostgrado\b|\bmaestria\b|\bdoctorado\b|\bespecializacion\b', text))
    if pre and post:
        return Route('clarify', message='¿Quieres consultar la normativa de pregrado o la de posgrado?', reason='ambos_ambitos')
    if role == 'docente':
        if is_ped and not is_doc:
            return Route('pedagogical', reason='solicitud_pedagogica')
        if is_ped and is_doc:
            return Route('clarify', message='¿Quieres que prepare una actividad pedagógica o que consulte documentos institucionales?', reason='intencion_ambigua')
        if not is_doc:
            return Route('clarify', message='¿Quieres apoyo para una actividad docente o consultar información institucional?', reason='intencion_no_clara')
    if pre:
        return Route('rag', 'pregrado', reason='ambito_explicito')
    if post:
        return Route('rag', 'posgrado', reason='ambito_explicito')
    if any(k in text for k in GENERAL_KEYWORDS):
        return Route('rag', 'general', reason='politica_general')
    if preferred_scope in ('pregrado', 'posgrado', 'general'):
        return Route('rag', preferred_scope, reason='ambito_del_contexto')
    return Route('clarify', message='¿Tu consulta corresponde a pregrado o posgrado? Si es una política general de la UAO, puedes indicarlo.', reason='ambito_no_claro')
