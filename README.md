# Atlas Spot Task — Anomaly Detection Deliverables

This repository contains time-series telemetry, anomaly detection scripts, and clean deliverables for reporting results.

## Quick start

1. Generate evaluation + visualization outputs:
   ```bash
   python code/code_4.py
   ```
2. Prepare a clean upload bundle for **Step 5** and **Step 6**:
   ```bash
   python code/prepare_step56_bundle.py
   ```

## Upload-ready files

After running the commands above, upload from:

- `deliverables/step5_6/step5_evaluation_and_visualization.md`
- `deliverables/step5_6/step6_suitability_tradeoffs.md`
- `deliverables/step5_6/evaluation_metrics.csv`
- `deliverables/step5_6/confusion_matrix.csv`
- `deliverables/step5_6/figures/` (overlay plots and confusion matrix figure)

## What Step 5 and 6 outcomes show

- **Step 5 (Evaluate + Visualize):**
  - Per-file overlay plots show anomaly flags (red markers) on top of original signals.
  - Metrics and confusion matrix summarize detection behavior.
- **Step 6 (Discuss suitability):**
  - Isolation Forest is practical with weak labels and mixed telemetry features.
  - Trade-offs include threshold sensitivity, false-positive risk, and lower interpretability.

## Main scripts

- `code/code_4.py`: computes weak-label metrics and generates overlay visualizations.
- `code/prepare_step56_bundle.py`: builds a clean, focused, upload-ready Step 5/6 bundle.
