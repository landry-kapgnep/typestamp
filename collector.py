import time
import csv
from pynput import keyboard

# Configuration
USERNAME = "Landry"
output_file = f"{USERNAME}_profile.csv"

data = []
last_release_time = None
press_times = {}

print(f"--- Entraînement de ypeStamp for {USERNAME} ---")
print("Tapez une phrase plusieurs fois (Appuyez sur 'Echap' pour terminer)")

def on_press(key):
    global last_release_time
    t = time.time()
    press_times[key] = t
    
    # Calcul du Flight Time (depuis le dernier relâchement)
    if last_release_time is not None:
        flight_time = t - last_release_time
        # On ne stocke que si c'est un enchaînement rapide (< 2s)
        if flight_time < 2.0:
            data[-1]['flight_time'] = flight_time

def on_release(key):
    global last_release_time
    t = time.time()
    if key in press_times:
        dwell_time = t - press_times[key]
        data.append({'key': str(key), 'dwell_time': dwell_time, 'flight_time': 0.0})
        last_release_time = t
        del press_times[key]

    if key == keyboard.Key.esc:
        return False

with keyboard.Listener(on_press=on_press, on_release=on_release) as listener:
    listener.join()

# Sauvegarde des données (en ignorant les entrées incomplètes)
with open(output_file, 'w', newline='') as f:
    writer = csv.DictWriter(f, fieldnames=['dwell_time', 'flight_time'])
    writer.writeheader()
    for entry in data:
        if entry['flight_time'] > 0:
            writer.writerow({'dwell_time': entry['dwell_time'], 'flight_time': entry['flight_time']})

print(f"Empreinte sauvegardée dans {output_file} !")