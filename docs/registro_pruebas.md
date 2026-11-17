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