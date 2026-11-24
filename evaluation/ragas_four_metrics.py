"""Cuatro métricas Ragas 0.4; sin regenerar respuestas de LAIA.
Ejemplo: python -m evaluation.ragas_four_metrics --case PRE-01 --metric faithfulness
         python -m evaluation.ragas_four_metrics --case PRE-01 --metric all
Las métricas con reference requieren revisión humana de esa respuesta.
"""
import argparse
import asyncio
import hashlib
import json
import os
from datetime import datetime, timezone
from pathlib import Path

from dotenv import load_dotenv
from instructor import Mode
from openai import AsyncOpenAI
from ragas.llms import llm_factory
from ragas.metrics.collections import (
    Faithfulness, ContextPrecision, ContextRecall, AnswerRelevancy
)

ROOT = Path(__file__).resolve().parents[1]
INPUT_FILE = ROOT / 'evaluation' / 'results' / 'ragas_first_run.json'
REFERENCES_FILE = ROOT / 'evaluation' / 'references.json'
OUTPUT_FILE = ROOT / 'evaluation' / 'results' / 'ragas_four_metrics.json'
JUDGE = 'openai/gpt-oss-20b'
EMBED_MODEL = 'sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2'
METRIC_NAMES = ('faithfulness', 'answer_relevancy', 'context_precision', 'context_recall')


def write_json_atomic(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix('.tmp')
    temporary.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding='utf-8')
    temporary.replace(path)


def read_json(path):
    if not path.exists():
        raise FileNotFoundError(f'No existe {path}')
    return json.loads(path.read_text(encoding='utf-8'))


def fingerprint(case, reference):
    payload = {'question': case['question'], 'answer': case['answer'],
               'contexts': case['retrieved_contexts'], 'reference': reference,
               'judge': JUDGE, 'embedding': EMBED_MODEL}
    return hashlib.sha256(json.dumps(payload, ensure_ascii=False, sort_keys=True).encode()).hexdigest()


async def main(case_id, metric_option):
    load_dotenv(ROOT / '.env')
    source = read_json(INPUT_FILE)
    cases = source.get('cases', {})
    if case_id not in cases:
        raise ValueError(f'Caso {case_id} inexistente. Disponibles: {list(cases)}')
    case = cases[case_id]
    reference = read_json(REFERENCES_FILE).get(case_id, {}).get('reference', '').strip()
    if not case.get('answer') or not case.get('retrieved_contexts'):
        raise ValueError('El caso requiere answer y retrieved_contexts guardados.')
    key = fingerprint(case, reference)
    saved = read_json(OUTPUT_FILE) if OUTPUT_FILE.exists() else {'cases': {}}
    saved.setdefault('cases', {})
    current = saved['cases'].get(case_id, {})
    if current.get('fingerprint') != key:
        current = {'fingerprint': key, 'question': case['question'],
                   'judge': JUDGE, 'embedding_model': EMBED_MODEL, 'metrics': {}}
        saved['cases'][case_id] = current
        write_json_atomic(OUTPUT_FILE, saved)

    selected = METRIC_NAMES if metric_option == 'all' else (metric_option,)
    pending = []
    for name in selected:
        if current['metrics'].get(name, {}).get('score') is not None:
            print(f'{name}: {current["metrics"][name]["score"]:.4f} (guardado)')
        elif name in {'context_precision', 'context_recall'} and not reference:
            print(f'{name}: PENDIENTE — escribe referencia verificada en evaluation/references.json')
        else:
            pending.append(name)
    if not pending:
        print(f'Archivo: {OUTPUT_FILE}')
        return
    if not os.getenv('GROQ_API_KEY'):
        raise RuntimeError('Configura GROQ_API_KEY en .env')
    client = AsyncOpenAI(api_key=os.environ['GROQ_API_KEY'],
                         base_url='https://api.groq.com/openai/v1',
                         max_retries=0, timeout=90)
    llm = llm_factory(JUDGE, provider='openai', client=client,
                      mode=Mode.MD_JSON, max_tokens=1200,
                      reasoning_effort='low', temperature=0)

    for name in pending:
        print(f'\n{case_id} | {name}: calculando...')
        try:
            if name == 'faithfulness':
                scorer = Faithfulness(llm=llm)
                result = await scorer.ascore(user_input=case['question'],
                                             response=case['answer'],
                                             retrieved_contexts=case['retrieved_contexts'])
            elif name == 'context_precision':
                scorer = ContextPrecision(llm=llm)
                result = await scorer.ascore(user_input=case['question'],
                                             reference=reference,
                                             retrieved_contexts=case['retrieved_contexts'])
            elif name == 'context_recall':
                scorer = ContextRecall(llm=llm)
                result = await scorer.ascore(user_input=case['question'],
                                             reference=reference,
                                             retrieved_contexts=case['retrieved_contexts'])
            else:
                # Los embeddings se usan para evaluar relevancia, NO para recuperar en LAIA.
                # La primera vez descarga un modelo multilingüe; puede tardar y ocupar disco.
                from ragas.embeddings.huggingface_provider import HuggingFaceEmbeddings
                embeddings = HuggingFaceEmbeddings(model=EMBED_MODEL, device='cpu')
                scorer = AnswerRelevancy(llm=llm, embeddings=embeddings)
                result = await scorer.ascore(user_input=case['question'],
                                             response=case['answer'])
            current['metrics'][name] = {'score': float(result.value),
                                        'error': None,
                                        'evaluated_at': datetime.now(timezone.utc).isoformat()}
            print(f'{name}: {float(result.value):.4f}')
        except Exception as exc:
            current['metrics'][name] = {'score': None,
                                        'error': f'{type(exc).__name__}: {exc}',
                                        'evaluated_at': datetime.now(timezone.utc).isoformat()}
            print(f'{name}: ERROR {type(exc).__name__}: {exc}')
            write_json_atomic(OUTPUT_FILE, saved)
            print('Detenido para evitar gasto de cuota; los resultados previos se conservan.')
            break
        write_json_atomic(OUTPUT_FILE, saved)
    print(f'\nResultados: {OUTPUT_FILE}')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--case', default='PRE-01')
    parser.add_argument('--metric', choices=(*METRIC_NAMES, 'all'), default='faithfulness')
    args = parser.parse_args()
    asyncio.run(main(args.case, args.metric))
