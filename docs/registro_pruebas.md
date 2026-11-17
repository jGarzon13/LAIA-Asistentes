# LAIA — Registro de pruebas locales

**Versión:** 0.1.0  
**Entorno:** Windows, Python, Ollama y Gemma 3 1B  
**Estado:** Prototipo en validación  
**Fecha de referencia:** 17 de noviembre de 2026

## 1. Objetivo

Verificar el funcionamiento básico de los asistentes académicos Docente y Estudiante, desarrollados como prototipos locales para LAIA, y registrar su comportamiento frente a consultas representativas.

## 2. Entorno de ejecución

- Memoria RAM: aproximadamente 8 GB.
- Gráficos: Intel UHD Graphics 620.
- Modelo: `gemma3:1b`.
- Proveedor: Ollama.
- Interfaz: consola Python.
- Integración con LucIA: no realizada.

## 3. Pruebas funcionales observadas

| ID | Asistente | Prueba | Resultado |
|---|---|---|---|
| PF-01 | General | Conexión Python–Ollama | Exitosa |
| PF-02 | Docente | Consulta abierta sobre agentes de IA | Respuesta coherente; solicita contexto |
| PF-03 | Docente | Diseño de actividad de 15 minutos | Parcial: los tiempos sumaron 16 minutos |
| PF-04 | Docente | Continuidad de conversación | Exitosa |
| PF-05 | Estudiante | Explicación del concepto de variables | Respuesta comprensible con ejemplos |
| PF-06 | Estudiante | Retroalimentación a respuesta del estudiante | Respuesta pertinente |
| PF-07 | Consola | Comando `/exit` | No reconocido en la versión inicial |

## 4. Hallazgos

**H-01. Inconsistencia temporal:** el Asistente Docente produjo una actividad de 16 minutos pese a solicitarse una duración exacta de 15 minutos.

**H-02. Limitación del modelo:** una prueba inicial de explicación de variables produjo una afirmación incorrecta sobre las reglas de nombres de variables en Python.

**H-03. Comandos de navegación:** el comando `/exit` se interpretó como mensaje de usuario. Se propone reconocerlo como comando de salida.

## 5. Limitaciones

Los resultados corresponden a observaciones preliminares y no constituyen una validación exhaustiva. No se han probado autenticación institucional, integración con LucIA, RAG, archivos de conocimiento ni acceso a plataformas académicas de la UAO.

## 6. Próximas actividades

Ejecutar las pruebas automatizadas, ampliar los casos funcionales, revisar las respuestas académicas y verificar los requisitos de compatibilidad con LucIA una vez se disponga de documentación técnica.

## 7. Pruebas unitarias automatizadas

### 7.1 Objetivo

Verificar mediante pruebas automatizadas el funcionamiento de los componentes internos de los asistentes académicos LAIA, específicamente la carga de configuraciones, lectura de instrucciones, procesamiento de mensajes, independencia entre asistentes y administración del historial conversacional.

Las pruebas se desarrollaron utilizando la biblioteca estándar `unittest` de Python y proveedores simulados (`FakeProvider`), permitiendo evaluar la lógica interna sin depender de la disponibilidad de Ollama ni de la generación de respuestas del modelo.

### 7.2 Procedimiento de ejecución

Desde la carpeta raíz del proyecto se ejecutó el siguiente comando:

```powershell
python -m unittest discover -s tests -p "test_*.py" -v
```

El descubrimiento automático identificó los archivos `test_docente.py` y `test_estudiante.py`.

### 7.3 Resultados obtenidos

**Fecha de ejecución:** 17 de noviembre de 2026.

| Indicador | Resultado |
|---|---|
| Pruebas ejecutadas | 12 |
| Pruebas exitosas | 12 |
| Pruebas fallidas | 0 |
| Errores de ejecución | 0 |
| Tiempo reportado | 0,011 segundos |
| Estado general | APROBADO |

**Detalle de las pruebas:**

| ID | Componente | Prueba | Resultado |
|---|---|---|---|
| PU-01 | Docente | `test_chat` | Aprobada |
| PU-02 | Docente | `test_empty_message` | Aprobada |
| PU-03 | Docente | `test_history_limit` | Aprobada |
| PU-04 | Docente | `test_load_config` | Aprobada |
| PU-05 | Docente | `test_load_prompt` | Aprobada |
| PU-06 | Docente | `test_reset` | Aprobada |
| PU-07 | Docente | `test_system_prompt_not_duplicated` | Aprobada |
| PU-08 | Estudiante | `test_chat` | Aprobada |
| PU-09 | Estudiante | `test_chat_does_not_mix_assistants` | Aprobada |
| PU-10 | Estudiante | `test_independent_prompts` | Aprobada |
| PU-11 | Estudiante | `test_load_config` | Aprobada |
| PU-12 | Estudiante | `test_load_prompt` | Aprobada |

