#!/usr/bin/env python3
# run_all_iran.py — Ejecuta el pipeline completo
# Cron: */30 * * * * flock -n /tmp/iran.lock python3 ~/iran-osint-monitor/scripts/run_all_iran.py

import os, sys, subprocess
from datetime import datetime

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPTS = os.path.join(BASE, "scripts")
LOG = os.path.join(BASE, "pipeline_iran.log")

def run(script):
    path = os.path.join(SCRIPTS, script)
    print(f"\n▶ {script}")
    result = subprocess.run([sys.executable, path], capture_output=True, text=True)
    if result.stdout: print(result.stdout)
    if result.stderr: print(f"STDERR: {result.stderr[:200]}")
    return result.returncode

if __name__ == "__main__":
    start = datetime.now()
    print(f"\n{'='*50}")
    print(f"IRAN OSINT PIPELINE — {start.strftime('%Y-%m-%d %H:%M')}")
    print(f"{'='*50}")
    steps = [
        "collect_iran.py",
        "detect_narratives_iran.py",
        "detect_sentiment_iran.py",
        "energy_tracker.py",
    ]
    for s in steps:
        rc = run(s)
        if rc != 0:
            print(f"⚠️  {s} terminó con código {rc}")
    elapsed = (datetime.now() - start).seconds
    msg = f"\n✅ Pipeline completado en {elapsed}s — {datetime.now().strftime('%H:%M')}\n"
    print(msg)
    with open(LOG, "a") as f:
        f.write(msg)
