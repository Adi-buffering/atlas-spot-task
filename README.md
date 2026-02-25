# Atlas Spot Task

End-to-end anomaly detection assignment project for multivariate telemetry time-series using **Isolation Forest**, with a reproducible evaluation and visualization workflow.

## Project Overview

This repository contains:
- A primary anomaly detection pipeline that ingests run files from `dataset/normal` and `dataset/anomalies`, standardizes mixed input formats, trains an Isolation Forest on normal data, and produces predictions + plots.
- A follow-up evaluation/report script that reads saved predictions, computes weak-label metrics, and generates overlay visualizations and summary artifacts.
- Final submission-ready report and metrics files at the repository root.

## Repository Structure

```text
.
├── README.md
├── assignment_step5_6_report.md
├── assignment_step5_6_metrics.csv
├── code/
│   ├── anomaly_detection_pipeline.py
│   ├── evaluation_visualization_report.py
│   ├── assignment_step5_6_metrics.csv
│   ├── step1_prmon_setup_and_familiarization.md
│   └── task_completion_review.md
└── prmon/
    └── ... (upstream prmon project files)
```

## Core Scripts

### 1) Detection pipeline
`code/anomaly_detection_pipeline.py`

What it does:
- Discovers supported files under `dataset/normal` and `dataset/anomalies` (`.csv`, `.tsv`, `.json`, `.log`).
- Normalizes schema/timestamp handling across files.
- Selects numeric feature columns.
- Trains `IsolationForest` (normal-only training split).
- Produces row-level anomaly flags and scores.
- Saves:
  - `predictions.csv`
  - `metrics.json`
  - per-file anomaly plot figures

Run example:

```bash
python code/anomaly_detection_pipeline.py \
  --dataset-path dataset \
  --output-dir anomaly_detection_pipeline_output \
  --contamination 0.05
```

### 2) Evaluation + visualization report
`code/evaluation_visualization_report.py`

What it does:
- Loads pipeline predictions.
- Computes weak-label metrics (precision, recall, F1, false positive rate, confusion matrix).
- Generates SVG overlays and confusion matrix visual.
- Writes analysis markdown report.

Run example:

```bash
python code/evaluation_visualization_report.py \
  --input-predictions code/anomaly_detection_pipeline_output/predictions.csv \
  --output-dir code/evaluation_visualization_report_output
```

## Data Layout Expected

Place your dataset using this structure:

```text
dataset/
├── normal/
│   ├── run_*.csv|tsv|json|log
└── anomalies/
    ├── run_*.csv|tsv|json|log
```

> Note: evaluation uses **weak labels** inferred from folder membership (`normal` vs `anomalies`).

## Environment & Dependencies

Recommended: Python 3.9+

Install required libraries:

```bash
pip install numpy pandas matplotlib scikit-learn
```

## Typical Workflow

1. Prepare dataset folders (`dataset/normal`, `dataset/anomalies`).
2. Run detection pipeline (`anomaly_detection_pipeline.py`).
3. Run evaluation report script (`evaluation_visualization_report.py`).
4. Review generated outputs and final report files.

## Final Submission Artifacts

Primary grading artifacts included at repository root:
- `assignment_step5_6_report.md`
- `assignment_step5_6_metrics.csv`

## Notes

- `prmon/` is included as project context/dependency work from earlier assignment steps.
- The analysis and metrics are designed for assignment reporting and operational triage, not strict point-level ground-truth benchmarking.
