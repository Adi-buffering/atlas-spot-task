# Step 1 — prmon Installation and Familiarization (Reproducible Log)

This file documents the exact commands used to install/build `prmon`, validate burner binaries, and generate baseline/anomaly monitoring runs.

## 1) Clone and build prmon

```bash
git clone --recurse-submodules https://github.com/HSF/prmon.git
cd prmon
mkdir -p build
cd build

cmake -DCMAKE_INSTALL_PREFIX="$HOME/prmon-install" -S .. -B .
make -j4
make install
make package

# Optional rebuild variant used during validation
cmake -DUSE_EXTERNAL_SPDLOG=FALSE -DCMAKE_INSTALL_PREFIX="$HOME/prmon-install" -S .. -B .
make test
```

## 2) Verify burner test binaries and runtime paths

```bash
cd package/tests
pwd
ls

export PATH="$HOME/prmon-install/bin:$PATH"

# Notes:
# - If you run from build/package/tests, ./mem-burner works directly.
# - If you run from repo root, use ./build/package/tests/mem-burner.

cd "$(git rev-parse --show-toplevel)"
cmake --build ./build --target mem-burner -j"$(nproc)"
which prmon
./build/package/tests/mem-burner --help
```

## 3) Generate baseline dataset (normal behavior)

```bash
mkdir -p project/data/normal
cd project

prmon --interval 1 \
  --filename data/normal/baseline_run1.tsv \
  --json-summary data/normal/baseline_run1.json \
  --log-filename data/normal/baseline_run1.log \
  -- ../build/package/tests/mem-burner --malloc 1024 --writef 0.8 --procs 2 --sleep 150
tr '\t' ',' < data/normal/baseline_run1.tsv > data/normal/baseline_run1.csv

prmon --interval 1 \
  --filename data/normal/baseline_run2.tsv \
  --json-summary data/normal/baseline_run2.json \
  --log-filename data/normal/baseline_run2.log \
  -- ../build/package/tests/mem-burner --malloc 1536 --writef 0.85 --procs 2 --sleep 160
tr '\t' ',' < data/normal/baseline_run2.tsv > data/normal/baseline_run2.csv

prmon --interval 1 \
  --filename data/normal/baseline_run3.tsv \
  --json-summary data/normal/baseline_run3.json \
  --log-filename data/normal/baseline_run3.log \
  -- ../build/package/tests/mem-burner --malloc 2048 --writef 0.9 --procs 2 --sleep 170
tr '\t' ',' < data/normal/baseline_run3.tsv > data/normal/baseline_run3.csv
```

## 4) Generate anomaly dataset (injected deviations)

```bash
cd "$(git rev-parse --show-toplevel)/project"
mkdir -p data/anomalies

prmon --interval 1 \
  --filename data/anomalies/anomaly_memory_1.tsv \
  --json-summary data/anomalies/anomaly_memory_1.json \
  --log-filename data/anomalies/anomaly_memory_1.log \
  -- ../build/package/tests/mem-burner --malloc 6144 --writef 1.0 --procs 4 --sleep 160
tr '\t' ',' < data/anomalies/anomaly_memory_1.tsv > data/anomalies/anomaly_memory_1.csv

prmon --interval 1 \
  --filename data/anomalies/anomaly_threads_1.tsv \
  --json-summary data/anomalies/anomaly_threads_1.json \
  --log-filename data/anomalies/anomaly_threads_1.log \
  -- ../build/package/tests/burner --threads 32 --procs 1 --time 170
tr '\t' ',' < data/anomalies/anomaly_threads_1.tsv > data/anomalies/anomaly_threads_1.csv

prmon --interval 1 \
  --filename data/anomalies/anomaly_processes_1.tsv \
  --json-summary data/anomalies/anomaly_processes_1.json \
  --log-filename data/anomalies/anomaly_processes_1.log \
  -- ../build/package/tests/burner --threads 1 --procs 24 --time 170
tr '\t' ',' < data/anomalies/anomaly_processes_1.tsv > data/anomalies/anomaly_processes_1.csv

prmon --interval 1 \
  --filename data/anomalies/anomaly_io_1.tsv \
  --json-summary data/anomalies/anomaly_io_1.json \
  --log-filename data/anomalies/anomaly_io_1.log \
  -- ../build/package/tests/io-burner --time 170
tr '\t' ',' < data/anomalies/anomaly_io_1.tsv > data/anomalies/anomaly_io_1.csv
```

## 5) Familiarization outcomes (what was validated)

- `prmon` binary is available from `$HOME/prmon-install/bin`.
- Burner binaries (`mem-burner`, `burner`, `io-burner`) execute and can be monitored by `prmon`.
- Time-series outputs are produced in `.tsv`, with derived `.csv` plus `.json` summaries and `.log` files.
- Baseline and anomaly scenarios differ by memory size, thread count, process count, and I/O burner usage.
