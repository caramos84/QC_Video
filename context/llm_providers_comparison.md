# Comparativa de proveedores de LLM

Referencia de costos y rendimiento para elegir proveedor de IA en la **capa semántica**
(`SEMANTICA_*`) y las reglas de CV/audio con ML actualmente marcadas como `deferred` en
`rules/catalog.yaml` (`VISUAL_PRODUCT_DETECTION`, `VISUAL_COMPOSITION`,
`SONORA_MUSIC_VS_VOICE`).

> **Vigencia de los datos:** investigado 2026-08-06. Precios, throughput y nombres de
> modelo cambian con frecuencia (nueva generación, repricing, deprecación) — antes de
> tomar una decisión de compra o de integrar un SDK, revalidar contra la fuente oficial
> del proveedor en vez de asumir que esta tabla sigue vigente.

## Tabla comparativa

| Proveedor | Modelo | Tier | Contexto | Output máx | Visión | $/1M in | $/1M out | Throughput (tok/s out) | TTFT |
|---|---|---|---|---|---|---|---|---|---|
| Anthropic | Claude Fable 5 | Más capaz | 1M | 128K | Sí | $10.00 | $50.00 | sin dato de benchmark | — |
| Anthropic | Claude Opus 5 | Flagship | 1M | 128K | Sí | $5.00 | $25.00 | 54.5 (std) / ~136 est. en fast mode (2.5x, precio premium) | 51.5s |
| Anthropic | Claude Sonnet 5 | Medio | 1M | 128K | Sí | $3.00 ($2.00 intro hasta 2026-08-31) | $15.00 ($10.00 intro) | 73.8 | 196.4s |
| Anthropic | Claude Haiku 4.5 | Rápido/económico | 200K | 64K | Sí | $1.00 | $5.00 | 86.1 | 1.1s |
| OpenAI | GPT-5.6 Sol | Flagship | 1.05M | 128K | Sí (texto+imagen) | $5.00 | $30.00 | 71.5 ⚠️ medido en GPT-5.5, no 5.6 | 79.3s |
| OpenAI | GPT-5.6 Terra | Económico | 1.05M | 128K | Sí | $2.00 | $12.00 | 92.8 ⚠️ medido en GPT-5 mini, no 5.6 | 97.2s |
| Google | Gemini 2.5 Pro | Flagship (GA) | 1.05M | 64K (65,536) | Sí (imagen/audio/video/PDF) | $1.25–2.50 | $10–15 | 131.0 ⚠️ medido en Gemini 3.1 Pro Preview | 32.4s |
| Google | Gemini 3.6 Flash | Económico (GA) | 1.05M | 64K | Sí | $1.50 | $7.50 | 213.2 | 17.3s |

## Advertencias

- **⚠️ = desfase de versión.** Los precios corresponden a la generación GA más reciente
  publicada por cada proveedor (GPT-5.6, Gemini 2.5 Pro), pero el benchmark de throughput
  (Artificial Analysis) todavía no tenía datos para esa generación exacta al momento de
  la consulta — se usó el modelo más cercano disponible. No tratar esos tok/s como
  exactos para la fila de precio listada.
- **TTFT no es comparable 1:1 entre filas.** En los modelos con razonamiento (Opus 5,
  Sonnet 5, GPT-5.5/5.6, Gemini Pro) el TTFT incluye el tiempo de "pensamiento" interno
  — por eso Sonnet 5 muestra 196s. Haiku 4.5 (1.1s) y los modos sin razonamiento son más
  representativos de latencia de red real.
- **Ningún proveedor publica throughput oficial**, salvo Anthropic parcialmente (el
  multiplicador ~2.5x de "fast mode" en Opus). Todos los tok/s de esta tabla vienen de
  benchmarking independiente (Artificial Analysis), no de garantías contractuales.
- **Claude Fable 5** no tiene benchmark de throughput público — es el modelo menos usado
  en benchmarks de terceros por su costo.

## Fuentes

- Claude: skill interna `claude-api` (caché 2026-06-24), basada en la documentación
  oficial de Anthropic.
- OpenAI: `developers.openai.com/api/docs/models/*`, `developers.openai.com/api/docs/pricing`.
- Google: `ai.google.dev/gemini-api/docs/pricing`, `ai.google.dev/gemini-api/docs/models`.
- Throughput/latencia: [artificialanalysis.ai](https://artificialanalysis.ai) (benchmark
  independiente, no vendor-reported).

## Recomendación para SPHERE QC-Video

La capa semántica y las reglas de CV/audio con ML son tareas de **visión + texto sobre
frames/audio ya extraídos** (no generación masiva de tokens), así que el throughput pesa
menos que precisión, ventana de contexto y costo por volumen de assets procesados:

- **Haiku 4.5** o **Gemini 3.6 Flash** — opción más barata para correr en volumen (miles
  de assets/campañas).
- **Sonnet 5** — intermedio, si la precisión de un modelo económico no alcanza para
  `SEMANTICA_MESSAGE_COMPLIANCE` / `SEMANTICA_BRAND_POSITIONING`.
- Mantener la arquitectura ya establecida (`rules/` sin dependencias de ML): la llamada al
  LLM iría en una notebook nueva (o extensión de la 02/03), produciendo campos JSON que
  `rules/checks.py` simplemente compara — mismo patrón que dominant-color/logo/loudness.

## Decisión (2026-08-06)

**Proveedor elegido para el prototipo: Gemini 3.6 Flash.** Razón del usuario: mejor
balance de facilidad de integración, rendimiento (213.2 tok/s, el más alto de la tabla)
y accesibilidad/costo ($1.50/$7.50 por 1M tokens) para la capa semántica y las reglas de
CV/audio con ML diferidas.

Implicaciones a tener en cuenta cuando se implemente:

- SDK: `google-genai` (Python) — a diferencia de Claude, esta llamada probablemente
  rompería el principio de "cero dependencias de ML en `rules/`" si se hace directo desde
  ahí. Debe vivir en una notebook (Colab), igual que dominant-color/logo/loudness, y
  `rules/checks.py` solo debe consumir el JSON ya producido.
- Gemini 3.6 Flash es multimodal (imagen/audio/video/PDF in) — puede recibir frames
  directamente sin pasar por OCR intermedio, lo cual podría simplificar
  `SEMANTICA_MESSAGE_COMPLIANCE` frente al pipeline actual de Tesseract OCR en
  Notebook 02.
- Revalidar precio/modelo contra `ai.google.dev/gemini-api/docs/pricing` antes de
  implementar — la tabla de arriba tiene fecha de corte 2026-08-06.
