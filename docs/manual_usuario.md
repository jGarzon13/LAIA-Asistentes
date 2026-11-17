# MANUAL DE USUARIO Y DESCRIPCIÓN TÉCNICA

## ASISTENTES ACADÉMICOS LAIA

Universidad Autónoma de Occidente | Prototipos locales Docente y Estudiante

## 1. Presentación y alcance

Este manual presenta la primera versión operativa de dos asistentes académicos de prueba —Docente y Estudiante—, construidos para explorar una definición estandarizada y portable de asistentes dentro de LAIA. Sirve como guía de uso, descripción de la arquitectura actual y referencia para las futuras decisiones de integración con LucIA.

El alcance probado corresponde a ejecución local por consola en Windows, Python y Ollama. No comprende autenticación institucional, consultas reales a Moodle, acceso a cursos, despliegue productivo, carga documental/RAG ni publicación de asistentes en LucIA.

## 2. Contexto institucional y relación entre sistemas

En la Fase I, LAIA fue definido como portal informativo y punto de entrada a iniciativas del Plan Táctico de IA de la UAO, incluyendo secciones de asistentes y agentes. La propuesta de LucIA presentada por Uninorte describe un portal institucional multimodelo y la creación de asistentes a partir de instrucciones (prompts) y archivos, con opciones de compartición. La UAO adquirió una licencia de LucIA, lo cual ha motivado el ajuste del trabajo del mes 2 hacia prototipos de asistentes y documentación.

El formato exacto para importar o recrear asistentes, las APIs disponibles y las condiciones de integración no han sido validados. Por ello, los prompts en Markdown y la configuración JSON constituyen una propuesta de representación independiente de plataforma, no un formato nativo confirmado de LucIA.

## 3. Inventario de asistentes

| Asistente | Público de prueba | Objetivo | Ejemplos de uso |
| --- | --- | --- | --- |
| LAIA — Asistente Docente | Docentes universitarios | Apoyar preparación de actividades, rúbricas y estrategias de enseñanza con IA | Actividad de 15 minutos; rúbrica de Python; retroalimentación formativa |
| LAIA — Asistente Estudiante | Estudiantes universitarios | Acompañar la comprensión de conceptos y el aprendizaje autónomo | Explicaciones con ejemplos; ejercicios; preguntas de comprensión |

### 3.1. Asistente Docente

Propone actividades de aprendizaje, resultados de aprendizaje, rúbricas y estrategias pedagógicas, con contexto universitario. Puede pedir asignatura, nivel y duración, o explicitar supuestos si estos datos no están disponibles. Debe comprobar las restricciones indicadas por el usuario y no atribuirse funciones institucionales que no tiene.

Ejemplo: «Diseña una actividad de aprendizaje activo de exactamente 15 minutos para enseñar variables en Python a estudiantes universitarios de primer semestre».

### 3.2. Asistente Estudiante

Explica contenidos con lenguaje accesible, ejemplos y preguntas de verificación. Promueve el razonamiento, el aprendizaje autónomo y la retroalimentación formativa. No sustituye a un docente, no accede a calificaciones ni a Moodle y no debe inventar notas ni políticas institucionales.

Ejemplo: «Explícame qué es una variable en Python con un ejemplo sencillo y hazme una pregunta para comprobar si entendí».

## 4. Arquitectura del prototipo

```text
Consola (main.py)
  → Assistant (core/assistant.py)
    → config.json + prompt.md (por asistente)
    → ModelProvider (core/models/base.py)
      → OllamaProvider (core/models/ollama_provider.py)
        → API local Ollama /api/chat → gemma3:1b
```

La interfaz común ModelProvider desacopla las instrucciones del proveedor. El módulo Assistant carga la identidad e instrucciones del asistente, gestiona mensajes y conserva una ventana acotada de historial. La implementación local OllamaProvider se comunica con el servicio de Ollama por HTTP. La reutilización de instrucciones en LucIA requerirá validar su soporte real, no se garantiza compatibilidad automática.

