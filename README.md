# QC Video Engine

> Intelligent Multimodal Quality Control Engine for Creative Assets

## Overview

QC Video Engine is an experimental framework designed to automate the Quality Control (QC) process for audiovisual creative assets.

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
       Notebook 04 - QC Decision Engine
                     │
          ┌──────────┴──────────┐
          ▼                     ▼
      QC Report             QC Score
```

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

Processes extracted frames using Computer Vision techniques.

Capabilities:

- OCR
- Word counting
- Bounding Boxes
- Layout analysis
- Frame-level inspection

Outputs:

```
visual_analysis.json
frame_analysis/
```

---

### Notebook 03 — Audio Analyzer

Processes the extracted audio.

Capabilities:

- Speech-to-Text
- Speech detection
- Silence detection
- Word counting
- Audio metadata

Outputs:

```
audio_analysis.json
transcript.json
```

---

### Notebook 04 — QC Decision Engine

Acts as the decision layer of the framework.

Responsibilities:

- Load analysis artifacts
- Load validation profiles
- Execute QC rules
- Calculate quality scores
- Generate executive reports

Outputs:

```
qc_report.json
qc_score.json
qc_summary.md
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

# Planned Features

- Logo Detection
- Brand Detection
- CTA Detection
- Safe Zone Validation
- Design System Validation
- Social Media Compliance
- Automatic Brand Rules
- GPT Vision integration
- Dashboard
- PDF Reporting

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

Future versions:

- GPT Vision
- Gemini
- Azure AI Vision
- Vertex AI

---

# Repository Structure

```
QC_VIDEO_ENGINE/

├── notebooks/
│   ├── 01_asset_decomposer.ipynb
│   ├── 02_visual_analyzer.ipynb
│   ├── 03_audio_analyzer.ipynb
│   └── 04_qc_decision_engine.ipynb
│
├── rules/
│
├── profiles/
│
├── samples/
│
├── outputs/
│
└── README.md
```

---

# Roadmap

- [x] Asset Decomposer
- [x] Visual Analyzer
- [ ] Audio Analyzer
- [ ] QC Decision Engine
- [ ] Rule Profiles
- [ ] Brand Validation
- [ ] Dashboard
- [ ] Production Deployment

---

## Vision

The long-term objective is to build a multimodal Quality Control platform capable of validating creative assets across multiple channels, brands and formats while integrating seamlessly into enterprise production workflows.

Rather than functioning as a collection of isolated AI tools, QC Video Engine is conceived as a modular decision system where specialized analysis engines collaborate to produce explainable and reproducible quality assessments.
