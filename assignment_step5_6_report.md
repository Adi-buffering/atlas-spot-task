# Assignment — Step 5 & Step 6 (Final Upload Version)

This is a compact, upload-ready report that completes:
- **Step 5:** Evaluate and visualize anomaly detection results.
- **Step 6:** Discuss suitability and trade-offs of the chosen method.

---

## Step 5 — Evaluate and visualize detection results

### Detection approach used
The anomaly detector is **Isolation Forest** applied to multivariate telemetry features, with weak labels derived from source folders (`normal` vs `anomalies`).

### Quantitative evaluation (row-level, weak-label)
See `assignment_step5_6_metrics.csv` for upload-ready metric values.

### Visual evidence (anomalies flagged on original time series)
The following figures show the original signal (blue) with flagged anomalies (red):

- `code/outputs_code4/figures/anomaly_io_1_overlay.svg`
- `code/outputs_code4/figures/anomaly_memory_1_overlay.svg`
- `code/outputs_code4/figures/anomaly_processes_1_overlay.svg`
- `code/outputs_code4/figures/anomaly_threads_1_overlay.svg`

Baseline overlays (for comparison):
- `code/outputs_code4/figures/baseline_run1_overlay.svg`
- `code/outputs_code4/figures/baseline_run2_overlay.svg`
- `code/outputs_code4/figures/baseline_run3_overlay.svg`

Confusion matrix figure:
- `code/outputs_code4/figures/confusion_matrix_weak_labels.svg`

### Short interpretation
- The model identifies many points in anomaly scenarios while keeping false positives moderate.
- Since labels are weak (folder-level), these metrics approximate behavior but are still useful for practical monitoring.

---

## Step 6 — Suitability and trade-offs

### Why Isolation Forest is suitable here
1. **Works with weak/noisy labels**: good fit when dense ground truth is unavailable.
2. **Handles multivariate telemetry**: captures unusual combinations across multiple resource/process metrics.
3. **Operationally practical**: produces point-level flags and anomaly scores suitable for triage.

### Trade-offs observed
1. **Weak-label uncertainty**: anomaly files may include normal windows, so metric interpretation is approximate.
2. **Threshold sensitivity**: fixed threshold/contamination may need recalibration as workloads drift.
3. **Interpretability limits**: Isolation Forest is less directly explainable than rule-based detectors.

### Final recommendation
Use Isolation Forest alerts as **triage signals**, then improve reliability with:
- periodic threshold calibration,
- temporal smoothing (e.g., consecutive-point rules),
- and optional feature enrichment (rolling stats/deltas).

---

## Notes for submission
If your instructor allows only one or two files, upload:
1. `assignment_step5_6_report.md` (this report)
2. `assignment_step5_6_metrics.csv` (metrics evidence)

These two files are enough to present the last part of the assignment in a clean format.
