import unittest
from web.router import route_query


class TestWebRouter(unittest.TestCase):
    def test_teacher_pedagogical(self):
        route = route_query('Diseña una actividad de Python', 'docente')
        self.assertEqual(route.kind, 'pedagogical')

    def test_teacher_regulation(self):
        route = route_query('¿Qué dice el reglamento de posgrado sobre evaluaciones?', 'docente')
        self.assertEqual((route.kind, route.scope), ('rag', 'posgrado'))

    def test_student_ambiguous_scope(self):
        route = route_query('¿Qué debo hacer para graduarme?', 'estudiante')
        self.assertEqual(route.kind, 'clarify')

    def test_student_explicit_scope(self):
        route = route_query('¿Cómo graduarme de pregrado?', 'estudiante')
        self.assertEqual((route.kind, route.scope), ('rag', 'pregrado'))

    def test_general_policy(self):
        route = route_query('¿Qué dice la política de protección de datos personales?', 'estudiante')
        self.assertEqual((route.kind, route.scope), ('rag', 'general'))

    def test_teacher_ambiguous_intent(self):
        route = route_query('¿Puedes ayudarme?', 'docente')
        self.assertEqual(route.kind, 'clarify')

    def test_teacher_mixed_intent(self):
        route = route_query('Diseña una actividad según el reglamento de posgrado', 'docente')
        self.assertEqual(route.kind, 'clarify')

    def test_student_does_not_fallback_to_pedagogy(self):
        route = route_query('Diseña una actividad de Python', 'estudiante')
        self.assertNotEqual(route.kind, 'pedagogical')


if __name__ == '__main__':
    unittest.main()
