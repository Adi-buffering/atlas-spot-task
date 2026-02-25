#!/usr/bin/env python3
"""Code 4: evaluation + visualization using existing deterministic predictions.

This script reuses outputs from code_2 (predictions.csv), computes weak-label metrics,
builds per-file anomaly overlays against the original signal, and writes a concise
suitability/trade-off analysis.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import shutil
from collections import defaultdict
from pathlib import Path
from typing import Dict, List, Tuple


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Code 4 evaluation + visualization")
    parser.add_argument("--input-predictions", default="code/anomaly_detection_pipeline_output/predictions.csv")
    parser.add_argument("--output-dir", default="code/evaluation_visualization_report_output")
    parser.add_argument("--target-signal", default="")
    return parser.parse_args()


def _to_float(value: str) -> float:
    try:
        return float(value)
    except Exception:
        return float("nan")


def _to_int(value: str) -> int:
    try:
        return int(float(value))
    except Exception:
        return 0


def _is_number_column(rows: List[Dict[str, str]], col: str, sample_n: int = 250) -> bool:
    seen = 0
    numeric = 0
    for row in rows[:sample_n]:
        val = row.get(col, "")
        if val is None or val == "":
            continue
        seen += 1
        try:
            float(val)
            numeric += 1
        except Exception:
            pass
    return seen > 0 and numeric / seen > 0.9


def choose_signal_column(rows: List[Dict[str, str]], requested: str) -> str:
    if not rows:
        raise RuntimeError("No rows found in predictions.")
    header = list(rows[0].keys())
    if requested and requested in header:
        return requested

    blocked = {
        "timestamp",
        "weak_label",
        "anomaly_flag",
        "threshold",
        "iforest_raw_prediction",
        "iforest_decision_function",
        "iforest_score_samples",
        "anomaly_score",
    }
    for col in header:
        if col in blocked:
            continue
        if _is_number_column(rows, col):
            return col
    raise RuntimeError("No numeric signal column available for plotting.")


def compute_metrics(rows: List[Dict[str, str]]) -> Dict[str, object]:
    tn = fp = fn = tp = 0
    for row in rows:
        y_true = _to_int(row.get("weak_label", "0"))
        y_pred = _to_int(row.get("anomaly_flag", "0"))
        if y_true == 0 and y_pred == 0:
            tn += 1
        elif y_true == 0 and y_pred == 1:
            fp += 1
        elif y_true == 1 and y_pred == 0:
            fn += 1
        elif y_true == 1 and y_pred == 1:
            tp += 1

    precision = tp / (tp + fp) if (tp + fp) else 0.0
    recall = tp / (tp + fn) if (tp + fn) else 0.0
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) else 0.0
    fpr = fp / (fp + tn) if (fp + tn) else 0.0

    return {
        "labeling_note": (
            "Weak labels are inferred from folder membership only: rows from dataset/anomalies are treated "
            "as anomalous and rows from dataset/normal as normal. Anomaly files may include normal intervals."
        ),
        "n_rows": len(rows),
        "n_predicted_anomalies": tp + fp,
        "confusion_matrix": {"tn": tn, "fp": fp, "fn": fn, "tp": tp},
        "precision": precision,
        "recall": recall,
        "f1": f1,
        "false_positive_rate": fpr,
    }


def _scale(value: float, vmin: float, vmax: float, out_min: float, out_max: float) -> float:
    if math.isnan(value):
        return (out_min + out_max) / 2
    if vmax <= vmin:
        return (out_min + out_max) / 2
    frac = (value - vmin) / (vmax - vmin)
    return out_min + frac * (out_max - out_min)


def _svg_header(width: int, height: int) -> List[str]:
    return [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
        '<rect width="100%" height="100%" fill="white"/>',
    ]


def write_overlay_svg(file_rows: List[Dict[str, str]], signal_col: str, out_file: Path) -> None:
    width, height = 1200, 500
    m_left, m_right, m_top, m_bottom = 80, 30, 45, 60
    plot_w = width - m_left - m_right
    plot_h = height - m_top - m_bottom

    sorted_rows = sorted(file_rows, key=lambda r: _to_float(r.get("timestamp", "0")))
    xs = [_to_float(r.get("timestamp", "0")) for r in sorted_rows]
    ys = [_to_float(r.get(signal_col, "nan")) for r in sorted_rows]

    finite_ys = [y for y in ys if not math.isnan(y)]
    x_min, x_max = min(xs) if xs else 0.0, max(xs) if xs else 1.0
    y_min, y_max = (min(finite_ys), max(finite_ys)) if finite_ys else (0.0, 1.0)
    if y_min == y_max:
        y_min -= 1.0
        y_max += 1.0

    svg = _svg_header(width, height)
    svg.append(f'<text x="{m_left}" y="28" font-size="18" font-family="Arial">Anomaly Overlay | {sorted_rows[0].get("source_file", "unknown")}</text>')

    x0, y0 = m_left, m_top
    svg.append(f'<rect x="{x0}" y="{y0}" width="{plot_w}" height="{plot_h}" fill="none" stroke="#444" stroke-width="1"/>')

    points = []
    for x, y in zip(xs, ys):
        px = _scale(x, x_min, x_max, x0, x0 + plot_w)
        py = _scale(y, y_min, y_max, y0 + plot_h, y0)
        points.append((px, py))
    line_points = " ".join(f"{px:.2f},{py:.2f}" for px, py in points)
    svg.append(f'<polyline points="{line_points}" fill="none" stroke="#1f77b4" stroke-width="1.5"/>')

    for row, (px, py) in zip(sorted_rows, points):
        if _to_int(row.get("anomaly_flag", "0")) == 1:
            svg.append(f'<circle cx="{px:.2f}" cy="{py:.2f}" r="2.6" fill="red"/>')

    # axis labels + legend
    svg.append(f'<text x="{x0 + plot_w/2:.0f}" y="{height - 18}" font-size="13" text-anchor="middle" font-family="Arial">timestamp / row index</text>')
    svg.append(f'<text x="20" y="{y0 + plot_h/2:.0f}" font-size="13" text-anchor="middle" transform="rotate(-90 20 {y0 + plot_h/2:.0f})" font-family="Arial">{signal_col}</text>')
    svg.append(f'<line x1="{width-270}" y1="20" x2="{width-240}" y2="20" stroke="#1f77b4" stroke-width="2"/><text x="{width-235}" y="24" font-size="12" font-family="Arial">signal</text>')
    svg.append(f'<circle cx="{width-255}" cy="38" r="3" fill="red"/><text x="{width-235}" y="42" font-size="12" font-family="Arial">flagged anomaly</text>')

    svg.append("</svg>")
    out_file.write_text("\n".join(svg), encoding="utf-8")


def write_confusion_matrix_svg(metrics: Dict[str, object], out_file: Path) -> None:
    cm = metrics["confusion_matrix"]
    vals = [[cm["tn"], cm["fp"]], [cm["fn"], cm["tp"]]]
    maxv = max(max(row) for row in vals) or 1
    width, height = 520, 380

    svg = _svg_header(width, height)
    svg.append('<text x="30" y="30" font-size="18" font-family="Arial">Row-level confusion matrix (weak labels)</text>')

    start_x, start_y, cell = 160, 80, 110
    labels_x = ["pred normal", "pred anomaly"]
    labels_y = ["actual normal", "actual anomaly"]

    for i in range(2):
        svg.append(f'<text x="{start_x + i*cell + cell/2:.0f}" y="65" font-size="12" text-anchor="middle" font-family="Arial">{labels_x[i]}</text>')
        svg.append(f'<text x="120" y="{start_y + i*cell + cell/2 + 4:.0f}" font-size="12" text-anchor="end" font-family="Arial">{labels_y[i]}</text>')

    for r in range(2):
        for c in range(2):
            v = vals[r][c]
            blue = int(255 - (v / maxv) * 160)
            color = f"rgb({blue},{blue},{255})"
            x = start_x + c * cell
            y = start_y + r * cell
            svg.append(f'<rect x="{x}" y="{y}" width="{cell}" height="{cell}" fill="{color}" stroke="#333"/>')
            svg.append(f'<text x="{x + cell/2:.0f}" y="{y + cell/2 + 6:.0f}" font-size="22" text-anchor="middle" font-family="Arial">{v}</text>')

    svg.append("</svg>")
    out_file.write_text("\n".join(svg), encoding="utf-8")


def write_metrics_summary_csv(metrics: Dict[str, object], out_file: Path) -> None:
    rows = [
        ["precision", metrics["precision"]],
        ["recall", metrics["recall"]],
        ["f1", metrics["f1"]],
        ["false_positive_rate", metrics["false_positive_rate"]],
    ]
    with out_file.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["metric", "value"])
        w.writerows(rows)


def write_analysis_md(metrics: Dict[str, object], signal_col: str, feature_cols: List[str], rows: List[Dict[str, str]], out_file: Path) -> None:
    normal_rows = [r for r in rows if r.get("split_label") == "normal"]
    anomaly_rows = [r for r in rows if r.get("split_label") == "anomaly_file"]
    normal_rate = sum(_to_int(r.get("anomaly_flag", "0")) for r in normal_rows) / len(normal_rows) if normal_rows else 0.0
    anomaly_rate = sum(_to_int(r.get("anomaly_flag", "0")) for r in anomaly_rows) / len(anomaly_rows) if anomaly_rows else 0.0

    text = f"""# Suitability and Trade-Off Analysis

