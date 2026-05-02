"""Interface CustomTkinter — fenêtre desktop native."""

import customtkinter as ctk
import threading
import os
from tkinter import messagebox

from lyrics_generator import generer_paroles, affiner_paroles
from music_generator import generer_musique
from recorder import Enregistreur
from post_prod import post_production_vocale, mixer_final
from config import DEFAULT_LANGUAGE, DEFAULT_REVERB

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

state = {
    "instrumental_path": None,
    "vocal_path": None,
    "vocal_prod_path": None,
    "mix_path": None,
}
enregistreur = Enregistreur()


class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("🎵 AI Music Studio")
        self.geometry("900x700")
        self.resizable(True, True)
        self._construire_ui()

    def _construire_ui(self):
        self.tabs = ctk.CTkTabview(self, anchor="nw")
        self.tabs.pack(fill="both", expand=True, padx=15, pady=15)

        for nom in ["1. Paroles", "2. Musique", "3. Enregistrement", "4. Post-prod", "5. Export"]:
            self.tabs.add(nom)

        self._onglet_paroles()
        self._onglet_musique()
        self._onglet_enregistrement()
        self._onglet_postprod()
        self._onglet_export()

    # ------------------------------------------------------------------ #
    # Onglet 1 — Paroles
    # ------------------------------------------------------------------ #
    def _onglet_paroles(self):
        tab = self.tabs.tab("1. Paroles")

        # Ligne style / thème / langue
        row = ctk.CTkFrame(tab, fg_color="transparent")
        row.pack(fill="x", pady=(10, 5))

        ctk.CTkLabel(row, text="Style musical").grid(row=0, column=0, padx=(0, 5), sticky="w")
        self.style_var = ctk.CTkEntry(row, placeholder_text="rap, pop, rock...")
        self.style_var.grid(row=1, column=0, padx=(0, 10), sticky="ew")

        ctk.CTkLabel(row, text="Thème / Ambiance").grid(row=0, column=1, padx=(0, 5), sticky="w")
        self.theme_var = ctk.CTkEntry(row, placeholder_text="nuit, mélancolie, urban...")
        self.theme_var.grid(row=1, column=1, padx=(0, 10), sticky="ew")

        ctk.CTkLabel(row, text="Langue").grid(row=0, column=2, sticky="w")
        self.langue_var = ctk.CTkOptionMenu(row, values=["fr", "en"], width=80)
        self.langue_var.set(DEFAULT_LANGUAGE)
        self.langue_var.grid(row=1, column=2)

        row.columnconfigure(0, weight=2)
        row.columnconfigure(1, weight=2)

        ctk.CTkButton(
            tab, text="✨ Générer les paroles", command=self._generer_paroles
        ).pack(pady=5)

        # Zone de texte paroles
        self.paroles_text = ctk.CTkTextbox(tab, height=280)
        self.paroles_text.pack(fill="both", expand=True, pady=5)

        # Affinage
        ctk.CTkLabel(tab, text="✏️ Affiner avec l'IA", anchor="w").pack(fill="x", pady=(8, 0))
        affiner_row = ctk.CTkFrame(tab, fg_color="transparent")
        affiner_row.pack(fill="x", pady=3)

        self.affiner_entry = ctk.CTkEntry(
            affiner_row,
            placeholder_text='Ex: "rends le refrain plus accrocheur", "version plus sombre"...',
        )
        self.affiner_entry.pack(side="left", fill="x", expand=True, padx=(0, 8))
        ctk.CTkButton(
            affiner_row, text="Affiner", width=100, command=self._affiner_paroles
        ).pack(side="right")

        self.paroles_status = ctk.CTkLabel(tab, text="", text_color="gray")
        self.paroles_status.pack()

    # ------------------------------------------------------------------ #
    # Onglet 2 — Musique
    # ------------------------------------------------------------------ #
    def _onglet_musique(self):
        tab = self.tabs.tab("2. Musique")

        ctk.CTkLabel(
            tab,
            text="Génère un instrumental à partir du style et thème définis à l'étape 1.",
            text_color="gray",
        ).pack(pady=(15, 5))

        ctk.CTkButton(
            tab, text="🎹 Générer l'instrumental", command=self._generer_musique
        ).pack(pady=10)

        self.musique_status = ctk.CTkLabel(tab, text="", text_color="gray")
        self.musique_status.pack()

        self.musique_path_label = ctk.CTkLabel(tab, text="", text_color="#4CAF50")
        self.musique_path_label.pack()

        ctk.CTkButton(
            tab, text="▶ Écouter l'instrumental", command=self._jouer_instrumental
        ).pack(pady=5)

    # ------------------------------------------------------------------ #
    # Onglet 3 — Enregistrement
    # ------------------------------------------------------------------ #
    def _onglet_enregistrement(self):
        tab = self.tabs.tab("3. Enregistrement")

        ctk.CTkLabel(
            tab,
            text="Enregistre ta voix. L'instrumental joue en fond si disponible.",
            text_color="gray",
        ).pack(pady=(15, 10))

        btn_row = ctk.CTkFrame(tab, fg_color="transparent")
        btn_row.pack(pady=10)

        self.btn_record = ctk.CTkButton(
            btn_row,
            text="⏺ Enregistrer",
            fg_color="#E53935",
            hover_color="#B71C1C",
            width=160,
            command=self._toggle_enregistrement,
        )
        self.btn_record.pack(side="left", padx=10)

        self.record_status = ctk.CTkLabel(tab, text="En attente...", text_color="gray")
        self.record_status.pack(pady=5)

        self.record_path_label = ctk.CTkLabel(tab, text="", text_color="#4CAF50")
        self.record_path_label.pack()

        ctk.CTkButton(
            tab, text="▶ Réécouter l'enregistrement", command=self._jouer_vocal
        ).pack(pady=5)

    # ------------------------------------------------------------------ #
    # Onglet 4 — Post-production
    # ------------------------------------------------------------------ #
    def _onglet_postprod(self):
        tab = self.tabs.tab("4. Post-prod")

        ctk.CTkLabel(
            tab,
            text="EQ vocal · Compression · Reverb · Pitch correction",
            text_color="gray",
        ).pack(pady=(15, 10))

        options_row = ctk.CTkFrame(tab, fg_color="transparent")
        options_row.pack(pady=5)

        ctk.CTkLabel(options_row, text="Reverb :").pack(side="left", padx=(0, 5))
        self.reverb_var = ctk.CTkOptionMenu(
            options_row, values=["small", "medium", "large"], width=120
        )
        self.reverb_var.set(DEFAULT_REVERB)
        self.reverb_var.pack(side="left", padx=(0, 20))

        self.delay_var = ctk.BooleanVar(value=False)
        ctk.CTkCheckBox(options_row, text="Delay", variable=self.delay_var).pack(side="left")

        ctk.CTkButton(
            tab, text="🎛 Appliquer post-production", command=self._post_prod
        ).pack(pady=10)

        self.postprod_status = ctk.CTkLabel(tab, text="", text_color="gray")
        self.postprod_status.pack()

        ctk.CTkButton(
            tab,
            text="🎚 Mixer voix + instrumental",
            fg_color="#1565C0",
            hover_color="#0D47A1",
            command=self._mixer,
        ).pack(pady=10)

        self.mix_status = ctk.CTkLabel(tab, text="", text_color="gray")
        self.mix_status.pack()

        ctk.CTkButton(
            tab, text="▶ Écouter le mix", command=self._jouer_mix
        ).pack(pady=5)

    # ------------------------------------------------------------------ #
    # Onglet 5 — Export
    # ------------------------------------------------------------------ #
    def _onglet_export(self):
        tab = self.tabs.tab("5. Export")

        ctk.CTkLabel(tab, text="Exporte le résultat final.", text_color="gray").pack(pady=(15, 10))

        self.format_var = ctk.StringVar(value="MP3")
        fmt_row = ctk.CTkFrame(tab, fg_color="transparent")
        fmt_row.pack(pady=5)
        ctk.CTkRadioButton(fmt_row, text="MP3 (320kbps)", variable=self.format_var, value="MP3").pack(side="left", padx=15)
        ctk.CTkRadioButton(fmt_row, text="WAV (lossless)", variable=self.format_var, value="WAV").pack(side="left", padx=15)

        ctk.CTkButton(tab, text="💾 Exporter", command=self._exporter).pack(pady=10)

        self.export_status = ctk.CTkLabel(tab, text="", text_color="gray")
        self.export_status.pack()

        self.export_path_label = ctk.CTkLabel(tab, text="", text_color="#4CAF50", wraplength=700)
        self.export_path_label.pack(pady=5)

    # ================================================================== #
    # Callbacks (tournent dans des threads pour ne pas bloquer l'UI)
    # ================================================================== #

    def _generer_paroles(self):
        style = self.style_var.get().strip()
        theme = self.theme_var.get().strip()
        langue = self.langue_var.get()
        if not style or not theme:
            messagebox.showwarning("Champs manquants", "Remplis le style et le thème.")
            return
        self._set_status(self.paroles_status, "⏳ Génération en cours...", "gray")
        threading.Thread(
            target=self._run_generer_paroles, args=(style, theme, langue), daemon=True
        ).start()

    def _run_generer_paroles(self, style, theme, langue):
        try:
            paroles = generer_paroles(style, theme, langue)
            self.after(0, lambda: self._afficher_paroles(paroles))
            self.after(0, lambda: self._set_status(self.paroles_status, "✅ Paroles générées", "#4CAF50"))
        except Exception as e:
            self.after(0, lambda: self._set_status(self.paroles_status, f"❌ {e}", "#E53935"))

    def _afficher_paroles(self, texte):
        self.paroles_text.delete("1.0", "end")
        self.paroles_text.insert("1.0", texte)

    def _affiner_paroles(self):
        paroles = self.paroles_text.get("1.0", "end").strip()
        instruction = self.affiner_entry.get().strip()
        langue = self.langue_var.get()
        if not paroles:
            messagebox.showwarning("Aucune parole", "Génère des paroles d'abord.")
            return
        if not instruction:
            messagebox.showwarning("Instruction manquante", "Décris ce que tu veux modifier.")
            return
        self._set_status(self.paroles_status, "⏳ Affinage en cours...", "gray")
        threading.Thread(
            target=self._run_affiner, args=(paroles, instruction, langue), daemon=True
        ).start()

    def _run_affiner(self, paroles, instruction, langue):
        try:
            affinee = affiner_paroles(paroles, instruction, langue)
            self.after(0, lambda: self._afficher_paroles(affinee))
            self.after(0, lambda: self._set_status(self.paroles_status, "✅ Paroles affinées", "#4CAF50"))
        except Exception as e:
            self.after(0, lambda: self._set_status(self.paroles_status, f"❌ {e}", "#E53935"))

    def _generer_musique(self):
        style = self.style_var.get().strip() or "cinematic"
        theme = self.theme_var.get().strip() or "epic"
        self._set_status(self.musique_status, "⏳ Génération instrumentale...", "gray")
        threading.Thread(
            target=self._run_generer_musique, args=(style, theme), daemon=True
        ).start()

    def _run_generer_musique(self, style, theme):
        try:
            path = generer_musique(style, theme)
            state["instrumental_path"] = path
            nom = os.path.basename(path) if path else "?"
            self.after(0, lambda: self._set_status(self.musique_status, "✅ Instrumental prêt", "#4CAF50"))
            self.after(0, lambda: self.musique_path_label.configure(text=nom))
        except Exception as e:
            self.after(0, lambda: self._set_status(self.musique_status, f"❌ {e}", "#E53935"))

    def _jouer_instrumental(self):
        self._jouer_fichier(state.get("instrumental_path"), "instrumental")

    def _toggle_enregistrement(self):
        if not enregistreur.recording:
            self.btn_record.configure(text="⏹ Stop", fg_color="#555", hover_color="#333")
            self._set_status(self.record_status, "🔴 Enregistrement en cours...", "#E53935")
            enregistreur.demarrer(instrumental_path=state.get("instrumental_path"))
        else:
            path = enregistreur.arreter()
            self.btn_record.configure(
                text="⏺ Enregistrer", fg_color="#E53935", hover_color="#B71C1C"
            )
            if path:
                state["vocal_path"] = path
                self._set_status(self.record_status, "✅ Enregistrement sauvegardé", "#4CAF50")
                self.record_path_label.configure(text=os.path.basename(path))
            else:
                self._set_status(self.record_status, "⚠️ Aucun audio capturé", "orange")

    def _jouer_vocal(self):
        self._jouer_fichier(state.get("vocal_path"), "vocal")

    def _post_prod(self):
        if not state.get("vocal_path"):
            messagebox.showwarning("Manquant", "Enregistre ta voix d'abord (étape 3).")
            return
        reverb = self.reverb_var.get()
        delay = self.delay_var.get()
        self._set_status(self.postprod_status, "⏳ Post-production en cours...", "gray")
        threading.Thread(
            target=self._run_post_prod, args=(reverb, delay), daemon=True
        ).start()

    def _run_post_prod(self, reverb, delay):
        try:
            path = post_production_vocale(state["vocal_path"], reverb_size=reverb, avec_delay=delay)
            state["vocal_prod_path"] = path
            self.after(0, lambda: self._set_status(self.postprod_status, "✅ Post-production appliquée", "#4CAF50"))
        except Exception as e:
            self.after(0, lambda: self._set_status(self.postprod_status, f"❌ {e}", "#E53935"))

    def _mixer(self):
        if not state.get("vocal_prod_path"):
            messagebox.showwarning("Manquant", "Applique la post-production d'abord.")
            return
        if not state.get("instrumental_path"):
            messagebox.showwarning("Manquant", "Génère un instrumental d'abord (étape 2).")
            return
        self._set_status(self.mix_status, "⏳ Mixage en cours...", "gray")
        threading.Thread(target=self._run_mixer, daemon=True).start()

    def _run_mixer(self):
        try:
            path = mixer_final(state["vocal_prod_path"], state["instrumental_path"])
            state["mix_path"] = path
            self.after(0, lambda: self._set_status(self.mix_status, "✅ Mix final prêt", "#4CAF50"))
        except Exception as e:
            self.after(0, lambda: self._set_status(self.mix_status, f"❌ {e}", "#E53935"))

    def _jouer_mix(self):
        self._jouer_fichier(state.get("mix_path"), "mix")

    def _exporter(self):
        source = state.get("mix_path") or state.get("vocal_prod_path")
        if not source:
            messagebox.showwarning("Rien à exporter", "Complète les étapes précédentes.")
            return
        fmt = self.format_var.get()
        theme = self.theme_var.get().strip() or "track"
        threading.Thread(
            target=self._run_export, args=(source, fmt, theme), daemon=True
        ).start()

    def _run_export(self, source, fmt, theme):
        try:
            from pydub import AudioSegment
            from config import EXPORT_BITRATE

            export_dir = os.path.join(os.path.dirname(__file__), "exports")
            os.makedirs(export_dir, exist_ok=True)

            nom = "".join(c for c in theme.replace(" ", "_")[:30] if c.isalnum() or c == "_")
            ext = fmt.lower()
            output_path = os.path.join(export_dir, f"{nom}.{ext}")

            audio = AudioSegment.from_file(source)
            if fmt == "MP3":
                audio.export(output_path, format="mp3", bitrate=EXPORT_BITRATE)
            else:
                audio.export(output_path, format="wav")

            self.after(0, lambda: self._set_status(self.export_status, f"✅ Exporté", "#4CAF50"))
            self.after(0, lambda: self.export_path_label.configure(text=output_path))
        except Exception as e:
            self.after(0, lambda: self._set_status(self.export_status, f"❌ {e}", "#E53935"))

    # ================================================================== #
    # Utilitaires
    # ================================================================== #

    def _set_status(self, label: ctk.CTkLabel, text: str, color: str):
        label.configure(text=text, text_color=color)

    def _jouer_fichier(self, path: str | None, nom: str):
        if not path or not os.path.exists(path):
            messagebox.showinfo("Indisponible", f"Aucun fichier {nom} disponible.")
            return
        threading.Thread(target=self._play_audio, args=(path,), daemon=True).start()

    @staticmethod
    def _play_audio(path: str):
        try:
            import pygame
            pygame.mixer.init()
            pygame.mixer.music.load(path)
            pygame.mixer.music.play()
        except ImportError:
            # Fallback : playsound si pygame absent
            try:
                from playsound import playsound
                playsound(path, block=False)
            except Exception:
                import subprocess
                subprocess.Popen(["start", path], shell=True)
        except Exception as e:
            print(f"[player] Erreur lecture : {e}")
