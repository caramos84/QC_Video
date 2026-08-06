# QC Video Engine — Highcut backend

> Intelligent Multimodal Quality Control Engine for Video & Motion Graphics Creative Assets

## Overview

QC Video Engine is the backend that powers **Highcut**, the Video & Motion Graphics QA engine of **SPHERE** — an internal, multi-engine Quality Control platform. SPHERE also includes five sibling engines for other asset types (Sherlock for static visual QA, Pixduct for HTML5/display ads, Experival for UX/UI & accessibility, Ripcheck for print/packaging, Echoval for audio engineering). This repo only implements Highcut; see [`context/sphere_platform.md`](context/sphere_platform.md) for the full platform context and how it was discovered.

Instead of performing manual reviews, the system decomposes videos into structured data and analyzes them through specialized processing modules before evaluating compliance against configurable business and brand rules.

The project follows a modular architecture inspired by MLOps principles, where each processing stage produces reusable artifacts consumed by downstream analysis engines.

---

## Objectives

The project aims to automate repetitive Quality Control tasks commonly found in creative production environments, including:

- Technical validation
- Visual inspection
- Audio inspection
- Text extraction
- Compliance verification
- Brand consistency
- Automated reporting

---

# Architecture

```text
                   Asset
                     │
                     ▼
        Notebook 01 - Asset Decomposer
                     │
        ┌────────────┴────────────┐
        ▼                         ▼
Notebook 02                 Notebook 03
Visual Analyzer           Audio Analyzer
        │                         │
        └────────────┬────────────┘
                     ▼
          asset_knowledge.json
                     ▼
       Notebook 04 - QC Decision Engine
         (thin wrapper over rules/)
                     │
                     ▼
        profile (channel/placement)
          + optional campaign brief
                     │
                     ▼
              rules/engine.py
       catalog → checks → scoring → report
                     │
          ┌──────────┼──────────┐
          ▼          ▼          ▼
     qc_report   qc_score   qc_summary
      .json       .json        .md
```

Notebooks 01–03 stay as Colab notebooks (heavy, exploratory dependencies: moviepy, EasyOCR, Whisper). Notebook 04's actual logic lives in the testable `rules/` Python package — see [Rules Engine](#rules-engine) below.

---

## Processing Pipeline

### Notebook 01 — Asset Decomposer

Responsible for:

- Video ingestion
- Metadata extraction
- Audio extraction
- Frame extraction
- Manifest generation

Outputs:

```
metadata.json
manifest.json
audio.wav
frames/
```

---

### Notebook 02 — Visual Analyzer

Processes extracted frames with OCR (EasyOCR, es/en) and extracts dominant colors via `cv2.kmeans` over sampled frame pixels. **Does not yet do logo/product/composition detection** — those are tracked as `NOT_EVALUATED` rules in the rules engine until a reference-image matching mechanism or a heavier CV pipeline exists. (CTA detection doesn't need its own CV step — the rules engine matches a campaign brief's expected CTA text against the OCR output already produced here.)

Capabilities:

- OCR text extraction
- Word counting
- Bounding boxes per detected text
- Dominant color extraction (k-means, top 5 by prevalence)

Outputs:

```
visual_analysis.json
frame_analysis/
```

---

### Notebook 03 — Audio Analyzer

Processes the extracted audio with Whisper ("base" model). **Does not yet do audio-quality analysis** — no silence detection, no loudness/volume measurement, no music-vs-voice detection. Those are tracked as `NOT_EVALUATED` rules in the rules engine until a real audio-quality pipeline exists.

Capabilities:

- Speech-to-Text transcription
- Speech detection
- Language detection
- Word counting

Outputs:

```
audio_analysis.json
transcript.json
```

---

### Notebook 04 — QC Decision Engine

A thin wrapper: clones the repo, installs the `rules/` package, and calls `rules.engine.run_qc(...)`. All decision logic lives in `rules/`, not in the notebook.

Outputs:

```
qc_report.json
qc_score.json
qc_summary.md
```

---

## Rules Engine

`rules/` is a standalone, testable Python package (`pytest`, 45 tests, 81% coverage) — see [`context/matriz_medios.md`](context/matriz_medios.md) for how the technical specs were sourced.

- **`rules/catalog.yaml`** — 26 rules across 4 layers (técnica / visual / sonora / semántica). 16 are implemented against what Notebooks 01–03 actually produce today: codec, frame rate and file size (via `ffprobe`/`os.path.getsize` in Notebook 01); CTA detection (reuses the OCR text Notebook 02 already extracts — no new CV needed) and dominant-color matching (`cv2.kmeans` over sampled frame pixels, added to Notebook 02). 10 remain `NOT_EVALUATED` stubs with an explicit reason (no CV pipeline for logo/product/composition, no audio-quality pipeline, no semantic/LLM layer) — missing data is never silently treated as a pass. **`rules/` itself still has zero image/ML dependencies** — all pixel-level computation happens upstream in the notebooks; the package only ever compares already-computed JSON fields (colors as hex strings, OCR text as strings), which is what keeps it fast/testable/CI-friendly.
- **`profiles/`** — 25 channel/placement profiles (Meta, TikTok, Google/YouTube/DV360, LinkedIn, Pinterest, CTV), auto-generated from [`context/matriz_medios.json`](context/matriz_medios.json) via `python -m rules.tools.build_profiles_from_matriz`. Never hand-edit a profile — edit the matrix and regenerate.
- **`samples/briefs/`** — per-campaign business rules (CTA text, legal disclaimers, brand colors/logo) that can override a rule's severity for that campaign.
- **Scoring**: severities `critico` (forces FAIL) / `error_de_marca` (-20) / `error_tecnico` (-15) / `warning` (-5). Verdict is `PASS` / `REVIEW` / `FAIL`, and **caps at `REVIEW` when rule coverage is low** — a perfect score can't be presented as "fully validated" while whole layers (visual/audio/semantic) are unevaluated.