### 7.4 Interpretación de resultados

Las doce pruebas finalizaron satisfactoriamente. Los resultados permiten establecer que, bajo los escenarios automatizados evaluados:

- Los asistentes cargan correctamente su configuración e instrucciones.
- Se procesan consultas mediante la interfaz común de proveedores.
- Los mensajes vacíos son rechazados.
- El historial conversacional respeta el límite establecido.
- Es posible reiniciar una conversación.
- El mensaje de sistema se conserva sin duplicaciones.
- Los asistentes Docente y Estudiante mantienen instrucciones e historiales independientes.

Estas pruebas verifican la lógica de la aplicación, pero no evalúan la precisión de las respuestas generadas por Gemma 3 1B, su desempeño pedagógico ni la compatibilidad real con LucIA.

### 7.5 Evidencia de ejecución

Salida final registrada en PowerShell:

```text
Ran 12 tests in 0.011s

OK
```

El resultado completo puede reproducirse ejecutando el comando indicado en la sección 7.2 sobre la versión correspondiente del repositorio.

## 8. Registro de incidencias y acciones correctivas

### 8.1 Incidencia INC-001: duplicación del mensaje de sistema

**Componente afectado:** `core/assistant.py`  
**Funcionalidad:** Administración del historial conversacional  
**Estado:** Corregida y verificada

**Descripción del hallazgo**

Durante la primera ejecución de las pruebas automatizadas se identificó un fallo en `test_chat_does_not_mix_assistants`.

El asistente conservaba incorrectamente una copia adicional del mensaje de sistema al procesar conversaciones cortas. El problema estaba relacionado con el mecanismo utilizado para limitar la cantidad de mensajes almacenados.

**Causa identificada**

La expresión original:

```python
self.messages[:1] + self.messages[-4:]
```

podía duplicar el mensaje de sistema cuando el historial contenía menos de cuatro mensajes.

**Corrección aplicada**

Se modificó el mecanismo de selección del historial:

```python
self.messages[:1] + self.messages[1:][-4:]
```

La nueva expresión conserva el mensaje de sistema y selecciona únicamente los últimos cuatro mensajes conversacionales, sin incluir nuevamente las instrucciones iniciales.

**Validación de la corrección**

Se incorporó la prueba de regresión `test_system_prompt_not_duplicated` para comprobar que el historial conserva exactamente un mensaje de sistema.

Durante el ajuste se detectó también un error de sintaxis de indexación que generó excepciones `TypeError`. Este error fue corregido antes de la ejecución final.

**Resultado final**

Se ejecutaron nuevamente las doce pruebas automatizadas y todas finalizaron correctamente.

**Conclusión de la incidencia**

La incidencia permitió fortalecer la gestión del historial y agregar una prueba de regresión para prevenir la reaparición del defecto.

### 8.2 Seguimiento

| Incidencia | Estado | Evidencia |
|---|---|---|
| INC-001: duplicación del mensaje de sistema | Corregida | 12 pruebas aprobadas |
| H-01: inconsistencia en duración de actividades | Pendiente de validación | Prueba funcional del Asistente Docente |
| H-02: afirmación incorrecta sobre variables en Python | Pendiente de validación | Prueba inicial con Gemma 3 1B |
| H-03: comando `/exit` no reconocido | Pendiente de verificar corrección | Prueba de consola |

Los hallazgos pendientes requieren pruebas posteriores para establecer si las mejoras realizadas resuelven satisfactoriamente los comportamientos observados.

## 9. Primera evaluación funcional de los asistentes con Ollama

### 9.1 Objetivo

Evaluar el comportamiento funcional y académico de los asistentes Docente y Estudiante mediante la ejecución de casos de prueba predefinidos, utilizando el modelo local Gemma 3 1B a través de Ollama.

La evaluación busca identificar el cumplimiento de instrucciones, la pertinencia de las respuestas, las limitaciones académicas y el desempeño técnico en un equipo de recursos limitados.

### 9.2 Entorno de pruebas

