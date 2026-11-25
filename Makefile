.PHONY: all test sim tables figures check paper realdata hurst results
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
	$(PY) diagnostics/gate_vs_memory.py

check: tables
	$(PY) scripts/check_abstract.py
test:
	$(PY) -m pytest -q tests
sim:
	$(PY) scripts/run_coverage_sim.py --n 5000 --R 500 --B 200
	$(PY) scripts/block_length_sensitivity.py --n 5000 --R 500 --B 200
	$(PY) scripts/hurst_sweep.py --H 0.55 0.6 0.7 0.8 0.9 --n 5000 --R 500 --B 200 --seed 0
	$(PY) diagnostics/gate_vs_memory.py
	$(PY) diagnostics/paired_difference_coverage.py
	$(PY) diagnostics/width_vs_estimand.py
	$(PY) diagnostics/auc_mechanics.py
tables:
	$(PY) scripts/dif_headline.py
	$(PY) scripts/make_tables.py
figures:
	$(PY) scripts/graphical_abstract.py
	$(PY) scripts/manuscript_figures.py
	$(PY) scripts/hurst_figure.py
	$(PY) scripts/pipeline_figure.py
paper: check
	cd paper && tectonic main.tex

# Regenerate the result files that `sim` does not cover: the metric-level intervals on the
# captures, the trace-driven coverage run, the recall-clock sensitivity, the order-arm experiment,
# the n=20000 confirmation and the B=1000 sensitivity. Slow; needs the real-data inputs for the
# first target. Run this and `make sim` to rebuild every committed CSV.
results:
	$(PY) scripts/metric_level_intervals.py
	$(PY) scripts/trace_coverage.py
	$(PY) scripts/recall_clock.py
	$(PY) scripts/split_order_arms.py
	$(PY) scripts/confirm_n20000.py
	$(PY) scripts/sensitivity_B1000.py
	$(PY) diagnostics/estimand_conflation.py
	$(PY) diagnostics/episode_curve.py
	$(PY) diagnostics/seed_vs_testset.py
	$(PY) scripts/make_tables.py
	$(PY) scripts/check_abstract.py
