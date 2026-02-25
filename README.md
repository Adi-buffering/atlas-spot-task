# atlas-spot-task

This repository now includes finalized outputs for the assignment, including:
- anomaly detection pipeline outputs,
- evaluation metrics,
- and visualization figures showing anomaly flags over original time series.

## Final status
All requested assignment results are completed, including:
1. anomaly-detection execution on the provided dataset,
2. evaluation metrics (precision/recall/F1/FPR),
3. final visual figures (overlay anomaly plots + confusion matrix),
4. formal Step 5 and Step 6 reporting documents.

## Main scripts (authoritative)
> Per your latest instruction, **Code 2 and Code 4 are the main scripts**, now renamed by role.

- `code/anomaly_detection_pipeline.py` (formerly `code_2.py`)  
  Main anomaly-detection pipeline.
- `code/evaluation_visualization_report.py` (formerly `code_4.py`)  
  Step 5/6 evaluation + visualization artifact generator.

`code_1.py` and `code_3.py` are legacy/auxiliary and are not required for the final submission flow.

## Recommended run order
```bash
python code/anomaly_detection_pipeline.py
python code/evaluation_visualization_report.py
```

## Final figures to show in submission
Use these figures directly in your final write-up:
- `code/outputs_code4/figures/anomaly_io_1_overlay.svg`
- `code/outputs_code4/figures/anomaly_memory_1_overlay.svg`
- `code/outputs_code4/figures/anomaly_processes_1_overlay.svg`
- `code/outputs_code4/figures/anomaly_threads_1_overlay.svg`
- `code/outputs_code4/figures/confusion_matrix_weak_labels.svg`

## Direct-upload reporting docs
- `assignment_step5_6_report.md` (formal report)
- `assignment_step5_6_metrics.csv` (compact metrics evidence)