- Fecha: 17 de noviembre de 2026.
- Hardware: portátil con aproximadamente 8 GB de RAM y gráficos integrados Intel UHD 620.
- Lenguaje: Python.
- Motor de inferencia: Ollama.
- Modelo: `gemma3:1b`.
- Interfaz: consola.
- Herramienta de evaluación: `evaluation.runner`.
- Casos definidos: 4.
- Tipo de ejecución: secuencial, con una nueva instancia del asistente para cada caso.

### 9.3 Resultados técnicos

| Indicador | Resultado |
|---|---|
| Casos ejecutados | 4 |
| Ejecuciones completadas | 4 |
| Errores técnicos | 0 |
| Generación de evidencia JSON | Exitosa |
| Generación de evidencia Markdown | Exitosa |

Tiempos registrados:

| Caso | Tiempo |
|---|---:|
| EV-DOC-001 | 59,50 s |
| EV-DOC-002 | 51,91 s |
| EV-EST-001 | 27,30 s |
| EV-EST-002 | 26,18 s |

Los resultados confirman la capacidad del prototipo para ejecutar ambos asistentes localmente y registrar sus respuestas.

### 9.4 Revisión preliminar de calidad académica

| ID | Resultado | Observaciones |
|---|---|---|
| EV-DOC-001 | No aprobado | La actividad solicitada debía durar exactamente 15 minutos, pero la suma de las etapas fue de 13 minutos. |
| EV-DOC-002 | No aprobado | No se construyeron tres niveles de desempeño diferenciados. Los porcentajes declarados tampoco corresponden al total indicado. |
| EV-EST-001 | Aprobado | Explicación adecuada, ejemplo válido en Python y pregunta de comprensión. |
| EV-EST-002 | Aprobado con observaciones | Reconoce que no dispone de acceso a Moodle y evita inventar calificaciones. Las indicaciones de navegación requieren verificación institucional. |

Esta clasificación corresponde a una revisión técnica y académica preliminar de las respuestas registradas. No constituye una certificación institucional del desempeño de los asistentes.

### 9.5 Hallazgos adicionales

**H-05. Incumplimiento de restricciones numéricas**

El Asistente Docente presentó inconsistencias en la distribución temporal de actividades, pese a recibir instrucciones explícitas sobre su duración.

**H-06. Inconsistencia estructural en instrumentos de evaluación**

El Asistente Docente no produjo una rúbrica con los tres niveles de desempeño solicitados y presentó porcentajes inconsistentes.

**H-07. Necesidad de verificar orientaciones institucionales**

El Asistente Estudiante reconoció correctamente sus limitaciones de acceso, pero ofreció orientaciones de navegación que requieren validación frente a la configuración real de Moodle de la UAO.

### 9.6 Análisis

Los resultados muestran que la arquitectura técnica permite ejecutar satisfactoriamente ambos asistentes en un entorno local de recursos limitados.

No obstante, el desempeño académico depende de la capacidad del modelo para seguir instrucciones, mantener coherencia y producir información correcta.

El modelo Gemma 3 1B presenta limitaciones observables en tareas que requieren precisión numérica y estructuración de instrumentos de evaluación. Por ello, se recomienda mantener mecanismos de revisión académica y evaluar modelos alternativos.

### 9.7 Recomendaciones

1. Incorporar controles programáticos para verificar restricciones objetivas, como sumas de tiempos y porcentajes.
2. Fortalecer las instrucciones del Asistente Docente mediante ejemplos de formatos esperados.
3. Ampliar los casos de prueba para evaluar consistencia ante solicitudes similares.
4. Comparar el desempeño con modelos de mayor capacidad en equipos apropiados.
5. Mantener separados los resultados técnicos, las verificaciones automáticas y la revisión académica.
6. Validar posteriormente los procedimientos institucionales y las especificaciones de integración de LucIA.

### 9.8 Evidencias

Se generaron los siguientes archivos:

- `evaluation_20261117_131133.json`
- `evaluation_20261117_131133.md`

Ambos contienen los resultados de la ejecución del 17 de noviembre de 2026 y permiten consultar las respuestas originales del modelo.

### 9.9 Conclusión

La primera evaluación funcional demuestra que los asistentes Docente y Estudiante pueden ejecutarse correctamente desde Python utilizando Ollama y Gemma 3 1B.

Los cuatro casos finalizaron técnicamente, mientras que la revisión académica preliminar identificó dos casos no aprobados, uno aprobado y uno aprobado con observaciones.

Se recomienda continuar con el fortalecimiento del proceso de evaluación antes de considerar los asistentes aptos para un uso académico institucional.