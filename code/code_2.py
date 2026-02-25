#!/usr/bin/env python3
"""
# Isolation Forest Time-Series Anomaly Detection Pipeline

This script discovers multiformat run files under `dataset/normal` and `dataset/anomalies`,
normalizes schema differences, trains Isolation Forest on normal runs, predicts anomalies on
all runs, evaluates weak-label metrics, and saves tabular + figure outputs.

Usage example:
    python isolation_forest_timeseries_pipeline.py --dataset-path dataset --contamination 0.05
"""

from __future__ import annotations

import argparse
import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Tuple

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest
from sklearn.impute import SimpleImputer
from sklearn.metrics import (
    average_precision_score,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

RANDOM_SEED = 42
SUPPORTED_SUFFIXES = {".csv", ".tsv", ".json", ".log"}
DEFAULT_TIMESTAMP_CANDIDATES = ["time", "timestamp", "datetime", "date", "wtime", "index"]


def parse_args() -> argparse.Namespace:
    """CLI/config block for reproducible runs."""
    parser = argparse.ArgumentParser(description="Isolation Forest anomaly detection for time-series runs")
    parser.add_argument("--dataset-path", default="dataset", help="Root dataset folder")
    parser.add_argument("--output-dir", default="outputs", help="Output folder")
    parser.add_argument(
        "--contamination",
        type=float,
        default=0.05,
        help="Expected anomaly fraction for Isolation Forest",
    )
    parser.add_argument(
        "--feature-cols",
        default="",
        help="Comma-separated numeric feature columns to use. Auto-selects if omitted.",
    )
    parser.add_argument(
        "--timestamp-col",
        default="",
        help="Optional timestamp column override. Falls back to row index if missing.",
    )
    parser.add_argument(
        "--target-signal",
        default="",
        help="Signal column to show in plots. Auto-selected if omitted.",
    )
    return parser.parse_args()


def discover_files(base_path: Path) -> List[Tuple[Path, str]]:
    """Find candidate files and attach split labels."""
    discovered: List[Tuple[Path, str]] = []
    for split, label in (("normal", "normal"), ("anomalies", "anomaly_file")):
        split_dir = base_path / split
        if not split_dir.exists():
            logging.warning("Missing split directory: %s", split_dir)
            continue
        for path in sorted(split_dir.iterdir()):
            if path.is_file() and path.suffix.lower() in SUPPORTED_SUFFIXES:
                discovered.append((path, label))
    logging.info("Discovered %d files", len(discovered))
    return discovered


def _read_delimited(path: Path, sep: str) -> pd.DataFrame:
    """Read delimited text across multiple pandas versions."""
    try:
        return pd.read_csv(path, sep=sep, engine="python", on_bad_lines="skip")
    except TypeError:
        # pandas<1.3 compatibility
        return pd.read_csv(path, sep=sep, engine="python", error_bad_lines=False, warn_bad_lines=False)


def _read_json_flexible(path: Path) -> pd.DataFrame:
    """Read either line-delimited JSON, array-like JSON, or nested dict JSON."""
    try:
        df = pd.read_json(path, lines=True)
        if not df.empty and len(df.columns) > 1:
            return df
    except Exception:
        pass

    try:
        df = pd.read_json(path)
        if isinstance(df, pd.DataFrame):
            return df.reset_index(drop=True)
    except Exception:
        pass

    with path.open("r", encoding="utf-8", errors="ignore") as f:
        payload = json.load(f)

    if isinstance(payload, list):
        return pd.json_normalize(payload)
    if isinstance(payload, dict):
        rows: List[Dict[str, object]] = []
        for key, value in payload.items():
            if isinstance(value, dict):
                row = {"section": key}
                row.update(value)
                rows.append(row)
            else:
                rows.append({"section": key, "value": value})
        return pd.DataFrame(rows)

    return pd.DataFrame()


def load_single_file(path: Path) -> pd.DataFrame:
    """Robust loader for csv/tsv/json/log with malformed row tolerance."""
    if path.stat().st_size == 0:
        return pd.DataFrame()

    suffix = path.suffix.lower()
    if suffix == ".csv":
        return _read_delimited(path, sep=",")
    if suffix == ".tsv":
        return _read_delimited(path, sep="\t")
    if suffix == ".json":
        return _read_json_flexible(path)

    # .log fallback: try whitespace-delimited tabular parse, then CSV sniffing.
    try:
        return pd.read_csv(path, sep=r"\s+", engine="python", on_bad_lines="skip")
    except TypeError:
        # pandas<1.3 compatibility
        return pd.read_csv(path, sep=r"\s+", engine="python", error_bad_lines=False, warn_bad_lines=False)
    except Exception:
        try:
            return pd.read_csv(path, sep=None, engine="python", on_bad_lines="skip")
        except TypeError:
            return pd.read_csv(path, sep=None, engine="python", error_bad_lines=False, warn_bad_lines=False)


def _select_timestamp_column(df: pd.DataFrame, override: str = "") -> Optional[str]:
    if override and override in df.columns:
        return override
    lowered = {c.lower(): c for c in df.columns}
    for candidate in DEFAULT_TIMESTAMP_CANDIDATES:
        if candidate in lowered:
            return lowered[candidate]
    return None


def standardize_dataframe(df: pd.DataFrame, file_path: Path, split: str, timestamp_override: str = "") -> pd.DataFrame:
    """Normalize columns and enrich with required metadata."""
    if df is None or df.empty:
        return pd.DataFrame()

    df = df.copy()
    df.columns = [str(c).strip() for c in df.columns]

    ts_col = _select_timestamp_column(df, timestamp_override)
    if ts_col is None:
        df["timestamp"] = np.arange(len(df), dtype=int)
    else:
        df["timestamp"] = pd.to_numeric(df[ts_col], errors="coerce")
        missing_ts = df["timestamp"].isna()
        if missing_ts.any():
            df.loc[missing_ts, "timestamp"] = np.flatnonzero(missing_ts.to_numpy())

    for col in df.columns:
        if col in {"timestamp"}:
            continue
        # Use `coerce` + selective replacement for compatibility with pandas builds
        # where `errors="ignore"` is rejected.
        coerced = pd.to_numeric(df[col], errors="coerce")
        if coerced.notna().any():
            df[col] = coerced

    df["source_file"] = file_path.name
    df["source_path"] = str(file_path)
    df["split_label"] = split
    df["weak_label"] = int(split == "anomaly_file")

    cols_front = ["source_file", "source_path", "split_label", "timestamp"]
    remaining = [c for c in df.columns if c not in cols_front]
    return df[cols_front + remaining]


def build_master_dataframe(base_path: Path, timestamp_override: str = "") -> pd.DataFrame:
    """Load all files, logging parse failures without crashing."""
    all_frames: List[pd.DataFrame] = []
    for path, split in discover_files(base_path):
        try:
            raw = load_single_file(path)
            std = standardize_dataframe(raw, path, split, timestamp_override=timestamp_override)
            if std.empty:
                logging.info("Skipping empty/unreadable tabular content from %s", path)
                continue

            numeric_candidates = std.select_dtypes(include=[np.number]).columns.tolist()
            numeric_candidates = [c for c in numeric_candidates if c not in {"timestamp", "weak_label"}]
            if len(std) < 5 or not numeric_candidates:
                logging.warning(
                    "Skipping non-timeseries/sparse frame from %s (rows=%d, numeric_features=%d)",
                    path,
                    len(std),
                    len(numeric_candidates),
                )
                continue

            all_frames.append(std)
            logging.info("Loaded %s rows=%d cols=%d", path.name, len(std), len(std.columns))
        except Exception as exc:
            logging.warning("Failed to parse %s: %s", path, exc)

    if not all_frames:
        raise RuntimeError("No readable files were loaded. Check dataset path and formats.")

    master = pd.concat(all_frames, ignore_index=True, sort=False)
    master["weak_label"] = (master["split_label"] == "anomaly_file").astype(int)
    return master


def choose_feature_columns(df: pd.DataFrame, requested: Sequence[str]) -> List[str]:
    """Choose numeric model features while excluding metadata columns."""
    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    blocked = {"timestamp", "weak_label", "anomaly_score", "anomaly_flag"}
    numeric_cols = [c for c in numeric_cols if c not in blocked]

    if requested:
        missing = [c for c in requested if c not in df.columns]
        if missing:
            logging.warning("Requested feature columns missing: %s", missing)
        selected = [c for c in requested if c in numeric_cols]
        if selected:
            return selected

    if not numeric_cols:
        raise RuntimeError("No numeric feature columns available for modeling.")

    return numeric_cols


def fit_isolation_forest(train_df: pd.DataFrame, feature_cols: Sequence[str], contamination: float) -> Pipeline:
    """Train Isolation Forest on normal data with preprocessing."""
    X_train = train_df.loc[:, feature_cols].copy()

    model = Pipeline(
        steps=[
            ("imputer", SimpleImputer(strategy="median")),
            ("scaler", StandardScaler()),
            (
                "iso",
                IsolationForest(
                    n_estimators=300,
                    contamination=contamination,
                    random_state=RANDOM_SEED,
                    n_jobs=-1,
                ),
            ),
        ]
    )
    model.fit(X_train)
    return model


def predict_and_score(model: Pipeline, df: pd.DataFrame, feature_cols: Sequence[str]) -> pd.DataFrame:
    """Infer anomaly scores and binary flags for all points."""
    X = df.loc[:, feature_cols].copy()
    iso = model.named_steps["iso"]

    pred = model.predict(X)  # 1 normal, -1 anomaly
    decision_values = model.decision_function(X)
    score_samples = model.score_samples(X)

    out = df.copy()
    out["iforest_raw_prediction"] = pred
    out["iforest_decision_function"] = decision_values
    out["iforest_score_samples"] = score_samples

    out["anomaly_flag"] = (pred == -1).astype(int)
    out["anomaly_score"] = -decision_values
    out["threshold"] = float(-iso.offset_)
    return out


def evaluate(pred_df: pd.DataFrame) -> Dict[str, object]:
    """Evaluate weak-label metrics using file-level split as pseudo ground truth."""
    y_true = pred_df["weak_label"].astype(int).to_numpy()
    y_pred = pred_df["anomaly_flag"].astype(int).to_numpy()
    y_score = pred_df["anomaly_score"].to_numpy()

    tn, fp, fn, tp = confusion_matrix(y_true, y_pred, labels=[0, 1]).ravel()

    metrics: Dict[str, object] = {
        "labeling_note": (
            "Weak labels were used: points from dataset/anomalies are treated as anomalous and "
            "points from dataset/normal are treated as normal. This overestimates anomaly coverage "
            "because anomaly files can contain normal points."
        ),
        "n_rows": int(len(pred_df)),
        "n_predicted_anomalies": int(y_pred.sum()),
        "confusion_matrix": {"tn": int(tn), "fp": int(fp), "fn": int(fn), "tp": int(tp)},
        "precision": float(precision_score(y_true, y_pred, zero_division=0)),
        "recall": float(recall_score(y_true, y_pred, zero_division=0)),
        "f1": float(f1_score(y_true, y_pred, zero_division=0)),
    }

    if len(np.unique(y_true)) > 1:
        metrics["roc_auc"] = float(roc_auc_score(y_true, y_score))
        metrics["pr_auc"] = float(average_precision_score(y_true, y_score))
    else:
        metrics["roc_auc"] = None
        metrics["pr_auc"] = None

    return metrics


def plot_results(pred_df: pd.DataFrame, out_dir: Path, feature_for_plot: str) -> None:
    """Save per-file time-series and score plots with anomaly highlights."""
    fig_dir = out_dir / "figures"
    fig_dir.mkdir(parents=True, exist_ok=True)

    for source_file, gdf in pred_df.groupby("source_file", sort=True):
        gdf = gdf.sort_values("timestamp").reset_index(drop=True)
        x = gdf["timestamp"]
        y = gdf[feature_for_plot]
        is_anom = gdf["anomaly_flag"] == 1

        fig, axes = plt.subplots(2, 1, figsize=(12, 7), sharex=True)

        axes[0].plot(x, y, linewidth=1.5, label=feature_for_plot)
        axes[0].scatter(x[is_anom], y[is_anom], color="red", s=18, label="flagged anomaly")
        axes[0].set_title(f"{source_file} | signal={feature_for_plot} | split={gdf['split_label'].iloc[0]}")
        axes[0].set_ylabel("Signal")
        axes[0].legend(loc="best")
        axes[0].grid(alpha=0.25)

        axes[1].plot(x, gdf["anomaly_score"], color="purple", linewidth=1.2, label="anomaly_score")
        axes[1].axhline(gdf["threshold"].iloc[0], color="black", linestyle="--", label="threshold")
        axes[1].set_ylabel("Anomaly score")
        axes[1].set_xlabel("timestamp / index")
        axes[1].legend(loc="best")
        axes[1].grid(alpha=0.25)

        fig.tight_layout()
        save_path = fig_dir / f"{Path(source_file).stem}_anomaly_plot.png"
        fig.savefig(save_path, dpi=150)
        plt.close(fig)


def save_outputs(pred_df: pd.DataFrame, metrics: Dict[str, object], out_dir: Path) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    pred_df.to_csv(out_dir / "predictions.csv", index=False)
    with (out_dir / "metrics.json").open("w", encoding="utf-8") as f:
        json.dump(metrics, f, indent=2)


def main() -> None:
    """Run full pipeline end-to-end."""
    logging.basicConfig(level=logging.INFO, format="[%(levelname)s] %(message)s")
    args = parse_args()

    np.random.seed(RANDOM_SEED)

    base_path = Path(args.dataset_path)
    out_dir = Path(args.output_dir)

    requested_features = [c.strip() for c in args.feature_cols.split(",") if c.strip()]

    logging.info("Building master dataframe from %s", base_path)
    master = build_master_dataframe(base_path=base_path, timestamp_override=args.timestamp_col.strip())

    feature_cols = choose_feature_columns(master, requested=requested_features)
    logging.info("Using feature columns (%d): %s", len(feature_cols), feature_cols)

    train_df = master[master["split_label"] == "normal"].copy()
    if train_df.empty:
        raise RuntimeError("No normal rows found for model training.")

    model = fit_isolation_forest(train_df, feature_cols=feature_cols, contamination=args.contamination)

    pred_df = predict_and_score(model, master, feature_cols=feature_cols)
    metrics = evaluate(pred_df)

    if args.target_signal and args.target_signal in pred_df.columns:
        feature_for_plot = args.target_signal
    else:
        feature_for_plot = feature_cols[0]

    plot_results(pred_df, out_dir=out_dir, feature_for_plot=feature_for_plot)
    save_outputs(pred_df, metrics=metrics, out_dir=out_dir)

    # Ensure one normal + one anomaly figure are explicitly generated for quick inspection.
    fig_dir = out_dir / "figures"
    for split, filename in (("normal", "example_normal.csv"), ("anomaly_file", "example_anomaly.csv")):
        subset = pred_df[pred_df["split_label"] == split]
        if not subset.empty:
            sample_file = subset["source_file"].iloc[0]
            subset[subset["source_file"] == sample_file].head(200).to_csv(fig_dir / filename, index=False)

    logging.info("Saved predictions to %s", out_dir / "predictions.csv")
    logging.info("Saved metrics to %s", out_dir / "metrics.json")
    logging.info("Saved figures to %s", out_dir / "figures")
    logging.info("Weak-label metrics: %s", json.dumps(metrics, indent=2))


if __name__ == "__main__":
    main()
