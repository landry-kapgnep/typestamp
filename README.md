# Typestamp

Biometric authentication engine based on keystroke dynamics.

The idea: the way you type (rhythm, key hold duration, transitions between keys) is a usable biometric signal. Typestamp builds a statistical profile from keystroke n-grams (digraphs, trigrams, 4-grams) and detects anomalies using z-scores.

<img width="972" height="781" alt="image" src="https://github.com/user-attachments/assets/66f608fb-48b9-418f-b678-78cf0e701131" />


## How it works

1. **Training**: the user types a reference phrase multiple times + free text. Typestamp records the timings (total_time, avg_flight) of each n-gram and computes mean/std per sequence.

2. **Authentication**: on a new input each n-gram is compared to the profile via z-score. A weighted multi-level scoring system (4-grams weigh more than 2-grams, since longer sequences are harder to reproduice) produces an acceptation or rejection verdict.

3. **Backoff**: inspired by n-gram language modeling in NLP. If a 4-gram is unknown in the profile, Typestamp falls back to its constituent 3-grams, then 2-grams. Limitation: backoff checks existence but cannot score the sub-sequence timings.

## Structure

- `typestamp_app.py` — Main version (n-grams, z-score, backoff, tkinter GUI)
- `typestamp_gui.py` — Earlier prototype (IsolationForest, real time visualization)
- `collector.py` — Raw keystroke collector (v1)
- `monitor.py` — Standalone IsolationForest monitoring (v1)

## Run

```
pip install pandas numpy scikit-learn matplotlib pynput
python typestamp_app.py
```

## Known limitations

- Backoff is existence based as sub-gram timings are not decomposed from the parent n-gram
- No replay protection
- Profiles are sensitive to hardware (different keyboard = retrain)
- Research prototype not production code yet
