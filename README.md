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

Processes extracted frames with OCR (EasyOCR, es/en), extracts dominant colors via `cv2.kmeans`, and — optionally, if a reference logo image is uploaded — detects logo presence/position via `cv2.ORB` feature matching. **Does not yet do product/composition detection** — those are tracked as `NOT_EVALUATED` rules in the rules engine (product varies too much for reference-image matching, composition is largely subjective/heuristic). (CTA detection doesn't need its own CV step — the rules engine matches a campaign brief's expected CTA text against the OCR output already produced here.)

Capabilities:

- OCR text extraction
- Word counting
- Bounding boxes per detected text
- Dominant color extraction (k-means, top 5 by prevalence)
- Logo presence + position detection (ORB feature matching, optional reference image; skipped entirely if none is uploaded)

Outputs:

```
visual_analysis.json
frame_analysis/
```

---

### Notebook 03 — Audio Analyzer

Processes the extracted audio with Whisper ("base" model), plus silence detection (RMS windowing over the raw waveform) and loudness measurement (`pyloudnorm`, ITU-R BS.1770 — real LUFS/LKFS, comparable against the targets a couple of placements publish in `context/matriz_medios.json`). **Does not yet classify music vs. voice** — that's tracked as a `NOT_EVALUATED` rule (judged unreliable without an ML model, same reasoning as deferring product/composition detection in Notebook 02).

Capabilities:

- Speech-to-Text transcription
- Speech detection
- Language detection
- Word counting
- Silence detection (contiguous silent segments ≥0.5s, RMS threshold)
- Integrated loudness measurement (LUFS, ITU-R BS.1770)

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

- **`rules/catalog.yaml`** — 26 rules across 4 layers (técnica / visual / sonora / semántica). 20 are implemented against what Notebooks 01–03 actually produce today: codec, frame rate and file size (via `ffprobe`/`os.path.getsize` in Notebook 01); CTA detection (reuses the OCR text Notebook 02 already extracts); dominant-color matching (`cv2.kmeans` over sampled frame pixels); logo presence + safe-zone position (`cv2.ORB` feature matching against an optional reference logo image uploaded in Notebook 02); silence detection and loudness/LUFS measurement (RMS windowing + `pyloudnorm`/ITU-R BS.1770 in Notebook 03 — see below). 6 remain `NOT_EVALUATED` stubs with an explicit reason (no product-detection/composition CV, no music-vs-voice classification, no semantic/LLM layer) — missing data is never silently treated as a pass. **`rules/` itself still has zero image/audio/ML dependencies** — all signal-level computation happens upstream in the notebooks; the package only ever compares already-computed JSON fields (colors as hex strings, OCR text as strings, logo bounding boxes as 0–1 fractions, LUFS as a number), which is what keeps it fast/testable/CI-friendly.
- **Logo detection is brief-coupled by design**: unlike every other check, matching a reference logo needs the actual reference image at CV-computation time, so Notebook 02 takes an *optional* reference-logo upload (skip it and `logo_detection` stays `null` → both logo rules fall back to `NOT_EVALUATED`, never a false `FAIL`). This means a given `asset_knowledge.json` is only meaningful for logo checks against the one brief/logo used when Notebook 02 ran — re-run Notebook 02 if you need to check the same footage against a different brand's logo. Accepted tradeoff: in practice one ad creative belongs to one campaign anyway.
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

- Product detection / composition analysis (`VISUAL_PRODUCT_DETECTION`, `VISUAL_COMPOSITION`)
- Music-vs-voice classification (`SONORA_MUSIC_VS_VOICE`) — deferred, unreliable without a real ML model
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
- [x] CTA detection via existing OCR text + dominant-color brand matching via k-means (`VISUAL_CTA_DETECTION`, `VISUAL_DOMINANT_COLOR`)
- [x] Logo presence + safe-zone position via ORB feature matching against an optional reference image (`VISUAL_LOGO_PRESENCE`, `VISUAL_LOGO_SAFE_ZONE`)
- [x] Silence detection + loudness/LUFS measurement (`SONORA_SILENCE_DETECTION`, `SONORA_VOLUME_LOUDNESS` — 20/26 catalog rules now implemented)
- [ ] Product detection / composition analysis / music-vs-voice classification (`VISUAL_PRODUCT_DETECTION`, `VISUAL_COMPOSITION`, `SONORA_MUSIC_VS_VOICE` — deferred, all three judged unreliable without a real ML model or reference-image mechanism that doesn't exist yet)
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