| Elemento | Archivo / ubicación | Responsabilidad |
| --- | --- | --- |
| Interfaz de consola | main.py | Menú, selección de asistente, interacción |
| Motor de asistente | core/assistant.py | Configuración, prompt y contexto |
| Contrato de proveedor | core/models/base.py | Interfaz abstracta generate(messages) |
| Adaptador Ollama | core/models/ollama_provider.py | Solicitud HTTP al modelo |
| Instrucciones | assistants/{docente,estudiante}/prompt.md | Rol, funciones, límites y formato de respuesta |
| Metadatos | assistants/{docente,estudiante}/config.json | Identificación, versión, público y modelo |
| Pruebas unitarias | tests/test_docente.py y test_estudiante.py | Pruebas de lógica con proveedores simulados |
| Evaluador funcional | evaluation/runner.py + cases.json | Casos reales, tiempos, respuestas y reportes |

## 5. Requisitos y preparación del entorno

- Windows con Python 3 instalado y terminal PowerShell o terminal integrada de VS Code.
- Git para versionamiento (opcional para ejecución, recomendable para desarrollo).
- Ollama instalado y servicio local disponible (habitualmente http://localhost:11434).
- Modelo descargado: gemma3:1b.
- Entorno virtual .venv recomendado; el prototipo inicial usa biblioteca estándar Python para HTTP y unittest.

Entorno realmente utilizado en las pruebas iniciales: portátil con aproximadamente 8 GB de RAM, Intel UHD Graphics 620 y ejecución de Gemma 3 1B mediante Ollama. Se trata de un equipo de demostración, no una referencia de dimensionamiento productivo.

## 6. Guía de instalación y ejecución

### 6.1. Verificación

```powershell
python --version
ollama --version
ollama list
Invoke-RestMethod http://localhost:11434/api/tags
```

Si gemma3:1b no aparece en la lista, descargar el modelo mediante «ollama pull gemma3:1b». Si Ollama no responde, verificar que el servicio esté activo. El comando «ollama run gemma3:1b» permite validar una conversación directamente antes de utilizar Python.

### 6.2. Ejecución desde la carpeta del proyecto

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python main.py
```

En la consola se muestran las opciones «1. Asistente Docente», «2. Asistente Estudiante» y «0. Salir». Escribir el número del asistente y enviar consultas en lenguaje natural. Para regresar al menú usar /salir; las alternativas /exit y /back aplican si se incorporó la mejora descrita y se validó su ejecución. Usar /reiniciar para limpiar el historial de la conversación activa.

### 6.3. Ejemplo de operación

```text
1 → Docente
Tú: Diseña una actividad de 15 minutos para enseñar variables en Python.
[Se obtiene una respuesta generada por Ollama]
/salir
2 → Estudiante
Tú: Explícame qué es una variable en Python y hazme una pregunta.
[Se obtiene una explicación y una pregunta de comprensión]
```

Las respuestas son generativas, pueden variar entre ejecuciones y deben verificarse antes de su uso académico. No deben interpretarse como orientaciones oficiales de la Universidad.

## 7. Gestión, configuración y adaptación

Las instrucciones se ajustan editando el archivo prompt.md del asistente correspondiente; los metadatos se ajustan en config.json. Para experimentar con otro modelo local es necesario contar con dicho modelo descargado y ajustar la configuración del proveedor que actualmente se instancia en main.py y evaluation/runner.py. El campo model presente en config.json es descriptivo en esta versión y todavía no determina automáticamente el modelo utilizado en ejecución.

El historial retiene un mensaje de sistema y hasta cuatro mensajes conversacionales recientes. Este mecanismo es simple y no ofrece todavía recorte por tokens, gestión persistente de conversaciones ni autorización por usuario. Las pruebas de regresión detectaron y permitieron corregir la duplicación del mensaje system en historiales cortos.

## 8. Pruebas realizadas y resultados

### 8.1. Pruebas unitarias

El 17 de noviembre de 2026 se ejecutó «python -m unittest discover -s tests -p "test_*.py" -v». Resultado suministrado desde la consola: 12 pruebas ejecutadas, 12 satisfactorias, 0 fallos, duración 0,011 s. Se validaron carga de configuración, carga de prompts, mensajes vacíos, generación simulada, reinicio, límite de historial, no duplicación de instrucciones y separación entre asistentes.

### 8.2. Evaluación funcional con modelo real

Se ejecutó «python -m evaluation.runner» con cuatro casos aislados, un modelo gemma3:1b y salida a JSON/Markdown. Resultado técnico: 4 casos completados, 0 errores. La evaluación académica manual preliminar revela diferencias que no se reflejan en el estado técnico COMPLETADA.

| Caso | Tiempo | Resultado académico preliminar | Observación |
| --- | --- | --- | --- |
| EV-DOC-001 — actividad 15 min | 59,50 s | No aprobado | Etapas 2 + 5 + 4 + 2 = 13 minutos |
| EV-DOC-002 — rúbrica | 51,91 s | No aprobado | No ofrece 3 niveles diferenciados; porcentajes 10+20+20, total declarado 100 |
| EV-EST-001 — variables | 27,30 s | Aprobado preliminar | Concepto, ejemplo válido y pregunta de comprensión |
| EV-EST-002 — Moodle | 26,18 s | Aprobado con observaciones | No inventa notas ni acceso; ruta sugerida de navegación sin validar |

Los cuatro estados COMPLETADA significan que se recibió respuesta sin error técnico; no equivalen a calidad académica aprobada. Estas valoraciones son preliminares y requieren ratificación por personal académico de la UAO.

### 8.3. Evidencias y reproducibilidad

```powershell
python -m unittest discover -s tests -p "test_*.py" -v
python -m evaluation.runner
```

Evidencia de evaluación registrada: docs/evaluaciones/evaluation_20261117_131133.json y .md. El evaluador registra pregunta, respuesta, términos indicativos y duración; conserva revisión humana pendiente. Los tiempos dependen del equipo, configuración y carga del modelo.

## 9. Restricciones, privacidad y buenas prácticas

- Usar datos ficticios o anonimizados durante las pruebas; evitar ingresar datos personales o información académica confidencial.
- Verificar toda respuesta antes de distribuir materiales a estudiantes.
- No afirmar acceso a Moodle, calificaciones, cursos, credenciales o políticas de la UAO.
- No asumir que el prototipo cumple por sí solo los requisitos de seguridad, retención, autenticación o protección de datos de un entorno productivo.
- No presentar pruebas locales como evidencia de despliegue ni compatibilidad operativa con LucIA.

## 10. Pendientes de validación con la UAO / Uninorte

| Tema | Pregunta o decisión pendiente |
| --- | --- |
| Formato de asistentes | ¿LucIA importa prompts/archivos? ¿Qué metadatos y límites requiere? |
| Administración y permisos | ¿Quién crea, revisa, edita y comparte asistentes? ¿Qué roles se asignan? |
| Modelos | ¿Cómo se configura un modelo por asistente y se controlan los costos? |
| Conocimiento documental | ¿Se admite recuperación/RAG? ¿Formatos, tamaño y gestión de archivos? |
| Identidad institucional | ¿Cómo se integran SSO, perfiles docentes y cursos vigentes? |
| Gobernanza | ¿Qué reglas de ética, privacidad y aprobación institucional aplican? |
| Integración LAIA–LucIA | ¿LAIA enlaza fichas, importa configuraciones o usa un servicio/API? |
| Despliegue y soporte | ¿Qué entornos, responsables y criterios de aceptación se utilizarán? |

## 11. Ruta de mejora propuesta

- Completar el manual y las fichas finales de asistentes cuando se confirmen las capacidades de LucIA.
- Ampliar casos y ejecutar varias repeticiones para caracterizar variabilidad.
- Crear validadores deterministas para sumas de tiempos y porcentajes, con intervención humana ante casos ambiguos.
- Probar otros modelos en computadores de mayor capacidad con los mismos casos.
- Validar las instrucciones de ética y fuentes académicas suministradas oficialmente.
- Acordar importación, publicación y permisos en LucIA antes de declarar integración.

## 12. Estado del entregable y criterios de aceptación propuestos

| Componente | Estado al 17/11/2026 |
| --- | --- |
| Fichas e instrucciones de dos asistentes | Borrador funcional elaborado |
| Ejecución por consola / Ollama | Validada localmente |
| Pruebas unitarias | 12/12 aprobadas |
| Casos funcionales con modelo real | 4/4 completados técnicamente |
| Aprobación académica institucional | Pendiente |
| Manual de usuario | Borrador 0.1 — sujeto a revisión |
| Integración real con LucIA | No ejecutada; pendiente de especificaciones |

Nota de control de alcance: el contrato original contemplaba otros entregables para el mes 2. La sustitución o ajuste de alcance debe quedar documentada con el supervisor y los responsables institucionales. Este manual no representa por sí mismo modificación contractual.
