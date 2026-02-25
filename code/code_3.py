#!/usr/bin/env python3
"""Concise Isolation Forest pipeline for CSV time-series anomaly detection."""

import argparse
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest
from sklearn.impute import SimpleImputer
from sklearn.metrics import confusion_matrix, f1_score
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler


def main():
    parser = argparse.ArgumentParser(description="Isolation Forest on dataset/{normal,anomalies} CSV files")
    parser.add_argument("--dataset-path", default="dataset", help="Root dataset path")
    parser.add_argument("--contamination", type=float, default=0.05, help="IsolationForest contamination")
    parser.add_argument("--output-dir", default="outputs", help="Output directory")
    args = parser.parse_args()

    np.random.seed(42)
    base = Path(args.dataset_path)
    out_dir = Path(args.output_dir)
    fig_dir = out_dir / "figures"
    fig_dir.mkdir(parents=True, exist_ok=True)

    rows = []
    for split, label in [("normal", 0), ("anomalies", 1)]:
        for f in sorted((base / split).glob("*.csv")):
            try:
                df = pd.read_csv(f)
            except Exception as e:
                print(f"[WARN] Failed to read {f}: {e}")
                continue
            if df.empty:
                continue
            ts_col = next((c for c in df.columns if c.lower() in {"time", "timestamp", "datetime", "date", "wtime"}), None)
            df["timestamp"] = pd.to_numeric(df[ts_col], errors="coerce") if ts_col else np.arange(len(df))
            df["timestamp"] = df["timestamp"].fillna(pd.Series(np.arange(len(df)), index=df.index))
            num_cols = df.select_dtypes(include=[np.number]).columns.tolist()
            num_cols = [c for c in num_cols if c != "timestamp"]
            if not num_cols:
                print(f"[WARN] No numeric features in {f}, skipping")
                continue
            keep = ["timestamp"] + num_cols
            tmp = df[keep].copy()
            tmp["source_file"] = f.name
            tmp["split"] = split
            tmp["y_true"] = label
            rows.append(tmp)

    if not rows:
        raise RuntimeError("No CSV time-series rows loaded. Check dataset path and file formats.")

    data = pd.concat(rows, ignore_index=True)
    feature_cols = [c for c in data.columns if c not in {"timestamp", "source_file", "split", "y_true"}]

    train = data[data["split"] == "normal"]
    if train.empty:
        raise RuntimeError("No normal data available for training.")

    model = Pipeline(
        [
            ("imputer", SimpleImputer(strategy="median")),
            ("scaler", StandardScaler()),
            (
                "iforest",
                IsolationForest(
                    n_estimators=300,
                    contamination=args.contamination,
                    random_state=42,
                    n_jobs=-1,
                ),
            ),
        ]
    )
    model.fit(train[feature_cols])

    pred = model.predict(data[feature_cols])
    decision = model.decision_function(data[feature_cols])
    data["anomaly_flag"] = (pred == -1).astype(int)
    data["anomaly_score"] = -decision

    out_file = out_dir / "predictions.csv"
    data.to_csv(out_file, index=False)

    cm = confusion_matrix(data["y_true"], data["anomaly_flag"], labels=[0, 1])
    f1 = f1_score(data["y_true"], data["anomaly_flag"], zero_division=0)
    print("Confusion matrix [[TN, FP], [FN, TP]]:")
    print(cm)
    print(f"F1 score: {f1:.4f}")
    print("Note: weak labels are file-level (all rows in anomalies/ treated as potentially anomalous).")

    plot_col = feature_cols[0]
    for split in ["normal", "anomalies"]:
        sample = data[data["split"] == split]
        if sample.empty:
            continue
        file_name = sample["source_file"].iloc[0]
        run = sample[sample["source_file"] == file_name].sort_values("timestamp")
        mask = run["anomaly_flag"] == 1

        plt.figure(figsize=(10, 4))
        plt.plot(run["timestamp"], run[plot_col], label=plot_col, linewidth=1.5)
        plt.scatter(run.loc[mask, "timestamp"], run.loc[mask, plot_col], c="red", s=18, label="Detected anomaly")
        plt.title(f"{split} example: {file_name}")
        plt.xlabel("timestamp / index")
        plt.ylabel(plot_col)
        plt.legend()
        plt.grid(alpha=0.3)
        plt.tight_layout()
        plt.savefig(fig_dir / f"example_{split}.png", dpi=150)
        plt.close()

    print(f"Saved: {out_file}")
    print(f"Saved figures in: {fig_dir}")


if __name__ == "__main__":
    main()
