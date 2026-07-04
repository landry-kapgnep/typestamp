# Typestamp

Continuous biometric authentication engine based on keystroke dynamics.

Typestamp builds a behavioral profile from how you type — not what you type — and detects identity mismatches in real time by analyzing the temporal micro-patterns of your keystrokes.

## How it works

### Keystroke features

Every key press/release pair produces two raw signals:

- **Dwell time**: how long a key is held down.
- **Flight time**: the gap between releasing one key and pressing the next.

These timings form a behavioral signature that is consistent within an individual but varies between users, even when typing the same text.

### N-gram latency profiling

Rather than treating each keystroke independently, Typestamp extracts **n-grams** (sequences of 2, 3, and 4 consecutive keys) and measures their aggregate timing:

- **total_time**: press of the first key → release of the last key.
- **avg_flight**: mean flight time between consecutive keys in the window.

A user profile is built by computing the mean and standard deviation of these features for each observed n-gram across multiple training sessions. A minimum sample threshold (`MIN_NGRAM_SAMPLES = 3`) filters out n-grams with insufficient data.

### Authentication scoring

When a user attempts to authenticate, Typestamp:

1. Extracts all n-grams from the input.
2. Computes a **z-score** per n-gram against the stored profile (both total_time and avg_flight).
3. Classifies each n-gram as normal (`z < 2.0`) or anomalous.
4. Applies **weighted multi-level scoring**: higher-order n-grams carry more weight (2-gram → ×1.0, 3-gram → ×1.5, 4-gram → ×2.0), since longer sequences are harder to mimic.
5. Applies a **backoff mechanism** inspired by n-gram language modeling: if a 4-gram is unknown, Typestamp falls back to its constituent 3-grams, then 2-grams, to maximize coverage.
6. Returns an accept/reject decision based on a strictness threshold (default: 70% of known n-grams must be normal) and a minimum coverage check (default: 50% of input n-grams must be known).

### Dual profile system

- **Phrase profile**: trained on repeated input of a fixed passphrase. High precision for challenge-response authentication.
- **General profile**: trained on free-text typing. Broader coverage of n-gram patterns for continuous monitoring.

During authentication, profiles are merged (general as base, phrase-specific overrides), combining the breadth of free-text data with the precision of passphrase repetition.

## Project structure

```
typestamp/
├── typestamp_app.py    # Main application — n-gram engine, scoring, GUI (v3)
├── typestamp_gui.py    # Earlier prototype — IsolationForest approach with real-time viz (v2)
├── collector.py        # Raw keystroke data collector (v1)
├── monitor.py          # Standalone monitoring script using IsolationForest (v1)
└── README.md
```

**v1** (`collector.py`, `monitor.py`): initial prototype using sklearn's IsolationForest on raw (dwell, flight) pairs. Functional but treats keystrokes independently, losing sequential information.

**v2** (`typestamp_gui.py`): GUI wrapper around the IsolationForest approach with a real-time matplotlib scatter plot.

**v3** (`typestamp_app.py`): complete redesign. Replaced the black-box ML model with an interpretable n-gram statistical engine. Added multi-level scoring, backoff, dual profiles, and coverage checks.

## Usage

### Requirements

```
pip install pandas numpy scikit-learn matplotlib pynput
```

### Training a profile

```bash
python typestamp_app.py
```

1. Create or load a profile in the top bar.
2. **Phrase tab**: type the reference phrase at least 5 times to build the phrase profile.
3. **Free text tab**: type naturally to build the general profile. Longer sessions produce better coverage.

### Authenticating

3. **Monitor tab**: type the passphrase. Typestamp scores the attempt against the trained profile and displays the verdict with per-level breakdown and a scatter plot of the attempt vs. the stored profile.

## Key parameters

| Parameter | Default | Role |
|---|---|---|
| `Z_THRESHOLD` | 2.0 | Z-score above which an n-gram is flagged as anomalous |
| `STRICTNESS_THRESHOLD` | 0.70 | Minimum ratio of normal n-grams to accept |
| `MIN_COVERAGE` | 0.50 | Minimum ratio of known n-grams in the attempt |
| `MIN_NGRAM_SAMPLES` | 3 | Minimum observations to include an n-gram in the profile |
| `MIN_STD` | 0.015 | Standard deviation floor to prevent division by zero |
| `MAX_N` | 4 | Maximum n-gram size (2, 3, 4) |
| `NGRAM_WEIGHTS` | {2: 1.0, 3: 1.5, 4: 2.0} | Scoring weights per n-gram level |

## Known limitations

- **Backoff is existence-based**: when falling back to sub-grams, Typestamp checks whether they exist in the profile but cannot score their timing (the sub-timings are not decomposed from the parent n-gram). This makes backoff a coverage booster rather than a true scoring mechanism.
- **No replay protection**: the system does not guard against recorded keystroke replay attacks.
- **Environment-sensitive**: typing patterns vary with keyboard hardware, fatigue, and posture. Profiles are not portable across devices without retraining.
- **No persistence optimization**: profiles are rebuilt from raw CSV on every load. Adequate for prototype scale but would need indexing for production use.

## Built with

Python · Pandas · NumPy · scikit-learn · Matplotlib · Tkinter
