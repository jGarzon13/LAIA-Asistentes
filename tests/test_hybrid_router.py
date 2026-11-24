import unittest
from web.router import route_query

class TestHybridRouter(unittest.TestCase):
    def test_student_general_chat(self):
        self.assertEqual(route_query('¿Qué es Python?', 'estudiante').kind, 'chat')
    def test_teacher_general_chat(self):
        self.assertEqual(route_query('¿Puedes ayudarme?', 'docente').kind, 'chat')
    def test_teacher_activity(self):
        self.assertEqual(route_query('actividad docente', 'docente').kind, 'pedagogical')
    def test_teacher_activity_rag_ambiguity(self):
        self.assertEqual(route_query('Diseña una actividad según el reglamento de posgrado', 'docente').kind, 'clarify')
    def test_student_no_rag_fallback_for_general(self):
        self.assertEqual(route_query('Explícame las funciones cuadráticas', 'estudiante').kind, 'chat')
    def test_institutional_pregrado(self):
        r = route_query('¿Cómo graduarme de pregrado?', 'estudiante')
        self.assertEqual((r.kind, r.scope), ('rag', 'pregrado'))
    def test_institutional_posgrado(self):
        r = route_query('¿Qué dice el reglamento de posgrado?', 'docente')
        self.assertEqual((r.kind, r.scope), ('rag', 'posgrado'))
    def test_institutional_ambiguous(self):
        self.assertEqual(route_query('¿Qué debo hacer para graduarme?', 'estudiante').kind, 'clarify')
    def test_general_policy(self):
        r = route_query('¿Qué dice el código de ética?', 'estudiante')
        self.assertEqual((r.kind, r.scope), ('rag', 'general'))
    def test_preferred_scope_not_hijack_chat(self):
        r = route_query('Muchas gracias', 'estudiante', preferred_scope='pregrado')
        self.assertEqual(r.kind, 'chat')

if __name__ == '__main__':
    unittest.main()
