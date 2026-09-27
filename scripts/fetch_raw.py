"""Fetch + verify the raw datasets the real-data producers need (P100). The raw data is NOT
redistributed with this artifact; this script downloads it from public mirrors and records a
SHA-256 manifest so a later run can verify byte-identity.

Datasets:
  - CICIDS2017 GeneratedLabelledFlows (flow grain): Hugging Face mirror `bencorn/CICIDS2017`
    (acquisition documented in docs/acquisition_p28.md; the zip was ~283,876,488 bytes).
  - CICIDS2017 daily pcaps (packet grain): same mirror.
The AAL MQTT-bridge telemetry is the authors' own (baseline_data/interleaved/*.csv, features in
../bridgeguard_features/); it is not fetched here.

Usage:
  python3 scripts/fetch_raw.py --url <base_url> --out data/raw   # download, then write manifest
  python3 scripts/fetch_raw.py --verify data/raw                 # re-hash and check against manifest
The manifest (data/MANIFEST.sha256) is written on download and checked on --verify; hashes are
recorded from the bytes actually fetched -- none is hand-entered.
"""
import sys, os, argparse, hashlib

MANIFEST = "data/MANIFEST.sha256"
# expected files the producers consume (names are matched by substring by the producers)
EXPECTED = ["Monday-WorkingHours.pcap_ISCX.csv", "Tuesday-WorkingHours.pcap_ISCX.csv",
            "Wednesday-workingHours.pcap_ISCX.csv"]


def sha256(path, buf=1 << 20):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(buf), b""):
            h.update(chunk)
    return h.hexdigest()


def write_manifest(out_dir):
    os.makedirs(os.path.dirname(MANIFEST) or ".", exist_ok=True)
    lines = []
    for name in sorted(os.listdir(out_dir)):
        p = os.path.join(out_dir, name)
        if os.path.isfile(p):
            lines.append(f"{sha256(p)}  {name}  {os.path.getsize(p)}")
    open(MANIFEST, "w").write("\n".join(lines) + "\n")
    print(f"wrote {MANIFEST} ({len(lines)} files)")


def verify(out_dir):
    if not os.path.exists(MANIFEST):
        print("no manifest; run a download first", file=sys.stderr); sys.exit(2)
    want = {}
    for ln in open(MANIFEST):
        if ln.strip():
            h, name, *_ = ln.split()
            want[name] = h
    bad = 0
    for name, h in want.items():
        p = os.path.join(out_dir, name)
        if not os.path.exists(p):
            print(f"MISSING {name}"); bad += 1; continue
        got = sha256(p)
        ok = got == h
        print(f"{'OK  ' if ok else 'FAIL'} {name}")
        bad += not ok
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--url", help="base URL of the mirror to download EXPECTED files from")
    ap.add_argument("--out", default="data/raw")
    ap.add_argument("--verify", metavar="DIR", help="verify a directory against the manifest")
    a = ap.parse_args()
    if a.verify:
        verify(a.verify)
    elif a.url:
        import urllib.request
        os.makedirs(a.out, exist_ok=True)
        for name in EXPECTED:
            dest = os.path.join(a.out, name)
            print(f"downloading {name} ...")
            urllib.request.urlretrieve(a.url.rstrip("/") + "/" + name, dest)
        write_manifest(a.out)
    else:
        ap.error("give --url to download or --verify DIR to check")
