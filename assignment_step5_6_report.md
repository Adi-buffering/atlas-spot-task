# Formal Report: Step 5 (Evaluation & Visualization) and Step 6 (Suitability & Trade-Offs)

## Project context
This report documents the final assignment outcomes for anomaly detection on telemetry time series using an Isolation Forest approach.

Per final project direction:
- `code/anomaly_detection_pipeline.py` is the primary detection script (renamed from Code 2),
- `code/evaluation_visualization_report.py` is the primary evaluation/visualization script (renamed from Code 4),
- Code 1 and Code 3 are not used in the final submission path.

---

## Step 5 — Evaluated and visualized the detection results

### Method used for evaluation
The detector produces row-level anomaly flags and scores. Performance is summarized with weak-label metrics, where folder origin is used as approximate ground truth (`normal` vs `anomalies`).

### Quantitative summary
The compact metric sheet is provided in `assignment_step5_6_metrics.csv`, including:
- rows evaluated,
- predicted anomalies,
- precision,
- recall,
- F1 score,
- false positive rate.

### Visualization evidence (anomalies against original time series)
The following final plots explicitly show anomalies flagged over original signal traces:
- `code/outputs_code4/figures/anomaly_io_1_overlay.svg`
- `code/outputs_code4/figures/anomaly_memory_1_overlay.svg`
- `code/outputs_code4/figures/anomaly_processes_1_overlay.svg`
- `code/outputs_code4/figures/anomaly_threads_1_overlay.svg`

Additional diagnostic figure:
- `code/outputs_code4/figures/confusion_matrix_weak_labels.svg`

### Evaluation interpretation
The detector captures substantial anomaly behavior in anomaly-designated runs while keeping false positives within a manageable range for monitoring use. Because labels are weak (folder-level), these values should be interpreted as operational indicators rather than strict ground-truth accuracy.

---

## Step 6 — Suitability of approach and observed trade-offs

### Why Isolation Forest is suitable
1. **Works under weak supervision:** effective when dense point-level labels are unavailable.
2. **Handles multivariate telemetry:** useful for combined resource/process behaviors.
3. **Operationally practical:** outputs point-level flags and scores for triage workflows.

### Trade-offs observed
1. **Weak-label ambiguity:** anomaly files can include normal intervals, affecting measured error rates.
2. **Threshold sensitivity:** fixed contamination/threshold values may need recalibration over time.
3. **Limited interpretability:** root-cause explanation is less direct than explicit rule systems.

### Final recommendation
Use the detector as a **triage mechanism** and combine it with:
- periodic threshold calibration,
- temporal smoothing/aggregation (e.g., consecutive-point confirmation),
- and optional feature engineering for better robustness and interpretability.

---

## Submission package (minimum)
For direct GitHub upload and grading, submit:
1. `assignment_step5_6_report.md` (this formal report)
2. `assignment_step5_6_metrics.csv` (numeric evidence)

---

## AI usage disclosure
- **Dataset generation and collection:** completed manually by me; no AI was used to generate the dataset.
- **Model development:** AI assistance was used after building an initial baseline model.
- **Tool/model used:** Codex 5.3 was used to help optimize and improve the ML model design and implementation.
