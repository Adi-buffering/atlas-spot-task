# Step 6 — Suitability and Trade-Off Discussion

## Chosen approach
The project uses **Isolation Forest** for anomaly detection on multivariate telemetry.

## Why this approach is suitable
- Works well when detailed point-level labels are unavailable.
- Handles mixed process/resource metrics efficiently.
- Produces per-row outlier flags and scores for operational triage.

## Trade-offs observed
- Weak labels can overstate errors because anomaly files may still contain normal windows.
- A single threshold can lead to false positives if baseline behavior drifts.
- Isolation Forest is less interpretable than rule-based detectors without added diagnostics.

## Practical recommendation
Use model outputs as triage signals, then add threshold calibration and temporal smoothing to reduce alert noise.

---

For the full run-specific analysis narrative, see `analysis_full.md`.
