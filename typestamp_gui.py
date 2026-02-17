import tkinter as tk
from tkinter import ttk
import time
import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
import matplotlib.pyplot as plt

# --- CONFIGURATION DU STYLE ---
plt.style.use('dark_background') # Pour le look Cyber
BG_COLOR = "#1e1e1e"
TEXT_COLOR = "#00ff00"
ALERT_COLOR = "#ff0000"

class TypestampGUI:
    def __init__(self, root, profile_csv):
        self.root = root
        self.root.title("Typestamp - Typing Monitor")
        self.root.geometry("800x600")
        self.root.configure(bg=BG_COLOR)

        # --- 1. CHARGEMENT ET ENTRAÎNEMENT DU MODÈLE ---
        try:
            print("Chargement du profil...")
            df = pd.read_csv(profile_csv)
            # On entraîne le modèle au démarrage
            self.model = IsolationForest(n_estimators=100, contamination=0.05, random_state=42)
            self.model.fit(df[['dwell_time', 'flight_time']].values)
            print("Modèle Typestamp prêt.")
            initial_status = "SYSTEM READY // AWAITING INPUT"
            status_color = TEXT_COLOR
        except FileNotFoundError:
             initial_status = "ERREUR : Fichier profil introuvable !"
             status_color = ALERT_COLOR
             self.model = None

        # --- 2. VARIABLES DE SUIVI ---
        self.active_keys = {}
        self.last_release_time = time.time()
        # Buffers pour le graphique (on garde les 50 derniers points)
        self.history_normal = [] # Liste de [x, y]
        self.history_anomaly = [] # Liste de [x, y]
        self.counter = 0

        # --- 3. INTERFACE GRAPHIQUE ---
        
        # A. Zone de statut (Haut)
        self.status_label = tk.Label(root, text=initial_status, font=("Consolas", 14, "bold"), bg=BG_COLOR, fg=status_color)
        self.status_label.pack(pady=10)

        # B. Zone du Graphique (Milieu)
        self.fig = Figure(figsize=(6, 4), dpi=100)
        self.ax = self.fig.add_subplot(111)
        self.setup_plot_axes()
        
        self.canvas = FigureCanvasTkAgg(self.fig, master=root)
        self.canvas.draw()
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True, padx=20, pady=10)

        # C. Zone de saisie (Bas)
        label_input = tk.Label(root, text="Zone de test (Tapez ici) :", bg=BG_COLOR, fg="white")
        label_input.pack()
        
        self.entry_box = tk.Entry(root, font=("Helvetica", 16), bg="#333333", fg="white", insertbackground="white")
        self.entry_box.pack(fill=tk.X, padx=20, pady=(0, 20), ipady=5)
        # On lie les événements clavier à la boîte de saisie
        self.entry_box.bind('<KeyPress>', self.on_key_press)
        self.entry_box.bind('<KeyRelease>', self.on_key_release)
        self.entry_box.focus_set()

    def setup_plot_axes(self):
        """Initialise le look du graphique"""
        self.ax.clear()
        self.ax.set_title("Keystroke Dynamics (Temps réel)", color="white")
        self.ax.set_xlabel("Dwell Time (Temps d'appui)", color="white")
        self.ax.set_ylabel("Flight Time (Temps de vol)", color="white")
        self.ax.grid(True, linestyle='--', alpha=0.3)
        # Fixer les limites pour éviter que le graphique ne saute trop
        self.ax.set_xlim(0, 0.3) # Dwell time typique entre 50ms et 200ms
        self.ax.set_ylim(0, 0.5) # Flight time typique

    def process_keystroke(self, dwell, flight):
        """Analyse une frappe et met à jour l'interface"""
        if self.model is None: return
        
        self.counter += 1
        # Prédiction : 1 = Normal, -1 = Anomalie
        features = np.array([[dwell, flight]])
        prediction = self.model.predict(features)[0]
        
        # Mise à jour des données du graphique
        if prediction == 1:
            self.history_normal.append([dwell, flight])
            self.status_label.config(text="IDENTITY CONFIRMED // Rythme OK", fg=TEXT_COLOR)
        else:
            self.history_anomaly.append([dwell, flight])
            self.status_label.config(text="*** IDENTITY MISMATCH DETECTED ***", fg=ALERT_COLOR)
            
        # Nettoyage des vieux points (garder les 50 derniers)
        if len(self.history_normal) > 50: self.history_normal.pop(0)
        if len(self.history_anomaly) > 50: self.history_anomaly.pop(0)

        self.update_plot()

    def update_plot(self):
        """Redessine le graphique avec les nouveaux points"""
        self.setup_plot_axes()
        
        # Convertir en numpy pour faciliter le slicing
        norm_data = np.array(self.history_normal)
        anom_data = np.array(self.history_anomaly)

        # Plot des points normaux (Bleu néon)
        if len(norm_data) > 0:
            self.ax.scatter(norm_data[:, 0], norm_data[:, 1], color='#00ccff', s=40, alpha=0.7, label='Profil Utilisateur')
        
        # Plot des anomalies (Rouge vif)
        if len(anom_data) > 0:
            self.ax.scatter(anom_data[:, 0], anom_data[:, 1], color='#ff3300', s=80, marker='X', label='Intrus/Anomalie')
            
        self.ax.legend()
        self.canvas.draw()

    # --- GESTIONNAIRES D'ÉVÉNEMENTS CLAVIER ---
    def on_key_press(self, event):
        # Ignore les touches spéciales maintenues (comme Shift)
        if event.keysym in self.active_keys: return
        
        t = time.time()
        self.active_keys[event.keysym] = t
        
        # Calcul du Flight Time (le temps depuis le dernier relâchement d'UNE AUTRE touche)
        flight_time = t - self.last_release_time
        # On stocke temporairement le FT associé à cette touche
        self.active_keys[event.keysym + "_ft"] = flight_time

    def on_key_release(self, event):
        t = time.time()
        press_t = self.active_keys.pop(event.keysym, None)
        flight_t = self.active_keys.pop(event.keysym + "_ft", None)
        
        if press_t and flight_t:
            dwell_time = t - press_t
            
            # Filtrage basique pour éviter les valeurs aberrantes
            if 0.01 < dwell_time < 1.0 and 0.0 < flight_t < 2.0:
                 self.process_keystroke(dwell_time, flight_t)

        self.last_release_time = t

if __name__ == "__main__":
    # REMPLACE PAR LE NOM DE TON FICHIER CSV GÉNÉRÉ À L'ÉTAPE 1
    CSV_FILE = "Landry_profile.csv" 
    
    root = tk.Tk()
    app = TypestampGUI(root, CSV_FILE)
    root.mainloop()