import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest
from pynput import keyboard
import time

# 1. Chargement et Entraînement de l'IA
df = pd.read_csv("Landry_profile.csv")
model = IsolationForest(contamination=0.1, random_state=42)
model.fit(df[['dwell_time', 'flight_time']])

print("Typestamp active.")

# 2. Variables de capture en temps réel
buffer = []
last_rel = None
press_t = {}

def check_identity(samples):
    # Prédit si les 10 dernières frappes correspondent au profil
    preds = model.predict(samples)
    # -1 = Anomalie, 1 = Normal
    normal_ratio = np.mean(preds == 1)
    
    if normal_ratio < 0.4: # Si moins de 40% des frappes sont "normales"
        print("\nIdentity mismatch - Rythme suspect détecté.")
    else:
        print(f"Confiance : {normal_ratio*100:.0f}%", end="\r")

def on_press(key):
    global last_rel
    t = time.time()
    press_t[key] = t

def on_release(key):
    global last_rel, buffer
    t = time.time()
    if key in press_t:
        dt = t - press_t[key]
        ft = t - last_rel if last_rel else 0
        if 0 < ft < 1.5:
            buffer.append([dt, ft])
            
        if len(buffer) >= 10: # Analyse par blocs de 10 touches
            check_identity(np.array(buffer))
            buffer = [] # Reset du buffer
            
        last_rel = t
        del press_t[key]

with keyboard.Listener(on_press=on_press, on_release=on_release) as listener:
    listener.join()