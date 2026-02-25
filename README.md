# Atlas Spot Task: Telemetry Anomaly Detection

This project is your assignment implementation for anomaly detection on telemetry time-series data using an **Isolation Forest** workflow.

It includes:
- a robust data-loading + anomaly detection pipeline,
- an evaluation/visualization script for reporting,
- final submission artifacts for Step 5/6.

---

## 1) What this project does

The repository solves a practical monitoring problem:
- ingest telemetry runs from two folders (`normal` and `anomalies`),
- normalize mixed file formats,
- train on normal behavior,
- flag anomalous rows,
- evaluate with weak labels,
- generate visuals + report-ready outputs.

Because labels are folder-level (not dense point-level truth), evaluation is **weak-label based** and should be treated as operational guidance.

---

## 2) Project layout

```text
atlas-spot-task/
├── assignment_step5_6_report.md
├── assignment_step5_6_metrics.csv
├── code/
│   ├── anomaly_detection_pipeline.py
│   ├── evaluation_visualization_report.py
│   ├── assignment_step5_6_metrics.csv
│   ├── step1_prmon_setup_and_familiarization.md
│   └── task_completion_review.md
└── prmon/
    └── (reference / setup artifacts from earlier assignment work)
```

---

## 3) Main scripts

### `code/anomaly_detection_pipeline.py`

Primary detection pipeline.

**Responsibilities**
- Discovers and parses supported files: `.csv`, `.tsv`, `.json`, `.log`.
- Standardizes timestamps and numeric telemetry fields.
- Trains `IsolationForest` on rows from `dataset/normal`.
- Predicts anomaly flags/scores for all rows.
- Exports predictions, metrics, and per-file figures.

**Example run**

```bash
python code/anomaly_detection_pipeline.py \
  --dataset-path dataset \
  --output-dir anomaly_detection_pipeline_output \
  --contamination 0.05
```

---

### `code/evaluation_visualization_report.py`

Evaluation and reporting utility over saved predictions.

**Responsibilities**
- Reads `predictions.csv` from the detection run.
- Computes weak-label metrics: precision, recall, F1, false-positive rate, confusion matrix.
- Creates SVG overlays (signal + anomaly markers).
- Produces summary tables and analysis markdown.

**Example run**

```bash
python code/evaluation_visualization_report.py \
  --input-predictions code/anomaly_detection_pipeline_output/predictions.csv \
  --output-dir code/evaluation_visualization_report_output
```

---

## 4) Expected dataset format

```text
dataset/
├── normal/
│   ├── *.csv|*.tsv|*.json|*.log
└── anomalies/
    ├── *.csv|*.tsv|*.json|*.log
```

- `normal/`: baseline behavior used for training.
- `anomalies/`: runs expected to contain anomalous behavior.

> Weak labels are inferred from folder membership, not true point-by-point annotations.

---

## 5) Environment setup

Recommended: **Python 3.9+**

Install dependencies:

```bash
pip install numpy pandas matplotlib scikit-learn
```

---

## 6) Typical end-to-end workflow

1. Prepare `dataset/normal` and `dataset/anomalies`.
2. Run anomaly detection pipeline.
3. Run evaluation/visualization report script.
4. Review outputs and include required files in submission.

---

## 7) Final assignment artifacts

Primary deliverables in this repository:
- `assignment_step5_6_report.md`
- `assignment_step5_6_metrics.csv`

These are the concise report + numeric evidence files for grading.

---

## 8) Notes

- The `prmon/` directory is retained from earlier assignment setup/familiarization tasks.
- Isolation Forest output should be used as **triage support**, not a final root-cause explanation by itself.
