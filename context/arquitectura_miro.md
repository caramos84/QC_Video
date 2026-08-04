# Arquitectura SPHERE QC-Video (fuente: Miro board uXjVHCVWl_I=)

## Modelo de 4 capas de QC

| Capa | Qué valida |
|---|---|
| **Técnica** | Formato, Duración, FPS, Resolución, Peso, Códec, Orientación, Aspect Ratio |
| **Visual** | Frames, Marca, Producto, CTA, Textos, Logos, Zonas seguras, Composición, Legibilidad |
| **Sonora** | Presencia audio, Voz, Música, Silencios, Volumen, Limpieza, Duración |
| **Semántica** | Contenido de textos, Mensaje, CTA, Posicionamiento de marca, Cumplimiento de lineamientos |

## Pipeline técnico

```
Asset
  → Ingesta técnica
  → Separación de señales (Frames / Audio / Metadata)
  → Análisis
       ├─ Computer Vision: detección de cambios, presencia/posición de logo,
       │  call to action, colores predominantes, producto, composición y
       │  legibilidad, safe zones, contador de palabras (CV)
       ├─ OCR: validador de textos
       └─ Speech-to-text / Audio análisis: separación de pista, duración
          audio, silencios, contador de palabras (STT), detector audio/música
  → Motor de reglas QC
  → Reporte (QC Score + QC Report)
```

## Mapeo a notebooks

- **Notebook 01 — Asset Decomposer**: video → metadata, manifest, frames, audio.wav *(no disponible como .ipynb, solo inferido de sus outputs)*
- **Notebook 02 — Visual Analyzer**: OCR (EasyOCR) sobre frames → `visual_analysis.json`, `frame_analysis/*.json` *(implementado, ver `notebooks/VisualAnalyzer.ipynb`)*
- **Notebook 03 — Audio Analyzer**: transcripción (Whisper) → `audio_analysis.json`, `transcript.json/txt` *(no disponible como .ipynb, solo su output en `samples/output_audio_analysis.zip`)*
- **Notebook 04 — QC Decision Engine**: consolida todo en `asset_knowledge.json` *(el archivo se llama `DecisionEngine.ipynb` pero por ahora SOLO agrega/consolida — no contiene el motor de reglas ni el scoring)*

## Ejemplos de reglas de negocio (definidas en el board, no implementadas)

```
IF canal = "Instagram Reels" AND formato != 1080x1920 THEN error crítico
IF CTA no aparece THEN warning / error según brief
IF logo aparece fuera de zona segura THEN error de marca
IF duración > límite de canal THEN error técnico
```

## Brechas identificadas (board vs. implementación actual)

1. **Motor de reglas QC**: diseñado (con reglas IF/THEN) pero no implementado. Notebook 04 actual solo produce un "knowledge model", no un veredicto ni un score.
2. **Computer Vision**: el board contempla detección de logo, CTA, colores predominantes, producto, safe zones, "detección de cambios" — nada de esto existe en el código actual. Notebook 02 solo hace OCR (texto), no CV real.
3. **Capa semántica**: cumplimiento de lineamientos / mensaje / posicionamiento de marca no está implementado — probablemente requiere LLM sobre el texto OCR + transcript comparado contra un brief.
4. **QC Score / QC Report**: no existen todavía como artefactos.
5. Todo el pipeline es manual vía Colab (`files.upload()` / `files.download()`), sin orquestación automática entre notebooks.