Run it locally:

```bash
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
pytest tests/ -v
python -m rules.tools.build_profiles_from_matriz --check
```

---

# Design Philosophy

The project intentionally separates extraction, analysis and decision making into independent modules.

This architecture provides:

- Modular development
- Independent testing
- Scalability
- Easy replacement of AI models
- Reusable intermediate artifacts
- MLOps-friendly workflows

---

# Planned Features (not yet implemented — tracked as `NOT_EVALUATED` catalog rules)

- Logo Detection / Safe Zone Validation (`VISUAL_LOGO_PRESENCE`, `VISUAL_LOGO_SAFE_ZONE`) — needs a reference logo image mechanism (classical CV, offline)
- Product detection / composition analysis (`VISUAL_PRODUCT_DETECTION`, `VISUAL_COMPOSITION`)
- Silence / loudness / music-vs-voice audio-quality analysis (`SONORA_SILENCE_DETECTION`, `SONORA_VOLUME_LOUDNESS`, `SONORA_MUSIC_VS_VOICE`)
- Semantic/brief compliance via LLM (`SEMANTICA_*`) — message, brand positioning, guideline compliance
- Dashboard (SPHERE UI — design system + components already available, see below)
- Harness CI provisioning (pipeline-as-code already written, account setup pending)

---

# Technologies

- Python
- Google Colab
- OpenCV
- FFmpeg
- EasyOCR
- Whisper
- Pandas
- NumPy
- PyYAML, jsonschema, pytest, ruff (rules engine)

Future versions:

- GPT Vision
- Gemini
- Azure AI Vision
- Vertex AI

---

# Repository Structure

```
QC_Video/
├── notebooks/
│   ├── 01_VideoExtraction.ipynb
│   ├── 02_VisualAnalyzer.ipynb
│   ├── 03_AudioAnalyzer.ipynb
│   └── 04_DecisionEngine.ipynb      # thin wrapper over rules/
│
├── rules/                            # the real QC Decision Engine
│   ├── catalog.yaml                  # 25 rules, implementable vs NOT_EVALUATED
│   ├── engine.py / checks.py / scoring.py / report.py / loaders.py / models.py
│   ├── schema/                       # JSON Schemas for profiles + briefs
│   └── tools/build_profiles_from_matriz.py
│
├── profiles/                         # 25 channel/placement profiles (generated)
│
├── samples/
│   ├── briefs/                       # example campaign brief
│   └── assets/                       # example asset_knowledge.json
│
├── tests/                            # pytest suite (45 tests)
│
├── outputs/                          # generated qc_report/qc_score/qc_summary (gitignored)
│
├── context/                          # research/design context (matriz de medios, SPHERE platform, Miro)
│
├── .harness/qc-video-ci.yaml         # Harness Cloud CI pipeline (written, not provisioned)
│
└── README.md
```

---

# Roadmap

- [x] Asset Decomposer
- [x] Visual Analyzer (OCR only)
- [x] Audio Analyzer (transcription only)
- [x] QC Decision Engine (rules engine v1 — 11/25 rules implemented, rest are explicit `NOT_EVALUATED`)
- [x] Rule Profiles (25, generated from the media specs matrix)
- [x] Codec/frame-rate/file-size technical checks (`TECH_CODEC`, `TECH_FRAME_RATE`, `TECH_FILE_SIZE`)
- [x] CTA detection via existing OCR text + dominant-color brand matching via k-means (`VISUAL_CTA_DETECTION`, `VISUAL_DOMINANT_COLOR` — 16/26 catalog rules now implemented)
- [ ] Logo detection / safe zone / product / composition (`VISUAL_LOGO_*`, `VISUAL_PRODUCT_DETECTION`, `VISUAL_COMPOSITION` — deferred, needs reference-image matching or a heavier CV pipeline)
- [ ] Audio-quality checks (silence/loudness/music — needs a real audio-quality pipeline)
- [ ] Semantic/brief compliance (needs an LLM layer)
- [ ] Dashboard (SPHERE UI)
- [ ] Harness CI provisioning + Production Deployment

---

# SPHERE Platform Context

This repo implements the backend for **Highcut**, one of six validation engines in **SPHERE** (an internal, multi-engine QC platform: Sherlock, Pixduct, Highcut, Experival, Ripcheck, Echoval — one per asset type). See [`context/sphere_platform.md`](context/sphere_platform.md) for the full breakdown and [`context/sphere_design_tokens.md`](context/sphere_design_tokens.md) for the shared design system (colors, typography, spacing) that a future SPHERE dashboard would use to render `qc_report.json` / `qc_score.json`.

---

## Vision

The long-term objective is to build a multimodal Quality Control platform capable of validating creative assets across multiple channels, brands and formats while integrating seamlessly into enterprise production workflows.

Rather than functioning as a collection of isolated AI tools, QC Video Engine is conceived as a modular decision system where specialized analysis engines collaborate to produce explainable and reproducible quality assessments.
