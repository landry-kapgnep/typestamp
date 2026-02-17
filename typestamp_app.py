import tkinter as tk
from tkinter import ttk, messagebox
import time
import csv
import os
import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
import matplotlib.pyplot as plt

# --- CONFIGURATION STYLE ---
plt.style.use('dark_background')
BG_COLOR = "#cfcaff"
FG_COLOR = "#000000"
ACCENT_COLOR = "#47417c"
ALERT_COLOR = "#ff3333"
SUCCESS_COLOR = "#00cc00"
PROFILE_FILE = "Landry_profile.csv"
FONT = "System"

# --- PARAMETRES DE SECURITE ---
HUMAN_LIMIT_FAST = 0.020  # 20ms : Limite physiologique humaine
HUMAN_LIMIT_SLOW = 2.0    # 2s : Limite de l'attention

class KeyPulseApp:
    def __init__(self, root):
        self.root = root
        self.root.title("KeyPulse // Biometric Security Suite")
        self.root.geometry("900x700")
        self.root.configure(bg=BG_COLOR)

        # Style des onglets
        style = ttk.Style()
        style.theme_use('clam')
        style.configure("TNotebook", background=BG_COLOR, borderwidth=0)
        style.configure("TNotebook.Tab", background="#333", foreground="white", padding=[10, 5])
        style.map("TNotebook.Tab", background=[("selected", ACCENT_COLOR)], foreground=[("selected", "black")])

        # Création des onglets
        self.notebook = ttk.Notebook(root)
        self.notebook.pack(fill='both', expand=True)

        # Onglet 1 : Entraînement
        self.tab_train = tk.Frame(self.notebook, bg=BG_COLOR)
        self.notebook.add(self.tab_train, text="  1. Enregistrement  ")
        self.setup_training_tab()

        # Onglet 2 : Surveillance
        self.tab_monitor = tk.Frame(self.notebook, bg=BG_COLOR)
        self.notebook.add(self.tab_monitor, text="  2. Surveillance  ")
        self.setup_monitoring_tab()
        
        # Événement : Quand on change d'onglet
        self.notebook.bind("<<NotebookTabChanged>>", self.on_tab_change)

        # Variables globales de capture
        self.active_keys = {}
        self.last_release_time = time.time()

    # ============================================================
    # ONGLET 1 : ENREGISTREMENT (COLLECTOR)
    # ============================================================
    def setup_training_tab(self):
        lbl_title = tk.Label(self.tab_train, text="Création d'empreinte", font=(FONT, 20), bg=BG_COLOR, fg=FG_COLOR)
        lbl_title.pack(pady=20)

        self.target_phrase = "La sécurité est biométrique"
        lbl_instr = tk.Label(self.tab_train, text=f"Tapez 15 fois la phrase exacte :\n'{self.target_phrase}'\npuis appuyez sur ENTRÉE à chaque fois.", 
                             font=(FONT, 14), bg=BG_COLOR, fg=FG_COLOR)
        lbl_instr.pack(pady=10)

        self.entry_train = tk.Entry(self.tab_train, font=(FONT, 18), bg="#333", fg="white", insertbackground="white")
        self.entry_train.pack(fill=tk.X, padx=50, pady=10)
        self.entry_train.bind('<KeyPress>', self.on_key_press_train)
        self.entry_train.bind('<KeyRelease>', self.on_key_release_train)
        self.entry_train.bind('<Return>', self.save_sentence)
        # On empêche le copier-coller pendant l'entraînement aussi
        self.entry_train.bind('<Control-v>', lambda e: "break")

        self.train_counter = 0
        self.lbl_progress = tk.Label(self.tab_train, text="Progression : 0 / 15", font=(FONT, 12), bg=BG_COLOR, fg=FG_COLOR)
        self.lbl_progress.pack(pady=10)
        
        self.train_data = [] 
        self.current_sentence_data = [] 

    def on_key_press_train(self, event):
        if event.keysym in ["Return", "BackSpace"]: return
        t = time.time()
        self.active_keys[event.keysym] = t
        self.active_keys[event.keysym + "_ft"] = t - self.last_release_time

    def on_key_release_train(self, event):
        if event.keysym in ["Return", "BackSpace"]: return
        t = time.time()
        press_t = self.active_keys.pop(event.keysym, None)
        flight_t = self.active_keys.pop(event.keysym + "_ft", None)
        self.last_release_time = t

        if press_t:
            dwell = t - press_t
            if HUMAN_LIMIT_FAST < dwell < 1.0 and 0 < flight_t < 2.0:
                self.current_sentence_data.append({'dwell': dwell, 'flight': flight_t})

    def save_sentence(self, event):
        content = self.entry_train.get().strip()
        if content != self.target_phrase:
            messagebox.showwarning("Erreur", f"La phrase doit être exactement :\n{self.target_phrase}")
            self.entry_train.delete(0, tk.END)
            self.current_sentence_data = []
            return

        self.train_data.extend(self.current_sentence_data)
        self.train_counter += 1
        self.lbl_progress.config(text=f"Progression : {self.train_counter} / 15")
        
        self.entry_train.delete(0, tk.END)
        self.current_sentence_data = []

        if self.train_counter >= 15:
            self.save_to_csv()

    def save_to_csv(self):
        try:
            with open(PROFILE_FILE, 'w', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=['dwell_time', 'flight_time'])
                writer.writeheader()
                for item in self.train_data:
                    writer.writerow({'dwell_time': item['dwell'], 'flight_time': item['flight']})
            
            messagebox.showinfo("Succès", "Profil sauvegardé ! Passez à l'onglet 'Surveillance'.")
            self.train_counter = 0
            self.lbl_progress.config(text="TERMINE - Profil prêt")
            self.train_data = []
        except Exception as e:
            messagebox.showerror("Erreur", f"Impossible de sauvegarder : {e}")

    # ============================================================
    # ONGLET 2 : SURVEILLANCE (MONITOR)
    # ============================================================
    def setup_monitoring_tab(self):
        self.lbl_status = tk.Label(self.tab_monitor, text="EN ATTENTE DU PROFIL...", font=(FONT, 16, "bold"), bg=BG_COLOR, fg=FG_COLOR)
        self.lbl_status.pack(pady=10)

        self.fig = Figure(figsize=(6, 3.5), dpi=100)
        self.ax = self.fig.add_subplot(111)
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.tab_monitor)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True, padx=20)
        self.setup_plot()

        lbl_test = tk.Label(self.tab_monitor, text="Zone de Test (Tapez librement) :", bg=BG_COLOR, fg=FG_COLOR)
        lbl_test.pack(pady=5)
        self.entry_monitor = tk.Entry(self.tab_monitor, font=(FONT, 16), bg="#222", fg="white", insertbackground="white")
        self.entry_monitor.pack(fill=tk.X, padx=20, pady=(0, 20))
        
        self.entry_monitor.bind('<KeyPress>', self.on_key_press_monitor)
        self.entry_monitor.bind('<KeyRelease>', self.on_key_release_monitor)
        
        # --- PROTECTION ANTI-TRICHE (PASTE) ---
        # Intercepte Ctrl+V et le clic droit coller
        self.entry_monitor.bind('<<Paste>>', self.trigger_impossible_speed)
        self.entry_monitor.bind('<Control-v>', self.trigger_impossible_speed)

        self.model = None
        self.history_normal = []
        self.history_anomaly = []
        self.history_cheat = [] # Pour stocker les "Paste" ou "Bot"

    def setup_plot(self):
        self.ax.clear()
        self.ax.set_facecolor(BG_COLOR)
        self.fig.patch.set_facecolor(BG_COLOR)
        self.ax.set_title("Biométrie en temps réel", color=FG_COLOR)
        self.ax.tick_params(colors=FG_COLOR)
        self.ax.grid(True, linestyle='--', alpha=0.2)
        self.ax.set_xlabel("Dwell Time (s)", color=FG_COLOR)
        self.ax.set_ylabel("Flight Time (s)", color=FG_COLOR)
        self.ax.set_xlim(0, 0.25)
        self.ax.set_ylim(0, 0.5)

    def load_model(self):
        if not os.path.exists(PROFILE_FILE):
            self.lbl_status.config(text="Aucun profil trouvé.", fg=ALERT_COLOR)
            return

        try:
            df = pd.read_csv(PROFILE_FILE)
            if len(df) < 20: # Réduit un peu l'exigence pour tester
                self.lbl_status.config(text="Données insuffisantes.", fg=ALERT_COLOR)
                return

            self.model = IsolationForest(contamination=0.1, random_state=42)
            self.model.fit(df[['dwell_time', 'flight_time']].values)
            self.lbl_status.config(text="Système prêt.", fg=FG_COLOR)
            self.entry_monitor.delete(0, tk.END)
        except Exception as e:
            print(f"Erreur chargement IA: {e}")

    def on_tab_change(self, event):
        if self.notebook.index("current") == 1:
            self.load_model()
            self.entry_monitor.focus_set()

    # --- Logique Monitor ---
    def trigger_impossible_speed(self, event):
        """Déclenché quand on détecte un Paste ou Ctrl+V"""
        self.lbl_status.config(text="COPIE-COLLE !", fg=ALERT_COLOR)
        # On ajoute des points fictifs "anormaux" (tout en bas à gauche) pour le visuel
        for _ in range(5):
            self.history_cheat.append([0.001, 0.001])
        self.update_graph()
        return "break" # Empêche le coller de se faire réellement

    def on_key_press_monitor(self, event):
        # Ignore les touches de modification seules
        if event.keysym in ["Control_L", "Control_R", "Shift_L", "Shift_R", "Alt_L", "Alt_R"]: return
        
        t = time.time()
        self.active_keys[event.keysym] = t
        self.active_keys[event.keysym + "_ft"] = t - self.last_release_time

    def on_key_release_monitor(self, event):
        if event.keysym in ["Control_L", "Control_R", "Shift_L", "Shift_R", "Alt_L", "Alt_R"]: return
        
        t = time.time()
        press_t = self.active_keys.pop(event.keysym, None)
        flight_t = self.active_keys.pop(event.keysym + "_ft", None)
        self.last_release_time = t

        if self.model and press_t:
            dwell = t - press_t
            
            # --- FILTRE 1 : LE RADAR DE VITESSE (Hard Rules) ---
            # Si le temps est trop court (bot/macro) ou le vol quasi nul
            if dwell < HUMAN_LIMIT_FAST or (flight_t < HUMAN_LIMIT_FAST and flight_t > 0):
                self.handle_cheat_detection(dwell, flight_t)
            # --- FILTRE 2 : COHERENCE ---
            elif dwell < 2.0 and flight_t < 2.0:
                self.check_biometrics(dwell, flight_t)

    def handle_cheat_detection(self, dwell, flight):
        self.history_cheat.append([dwell, flight])
        self.lbl_status.config(text="VITESSE SUSPECTE", fg=ALERT_COLOR)
        self.update_limits_and_draw()

    def check_biometrics(self, dwell, flight):
        # Prédiction IA
        pred = self.model.predict([[dwell, flight]])[0]
        
        if pred == 1:
            self.history_normal.append([dwell, flight])
            self.lbl_status.config(text="Identité confirmée.", fg=SUCCESS_COLOR)
        else:
            self.history_anomaly.append([dwell, flight])
            self.lbl_status.config(text="Rythme Inhabituel", fg="orange")

        self.update_limits_and_draw()

    def update_limits_and_draw(self):
        # Gestion de la taille des listes (Buffer glissant)
        max_points = 40
        if len(self.history_normal) > max_points: self.history_normal.pop(0)
        if len(self.history_anomaly) > max_points: self.history_anomaly.pop(0)
        if len(self.history_cheat) > max_points: self.history_cheat.pop(0)
        
        self.update_graph()

    def update_graph(self):
        self.setup_plot()
        
        norm = np.array(self.history_normal)
        anom = np.array(self.history_anomaly)
        cheat = np.array(self.history_cheat)

        # 1. Points normaux (Vert/Accent)
        if len(norm) > 0:
            self.ax.scatter(norm[:, 0], norm[:, 1], c=ACCENT_COLOR, s=50, alpha=0.8, label="Normal")
        
        # 2. Anomalies de rythme (Orange/Rouge léger)
        if len(anom) > 0:
            self.ax.scatter(anom[:, 0], anom[:, 1], c="orange", marker='x', s=80, label="Rythme Suspect")

        # 3. Triche / Vitesse impossible (Rouge vif)
        if len(cheat) > 0:
            self.ax.scatter(cheat[:, 0], cheat[:, 1], c="red", marker='D', s=100, label="Bot/Paste")
            
        self.ax.legend(loc="upper right", fontsize="small")
        self.canvas.draw()

if __name__ == "__main__":
    root = tk.Tk()
    app = KeyPulseApp(root)
    root.mainloop()