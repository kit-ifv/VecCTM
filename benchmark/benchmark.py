import time
import json
import subprocess
from resources import Settings
import sys

# To simulate different networks, the variable SIM_FILE in Settings.py must be changed, and the input file in the scripts must be adjusted.

# Number of warmup runs and measured runs for benchmarking
m = 3  # number of warmup runs
n = 10  # number of measured runs

# Liste mit Skriptnamen, die ausgeführt werden sollen
scripts = [
    "..\\traffic\\vector_full.py",
    "..\\traffic\\vector_sparse.py",
    "..\\traffic\\network_par.py",
    "..\\traffic\\network_seq.py"
]


# Ergebnis-Dictionary initialisieren
results = {}


# Schleife für jedes Skript
for script in scripts:
    # Ergebnis-Liste für das Skript initialisieren
    script_results_warmup = {}
    script_results = {}
    results[script] = {}

    # Schleife für jede Wiederholung
    for i in range(m):
        # Skript ausführen und Zeit messen
        print(f"Warm-up run {i} for script {script}")
        start_time = time.time()
        subprocess.run([sys.executable, script])
        end_time = time.time()
        elapsed_time = end_time - start_time
        # Ergebnis zur Liste hinzufügen
        script_results_warmup[i] = elapsed_time
    # Ergebnis-Liste in das Ergebnis-Dictionary schreiben

    results[script]['warmup'] = script_results_warmup
    for i in range(n):
        # Skript ausführen und Zeit messen
        print(f"Benchmark run {i} for script {script}")
        start_time = time.time()
        subprocess.run([sys.executable, script])
        end_time = time.time()
        elapsed_time = end_time - start_time
        # Ergebnis zur Liste hinzufügen
        script_results[i] = elapsed_time
    # Ergebnis-Liste in das Ergebnis-Dictionary schreiben

    results[script]['benchmark'] = script_results

# Ergebnis-Dictionary in eine JSON-Datei schreiben
with open(f"{Settings.SIM_FILE}-bench.json", "w") as f:
    json.dump(results, f)
