import json
import tempfile
import unittest
from pathlib import Path

from core.rag.graph.multidocument_service import MultiDocumentGraphRAGService


class FakeProvider:
    def __init__(self):
        self.messages = None

    def generate(self, messages):
        self.messages = messages
        return 'Respuesta de prueba [FUENTE 1].'


class TestMultiDocumentGraphRAG(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        root = Path(self.tmp.name)
        self.index = root / 'chunks.json'
        self.metadata = root / 'metadata.json'
        self.graph = root / 'missing_graph.json'
        chunks = [
            dict(id='p-C0001', document_id='p', filename='pregrado.pdf',
                 page=1, text='Requisitos de graduación académica: créditos aprobados.',
                 requires_review=False),
            dict(id='p-C0002', document_id='p', filename='pregrado.pdf',
                 page=1, text='La prueba Saber Pro corresponde a otro requisito.',
                 requires_review=False),
            dict(id='q-C0001', document_id='q', filename='posgrado.pdf',
                 page=1, text='Requisitos de graduación académica de maestría.',
                 requires_review=False),
            dict(id='f-C0001', document_id='f', filename='procedimiento_academico_ficticio.txt',
                 page=1, text='Graduación inventada.', requires_review=False),
        ]
        self.index.write_text(json.dumps({'documents': [
            {'id':'p','filename':'pregrado.pdf','source_path':'pregrado.pdf'},
            {'id':'q','filename':'posgrado.pdf','source_path':'posgrado.pdf'},
            {'id':'f','filename':'procedimiento_academico_ficticio.txt','source_path':'procedimiento_academico_ficticio.txt'}],
            'chunks':chunks}), encoding='utf-8')
        self.metadata.write_text(json.dumps({'documents':{
            'pregrado.pdf':{'document_id':'p','effective':{'scope':'pregrado','validity':'vigente'}},
            'posgrado.pdf':{'document_id':'q','effective':{'scope':'posgrado','validity':'vigente'}},
            'procedimiento_academico_ficticio.txt':{'document_id':'f','effective':{'scope':'pregrado','validity':'vigente'}}
        }}), encoding='utf-8')
        self.provider = FakeProvider()
        self.service = MultiDocumentGraphRAGService(
            self.provider, index_file=self.index, metadata_file=self.metadata,
            graph_file=self.graph, top_k=1, max_contexts=3, min_score=0.01)

    def tearDown(self):
        self.tmp.cleanup()

    def test_pregrado_does_not_leak_other_scopes(self):
        result = self.service.ask('Requisitos de graduación', 'pregrado')
        names = {s['filename'] for s in result['sources']}
        self.assertEqual(names, {'pregrado.pdf'})
        self.assertEqual(result['status'], 'ok')
        self.assertLessEqual(len(result['sources']), 3)

    def test_graph_expands_to_neighbor(self):
        result = self.service.ask('créditos aprobados', 'pregrado')
        self.assertEqual([s['chunk_id'] for s in result['sources']],
                         ['p-C0001', 'p-C0002'])

    def test_no_evidence_does_not_call_provider(self):
        result = self.service.ask('termodinamica cuantica inventada', 'pregrado')
        self.assertEqual(result['status'], 'no_evidence')
        self.assertIsNone(self.provider.messages)

    def test_invalid_scope(self):
        result = self.service.ask('Requisitos', 'otro')
        self.assertEqual(result['status'], 'invalid_scope')
        self.assertIsNone(self.provider.messages)


if __name__ == '__main__':
    unittest.main()
