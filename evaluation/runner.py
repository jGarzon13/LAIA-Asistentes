
import json
import time
from datetime import datetime, timezone
from pathlib import Path

from core.assistant import Assistant
from core.models.ollama_provider import OllamaProvider


ROOT = Path(__file__).resolve().parents[1]
CASES_FILE = ROOT / "evaluation" / "cases.json"
OUTPUT_DIR = ROOT / "docs" / "evaluaciones"


def load_cases():
    with open(CASES_FILE, encoding="utf-8") as file:
        return json.load(file)


def evaluate_case(case, provider):
    assistant_path = ROOT / "assistants" / case["assistant"]

    # Instancia nueva para evitar mezclar conversaciones
    assistant = Assistant(assistant_path, provider)

    print(f"\nEjecutando {case['id']}")
    print(f"Asistente: {assistant.name}")

    start = time.perf_counter()

    try:
        response = assistant.chat(case["prompt"])
        elapsed = round(time.perf_counter() - start, 2)

        # Comprobación básica de términos esperados.
        # No equivale a una validación de calidad académica.
        keyword_checks = {
            term: term.casefold() in response.casefold()
            for term in case.get("required_terms", [])
        }

        return {
            **case,
            "model": provider.model,
            "status": "COMPLETADA",
            "response": response,
            "elapsed_seconds": elapsed,
            "keyword_checks": keyword_checks,
            "requires_human_review": True,
            "academic_verdict": "PENDIENTE_REVISION",
            "error": None
        }

    except (RuntimeError, ValueError, OSError) as exc:
        elapsed = round(time.perf_counter() - start, 2)

        return {
            **case,
            "model": provider.model,
            "status": "ERROR",
            "response": "",
            "elapsed_seconds": elapsed,
            "keyword_checks": {},
            "requires_human_review": True,
            "academic_verdict": "NO_EVALUADO",
            "error": str(exc)
        }


def save_json(results, path):
    with open(path, "w", encoding="utf-8") as file:
        json.dump(
            results,
            file,
            indent=2,
            ensure_ascii=False
        )


def save_markdown(results, path):
    lines = [
        "# LAIA - Evaluación local de asistentes",
        "",
        f"Fecha UTC: {results['executed_at']}",
        f"Modelo: {results['model']}",
        "",
        "## Resumen",
        "",
        f"- Casos ejecutados: {len(results['cases'])}",
        f"- Ejecuciones completadas: {results['completed']}",
        f"- Errores técnicos: {results['errors']}",
        "- Evaluación académica: pendiente de revisión humana",
        "",
        "## Casos evaluados",
        ""
    ]

    for case in results["cases"]:
        lines.extend([
            f"### {case['id']} - {case['category']}",
            "",
            f"**Asistente:** {case['assistant']}",
            f"**Estado técnico:** {case['status']}",
            f"**Tiempo:** {case['elapsed_seconds']} segundos",
            f"**Resultado académico:** {case['academic_verdict']}",
            "",
            "**Consulta enviada:**",
            "",
            case["prompt"],
            "",
            "**Comportamiento esperado:**",
            "",
            case["expected_behavior"],
            "",
            "**Respuesta obtenida:**",
            ""
        ])

        if case["error"]:
            lines.append(f"Error técnico: {case['error']}")
        else:
            lines.append(case["response"])

        lines.extend([
            "",
            "**Comprobaciones de términos:**",
            ""
        ])

        if case["keyword_checks"]:
            for term, found in case["keyword_checks"].items():
                result = "Encontrado" if found else "No encontrado"
                lines.append(f"- {term}: {result}")
        else:
            lines.append("Sin términos configurados.")

        lines.extend([
            "",
            "**Criterios para revisión humana:**",
            ""
        ])

        for criterion in case["review_criteria"]:
            lines.append(f"- [ ] {criterion}")

        lines.extend([
            "",
            "**Observaciones del evaluador:** Pendiente",
            "",
            "---",
            ""
        ])

    path.write_text("\n".join(lines), encoding="utf-8")


def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    cases = load_cases()
    provider = OllamaProvider(model="gemma3:1b")

    print("=" * 55)
    print("LAIA - Evaluador local de asistentes")
    print("=" * 55)
    print(f"Modelo: {provider.model}")
    print(f"Casos disponibles: {len(cases)}")

    results = []

    for case in cases:
        result = evaluate_case(case, provider)
        results.append(result)

        print(f"Estado: {result['status']}")
        print(f"Tiempo: {result['elapsed_seconds']} s")

        if result["error"]:
            print(f"Detalle: {result['error']}")

    completed = sum(
        case["status"] == "COMPLETADA"
        for case in results
    )

    errors = len(results) - completed

    report = {
        "executed_at": datetime.now(
            timezone.utc
        ).isoformat(),
        "model": provider.model,
        "completed": completed,
        "errors": errors,
        "cases": results
    }

    timestamp = datetime.now().strftime(
        "%Y%m%d_%H%M%S"
    )

    json_path = OUTPUT_DIR / f"evaluation_{timestamp}.json"
    md_path = OUTPUT_DIR / f"evaluation_{timestamp}.md"

    save_json(report, json_path)
    save_markdown(report, md_path)

    print("\n" + "=" * 55)
    print("RESUMEN")
    print(f"Casos: {len(results)}")
    print(f"Completados: {completed}")
    print(f"Errores: {errors}")
    print("Calidad académica: pendiente de revisión")
    print(f"\nJSON: {json_path}")
    print(f"Markdown: {md_path}")


if __name__ == "__main__":
    main()
