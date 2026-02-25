# Suitability and Trade-Off Analysis

## Why Isolation Forest fits this project
Isolation Forest is suitable here because the project has **weak labels** (folder-level, not dense point annotations), and the model can be trained in an unsupervised/normal-only way while still producing point-level outlier scores. It also handles **multivariate numeric telemetry** efficiently (features detected: Time, wtime, pss, rss, swap, vmem, rchar, read_bytes, wchar, write_bytes, rx_bytes, rx_packets, tx_bytes, tx_packets, stime, utime, nprocs, nthreads, Avg, Max, max_pss, cpu, threads).

## Strengths observed in current results
- Works with weak supervision and still provides actionable anomaly flags.
- Captures unusual combinations across multiple metrics rather than one handcrafted rule.
- In this run, row-level recall is **0.9202**, indicating many rows in anomaly-folder files are surfaced.

## Weaknesses and trade-offs observed
- Folder-derived weak labels inflate ambiguity: anomaly files can contain normal sections, so confusion matrix values are approximate.
- Fixed contamination/threshold can over- or under-alert when data drift changes baseline behavior.
- Normal-folder false positives are non-trivial in practice (weak-label FPR=0.0509), which can increase alert fatigue.
- Isolation Forest scores are not inherently explanatory, limiting root-cause interpretability.

## Practical implications for production monitoring
- Use detections as triage signals, not definitive fault labels.
- Pair alerts with time-window context and analyst review.
- Monitor alert volumes and adjust thresholds periodically as system behavior shifts.

## Concrete improvement options
1. Calibrate thresholds/contamination on a reviewed validation window and operating-cost targets.
2. Add temporal features (rolling mean/std, deltas, seasonal baselines) to improve robustness.
3. Apply temporal post-processing (e.g., require k consecutive points) to suppress isolated spikes.
4. Benchmark alternatives (LOF, One-Class SVM, sequence autoencoders) under the same evaluation harness.

## Run-specific notes
- Overlay signal column: `Time`
- Flag rate in normal-folder rows: **0.0509**
- Flag rate in anomaly-folder rows: **0.9202**
- Precision=0.9755, Recall=0.9202, F1=0.9471