## Why Isolation Forest fits this project
Isolation Forest is suitable here because the project has **weak labels** (folder-level, not dense point annotations), and the model can be trained in an unsupervised/normal-only way while still producing point-level outlier scores. It also handles **multivariate numeric telemetry** efficiently (features detected: {', '.join(feature_cols)}).

## Strengths observed in current results
- Works with weak supervision and still provides actionable anomaly flags.
- Captures unusual combinations across multiple metrics rather than one handcrafted rule.
- In this run, row-level recall is **{metrics['recall']:.4f}**, indicating many rows in anomaly-folder files are surfaced.

## Weaknesses and trade-offs observed
- Folder-derived weak labels inflate ambiguity: anomaly files can contain normal sections, so confusion matrix values are approximate.
- Fixed contamination/threshold can over- or under-alert when data drift changes baseline behavior.
- Normal-folder false positives are non-trivial in practice (weak-label FPR={metrics['false_positive_rate']:.4f}), which can increase alert fatigue.
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
- Overlay signal column: `{signal_col}`
- Flag rate in normal-folder rows: **{normal_rate:.4f}**
- Flag rate in anomaly-folder rows: **{anomaly_rate:.4f}**
- Precision={metrics['precision']:.4f}, Recall={metrics['recall']:.4f}, F1={metrics['f1']:.4f}
"""
    out_file.write_text(text, encoding="utf-8")


def main() -> None:
    args = parse_args()

    repo_root = Path(__file__).resolve().parents[1]
    input_path = Path(args.input_predictions)
    if not input_path.is_absolute():
        input_path = repo_root / input_path

    out_dir = Path(args.output_dir)
    if not out_dir.is_absolute():
        out_dir = repo_root / out_dir
    figures_dir = out_dir / "figures"
    out_dir.mkdir(parents=True, exist_ok=True)
    figures_dir.mkdir(parents=True, exist_ok=True)

    if not input_path.exists():
        raise FileNotFoundError(f"Missing input predictions: {input_path}")

    with input_path.open("r", newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))

    signal_col = choose_signal_column(rows, args.target_signal)
    feature_cols = [
        c
        for c in rows[0].keys()
        if c not in {
            "source_file",
            "source_path",
            "split_label",
            "timestamp",
            "weak_label",
            "anomaly_flag",
            "anomaly_score",
            "iforest_raw_prediction",
            "iforest_decision_function",
            "iforest_score_samples",
            "threshold",
        }
        and _is_number_column(rows, c)
    ]

    # 1) predictions copy for code4 deliverable
    shutil.copyfile(input_path, out_dir / "predictions.csv")

    # 2) per-file overlays for csv runs
    by_file: Dict[str, List[Dict[str, str]]] = defaultdict(list)
    for row in rows:
        source_file = row.get("source_file", "")
        if source_file.lower().endswith(".csv"):
            by_file[source_file].append(row)
    for source_file, file_rows in sorted(by_file.items()):
        out_file = figures_dir / f"{Path(source_file).stem}_overlay.svg"
        write_overlay_svg(file_rows, signal_col=signal_col, out_file=out_file)

    # 3) aggregate metrics and figures
    metrics = compute_metrics(rows)
    (out_dir / "metrics.json").write_text(json.dumps(metrics, indent=2), encoding="utf-8")
    cm = metrics["confusion_matrix"]
    with (out_dir / "confusion_matrix.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["", "pred_normal", "pred_anomaly"])
        w.writerow(["actual_normal", cm["tn"], cm["fp"]])
        w.writerow(["actual_anomaly", cm["fn"], cm["tp"]])
    write_metrics_summary_csv(metrics, out_dir / "metrics_summary.csv")
    write_confusion_matrix_svg(metrics, figures_dir / "confusion_matrix_weak_labels.svg")

    # 4) analysis report
    write_analysis_md(metrics, signal_col, feature_cols, rows, out_dir / "analysis.md")


if __name__ == "__main__":
    main()
