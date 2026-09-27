.PHONY: all test sim tables figures check paper realdata hurst week1 week2 week3 week4
all: test tables figures check paper

# The interpreter used for every rule. The default works for anyone who has installed the
# environment (env/environment.yml or requirements.txt) and is running inside it. Override it
# for a Python that is not on PATH, e.g.:
#     make all PY=/path/to/venv/bin/python
PY ?= python3

# Regenerate every committed real-data CSV from raw (P100). Raw is not redistributed:
# run `python3 scripts/fetch_raw.py --url <mirror> --out data/raw` first, then `make realdata`.
# AAL uses the authors' own features file (present); CICIDS/packet need data/raw fetched.
RAW ?= data/raw
CIC_WED ?= $(RAW)/Wednesday-workingHours.pcap_ISCX.csv
realdata:
	$(PY) scripts/aal_dif.py                              # AAL window (features present)
	$(PY) scripts/cicids_dif.py "$(CIC_WED)"             # CICIDS flow + differential
	$(PY) scripts/flow_dif_producer.py "$(RAW)"          # cicids_flow_dif.csv (b/a per day)
	$(PY) scripts/time_order_audit.py "$(CIC_WED)"       # time_order_audit.csv
	$(PY) scripts/pcap_window_dif.py "$(RAW)/win_early.pcapng" early --csv results/packet_windows.csv
	$(PY) scripts/pcap_window_dif.py "$(RAW)/win_mid.pcapng"   mid   --csv results/packet_windows.csv
	$(PY) scripts/pcap_window_dif.py "$(RAW)/win_late.pcapng"  late  --csv results/packet_windows.csv
# The long-memory boundary (Table 12). Same seed/n/R/B as the reported lrd_H0.8 cell, so its
# H=0.8 arm must reproduce it; `make check` fails if it does not.
hurst:
	$(PY) scripts/hurst_sweep.py --H 0.55 0.6 0.7 0.8 0.9 --n 5000 --R 500 --B 200 --seed 0
	$(PY) diagnostics/p127_gate_vs_memory.py

check: tables
	$(PY) scripts/check_abstract.py
test:
	$(PY) -m pytest -q tests
sim:
	$(PY) scripts/run_coverage_sim.py --n 5000 --R 500 --B 200
	$(PY) scripts/block_length_sensitivity.py --n 5000 --R 500 --B 200
	$(PY) scripts/hurst_sweep.py --H 0.55 0.6 0.7 0.8 0.9 --n 5000 --R 500 --B 200 --seed 0
	$(PY) diagnostics/p127_gate_vs_memory.py
	$(PY) diagnostics/p121_width_vs_estimand.py
	$(PY) diagnostics/p122_auc_mechanics.py
tables:
	$(PY) scripts/dif_headline.py
	$(PY) scripts/make_tables.py
figures:
	$(PY) scripts/graphical_abstract.py
	$(PY) scripts/week4_figures.py
	$(PY) scripts/hurst_figure.py
paper: check
	cd paper && tectonic main.tex

# Week 1 of the Q1 program: metric-level intervals and paired comparisons.
week1:
	$(PY) scripts/week1_metric_level.py

# Week 2 of the Q1 program: trace-driven coverage on Monday benign series.
week2:
	$(PY) scripts/week2_trace_coverage.py

# Week 3 of the Q1 program: recall-clock sensitivity, then the manuscript macros.
week3:
	$(PY) scripts/week3_recall_clock.py
	$(PY) scripts/make_tables.py
	$(PY) scripts/check_abstract.py

# Week 4 of the Q1 program: figures, manuscript macros, abstract check.
week4:
	$(PY) scripts/week4_figures.py
	$(PY) scripts/hurst_figure.py
	$(PY) scripts/make_tables.py
	$(PY) scripts/check_abstract.py
