
import sqlite3
import csv
from datetime import datetime
from pathlib import Path
import tkinter as tk
from tkinter import ttk, messagebox, filedialog

# ==================================================
# CONFIGURATION
# ==================================================

APP_DIR = Path(__file__).resolve().parent
DB_PATH = APP_DIR / "suivi_retard.db"

BG = "#F4F7FB"
CARD = "#FFFFFF"
NAVY = "#172B4D"
MUTED = "#68778D"
BLUE = "#356AE6"
RED = "#D9485F"
GREEN = "#16866A"
BORDER = "#E1E7F0"


class SuiviRetard(tk.Tk):

    def __init__(self):
        super().__init__()

        self.title("Retard Au Drive")
        self.geometry("1120x740")
        self.minsize(900, 620)
        self.configure(bg=BG)

        self.selected_id = None
        self.search_var = tk.StringVar()
        self.first_var = tk.StringVar()
        self.last_var = tk.StringVar()
        self.late_var = tk.StringVar(value="0")
        self.absent_var = tk.StringVar(value="0")
        self.notes_var = tk.StringVar()
        self.status_var = tk.StringVar(value="Prêt")

        self._setup_style()
        self._init_db()
        self._build_ui()
        self.refresh_table()

    # ==================================================
    # STYLE
    # ==================================================

    def _setup_style(self):
        style = ttk.Style(self)

        try:
            style.theme_use("clam")
        except tk.TclError:
            pass

        style.configure(
            "Treeview",
            background=CARD,
            fieldbackground=CARD,
            foreground=NAVY,
            rowheight=34,
            borderwidth=0,
            font=("Segoe UI", 10)
        )

        style.configure(
            "Treeview.Heading",
            background="#EDF2FA",
            foreground=MUTED,
            font=("Segoe UI", 9, "bold"),
            padding=(10, 10),
            relief="flat"
        )

        style.map(
            "Treeview",
            background=[("selected", "#DCE8FF")],
            foreground=[("selected", NAVY)]
        )

        style.configure("TEntry", padding=9,
                        font=("Segoe UI", 10))
        style.configure("TSpinbox", padding=7,
                        font=("Segoe UI", 10))
        style.configure("TButton", font=("Segoe UI", 10),
                        padding=(12, 9))

        style.configure(
            "Primary.TButton",
            background=BLUE,
            foreground="white"
        )

        style.map(
            "Primary.TButton",
            background=[("active", "#2856C5")],
            foreground=[("active", "white")]
        )

        style.configure(
            "Danger.TButton",
            background="#FCE8EC",
            foreground=RED
        )

        style.map(
            "Danger.TButton",
            background=[("active", "#F8D7DE")]
        )

        style.configure(
            "TLabel",
            background=CARD,
            foreground=NAVY,
            font=("Segoe UI", 10)
        )

        style.configure(
            "Muted.TLabel",
            background=CARD,
            foreground=MUTED,
            font=("Segoe UI", 9)
        )

    # ==================================================
    # BASE DE DONNEES
    # ==================================================

    def _init_db(self):
        with sqlite3.connect(DB_PATH) as con:
            con.execute("""
                CREATE TABLE IF NOT EXISTS people (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    first_name TEXT NOT NULL,
                    last_name TEXT NOT NULL,
                    late_count INTEGER NOT NULL DEFAULT 0,
                    absent_count INTEGER NOT NULL DEFAULT 0,
                    notes TEXT NOT NULL DEFAULT '',
                    updated_at TEXT NOT NULL
                )
            """)

            con.execute("""
                CREATE INDEX IF NOT EXISTS idx_people_name
                ON people(last_name, first_name)
            """)

    # ==================================================
    # INTERFACE
    # ==================================================

    def _build_ui(self):
        header = tk.Frame(
            self, bg=NAVY, padx=28, pady=22
        )
        header.pack(fill="x")

        left = tk.Frame(header, bg=NAVY)
        left.pack(side="left", fill="x", expand=True)

        tk.Label(
            left,
            text="CREER PAR HUGO",
            bg=NAVY,
            fg="#B9CCFF",
            font=("Segoe UI", 9, "bold")
        ).pack(anchor="w")

        tk.Label(
            left,
            text="SUIVI DES RETARDS AU DRIVE",
            bg=NAVY,
            fg="white",
            font=("Segoe UI", 22, "bold")
        ).pack(anchor="w", pady=(4, 2))

        tk.Label(
            left,
            text="Gardez un historique simple des retards et absences.",
            bg=NAVY,
            fg="#D6DFEF",
            font=("Segoe UI", 10)
        ).pack(anchor="w")

        tk.Button(
            header,
            text="＋  Ajouter une personne",
            command=self.new_person,
            bg=BLUE,
            fg="white",
            activebackground="#2856C5",
            activeforeground="white",
            relief="flat",
            bd=0,
            padx=16,
            pady=12,
            font=("Segoe UI", 10, "bold"),
            cursor="hand2"
        ).pack(side="right", padx=(15, 0))

        body = tk.Frame(self, bg=BG, padx=24, pady=20)
        body.pack(fill="both", expand=True)

        # Cartes statistiques
        stats = tk.Frame(body, bg=BG)
        stats.pack(fill="x", pady=(0, 18))

        self.stat_people = self._stat_card(
            stats, "PERSONNES SUIVIES", "0", BLUE
        )

        self.stat_late = self._stat_card(
            stats, "RETARDS CUMULÉS", "0", "#C47A16"
        )

        self.stat_absent = self._stat_card(
            stats, "ABSENCES CUMULÉES", "0", RED
        )

        # Zone principale
        content = tk.Frame(body, bg=BG)
        content.pack(fill="both", expand=True)
        content.columnconfigure(0, weight=3)
        content.columnconfigure(1, weight=2)
        content.rowconfigure(0, weight=1)

        # Répertoire
        list_card = tk.Frame(
            content,
            bg=CARD,
            highlightbackground=BORDER,
            highlightthickness=1
        )

        list_card.grid(
            row=0, column=0, sticky="nsew",
            padx=(0, 14)
        )

        list_head = tk.Frame(
            list_card, bg=CARD, padx=18, pady=16
        )
        list_head.pack(fill="x")

        tk.Label(
            list_head,
            text="Répertoire",
            bg=CARD,
            fg=NAVY,
            font=("Segoe UI", 14, "bold")
        ).pack(anchor="w")

        tk.Label(
            list_head,
            text="Sélectionnez une ligne pour modifier une fiche.",
            bg=CARD,
            fg=MUTED,
            font=("Segoe UI", 9)
        ).pack(anchor="w", pady=(3, 12))

        search_row = tk.Frame(list_head, bg=CARD)
        search_row.pack(fill="x")

        self.search_entry = ttk.Entry(
            search_row, textvariable=self.search_var
        )
        self.search_entry.pack(
            side="left", fill="x", expand=True
        )

        tk.Button(
            search_row,
            text="Effacer",
            command=lambda: self.search_var.set(""),
            bg="#EDF2FA",
            fg=NAVY,
            relief="flat",
            padx=10,
            pady=7,
            cursor="hand2"
        ).pack(side="left", padx=(8, 0))

        self.search_var.trace_add(
            "write",
            lambda *_: self.refresh_table()
        )

        table_frame = tk.Frame(
            list_card,
            background=CARD,
            padx=14,
            pady=0
        )
        table_frame.pack(fill="both", expand=True)

        columns = ("name", "late", "absent")

        

        self.tree = ttk.Treeview(
            table_frame,
            columns=(
                 "first_name",
                 "last_name",
                 "late_count",
                  "absent_count",
                "updated_at"
            ),
            show="headings"
        )   

        self.tree.heading("first_name", text="PRÉNOM")
        self.tree.heading("last_name", text="NOM")
        self.tree.heading("late_count", text="RETARDS")
        self.tree.heading("absent_count", text="ABSENCES")
        self.tree.heading("updated_at", text="DERNIÈRE MODIFICATION")

        self.tree.column("first_name", width=120, anchor="w")
        self.tree.column("last_name", width=120, anchor="w")
        self.tree.column("late_count", width=85, anchor="center")
        self.tree.column("absent_count", width=95, anchor="center")
        self.tree.column("updated_at", width=155, anchor="center")

        scrollbar = ttk.Scrollbar(
            table_frame,
            orient="vertical",
            command=self.tree.yview
        )

        self.tree.configure(
            yscrollcommand=scrollbar.set
        )

        self.tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        self.tree.bind("<<TreeviewSelect>>", self.on_select)
        self.tree.bind("<Double-1>", self.on_select)

        # Formulaire
        form_card = tk.Frame(
            content,
            bg=CARD,
            highlightbackground=BORDER,
            highlightthickness=1
        )

        form_card.grid(
            row=0, column=1, sticky="nsew"
        )

        form = tk.Frame(
            form_card, bg=CARD, padx=20, pady=18
        )
        form.pack(fill="both", expand=True)

        tk.Label(
            form,
            text="Fiche personne",
            bg=CARD,
            fg=NAVY,
            font=("Segoe UI", 14, "bold")
        ).pack(anchor="w")

        tk.Label(
            form,
            text="Ajoutez une personne ou mettez ses compteurs à jour.",
            bg=CARD,
            fg=MUTED,
            font=("Segoe UI", 9),
            wraplength=300,
            justify="left"
        ).pack(anchor="w", pady=(3, 16))

        self._field_label(form, "Prénom")
        ttk.Entry(
            form, textvariable=self.first_var
        ).pack(fill="x", pady=(5, 12))

        self._field_label(form, "Nom")
        ttk.Entry(
            form, textvariable=self.last_var
        ).pack(fill="x", pady=(5, 12))

        counters = tk.Frame(form, bg=CARD)
        counters.pack(fill="x", pady=(0, 10))
        counters.columnconfigure(0, weight=1)
        counters.columnconfigure(1, weight=1)

        for col, title, var in [
            (0, "Nombre de retards", self.late_var),
            (1, "Nombre d’absences", self.absent_var)
        ]:
            block = tk.Frame(counters, bg=CARD)
            padx = (0, 8) if col == 0 else (8, 0)
            block.grid(
                row=0, column=col, sticky="ew", padx=padx
            )

            self._field_label(block, title)

            ttk.Spinbox(
                block,
                from_=0,
                to=999999,
                textvariable=var,
                width=8
            ).pack(fill="x", pady=(5, 0))

        self._field_label(form, "Note (facultatif)")

        ttk.Entry(
            form, textvariable=self.notes_var
        ).pack(fill="x", pady=(5, 8))

        tk.Label(
            form,
            text="Ex. : De mauvaise foi, pas aimable...",
            bg=CARD,
            fg=MUTED,
            font=("Segoe UI", 8)
        ).pack(anchor="w", pady=(0, 14))

        self.save_btn = ttk.Button(
            form,
            text="Enregistrer la fiche",
            style="Primary.TButton",
            command=self.save_person
        )
        self.save_btn.pack(fill="x", pady=(0, 8))

        ttk.Button(
            form,
            text="Nouvelle fiche / Réinitialiser",
            command=self.new_person
        ).pack(fill="x", pady=(0, 8))

        ttk.Button(
            form,
            text="Supprimer la personne sélectionnée",
            style="Danger.TButton",
            command=self.delete_person
        ).pack(fill="x", pady=(0, 8))

        ttk.Button(
            form,
            text="Exporter en CSV…",
            command=self.export_csv
        ).pack(fill="x")

        # Pied de page
        footer = tk.Frame(body, bg=BG)
        footer.pack(fill="x", pady=(12, 0))

        tk.Label(
            footer,
            text="💾  Les données sont enregistrées automatiquement dans un fichier local.",
            bg=BG,
            fg=MUTED,
            font=("Segoe UI", 9)
        ).pack(side="left")

        tk.Label(
            footer,
            textvariable=self.status_var,
            bg=BG,
            fg=MUTED,
            font=("Segoe UI", 9)
        ).pack(side="right")

    def _stat_card(self, parent, title, value, accent):
        card = tk.Frame(
            parent,
            bg=CARD,
            highlightbackground=BORDER,
            highlightthickness=1,
            padx=18,
            pady=14
        )

        card.pack(
            side="left", fill="x", expand=True, padx=(0, 12)
        )

        tk.Frame(
            card, bg=accent, height=3
        ).pack(fill="x", pady=(0, 10))

        tk.Label(
            card,
            text=title,
            bg=CARD,
            fg=MUTED,
            font=("Segoe UI", 8, "bold")
        ).pack(anchor="w")

        value_label = tk.Label(
            card,
            text=value,
            bg=CARD,
            fg=NAVY,
            font=("Segoe UI", 23, "bold")
        )
        value_label.pack(anchor="w", pady=(4, 0))

        return value_label

    def _field_label(self, parent, text):
        tk.Label(
            parent,
            text=text,
            bg=CARD,
            fg=NAVY,
            font=("Segoe UI", 9, "bold")
        ).pack(anchor="w")

    # ==================================================
    # ACTUALISATION DU REPERTOIRE
    # ==================================================

    def refresh_table(self):
        query = self.search_var.get().strip().lower()

        for item in self.tree.get_children():
            self.tree.delete(item)

        with sqlite3.connect(DB_PATH) as con:
            con.row_factory = sqlite3.Row

            rows = con.execute("""
                SELECT * FROM people
                WHERE lower(first_name || ' ' || last_name) LIKE ?
                   OR lower(last_name || ' ' || first_name) LIKE ?
                ORDER BY last_name COLLATE NOCASE,
                         first_name COLLATE NOCASE
            """, (f"%{query}%", f"%{query}%")).fetchall()

            totals = con.execute("""
                SELECT COUNT(*) AS people,
                       COALESCE(SUM(late_count), 0) AS late,
                       COALESCE(SUM(absent_count), 0) AS absent
                FROM people
            """).fetchone()

        for row in rows:
            self.tree.insert(
                "",
                "end",
                iid=str(row["id"]),
                values=(
                    f'{row["last_name"]} {row["first_name"]}',
                    row["late_count"],
                    row["absent_count"],
                    row["updated_at"]
                )
            )

        self.stat_people.config(text=str(totals["people"]))
        self.stat_late.config(text=str(totals["late"]))
        self.stat_absent.config(text=str(totals["absent"]))

        self.status_var.set(
            f"{len(rows)} résultat(s) affiché(s)"
        )

    # ==================================================
    # SELECTION D'UNE PERSONNE
    # ==================================================

    def on_select(self, _event=None):
        selection = self.tree.selection()

        if not selection:
            return

        person_id = int(selection[0])

        with sqlite3.connect(DB_PATH) as con:
            con.row_factory = sqlite3.Row
            row = con.execute(
                "SELECT * FROM people WHERE id = ?",
                (person_id,)
            ).fetchone()

        if row:
            self.selected_id = person_id
            self.first_var.set(row["first_name"])
            self.last_var.set(row["last_name"])
            self.late_var.set(str(row["late_count"]))
            self.absent_var.set(str(row["absent_count"]))
            self.notes_var.set(row["notes"])

            self.save_btn.config(text="Mettre à jour la fiche")

            self.status_var.set(
                f'Fiche sélectionnée : {row["first_name"]} {row["last_name"]}'
            )

    # ==================================================
    # VALIDATION
    # ==================================================

    def _counter(self, value, label):
        try:
            number = int(value)

            if number < 0:
                raise ValueError

            return number

        except (ValueError, TypeError):
            raise ValueError(
                f"Le champ « {label} » doit être un nombre "
                "entier positif ou nul."
            )

    # ==================================================
    # AJOUT ET MODIFICATION
    # ==================================================

    def get_modification_date(self):
        """Récupère automatiquement la date et l'heure."""
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


    def save_person(self):
        first = self.first_var.get().strip()
        last = self.last_var.get().strip()

        if not first or not last:
            messagebox.showwarning(
                "Informations manquantes",
                "Veuillez renseigner le prénom et le nom."
            )
            return

        try:
            late = self._counter(
                self.late_var.get(), "Nombre de retards"
            )
            absent = self._counter(
                self.absent_var.get(), "Nombre d’absences"
            )

        except ValueError as exc:
            messagebox.showerror("Valeur incorrecte", str(exc))
            return

        notes = self.notes_var.get().strip()
        now = self.get_modification_date()

        with sqlite3.connect(DB_PATH) as con:

            if self.selected_id is None:

                existing = con.execute("""
                    SELECT id FROM people
                    WHERE lower(first_name) = lower(?)
                      AND lower(last_name) = lower(?)
                """, (first, last)).fetchone()

                if existing:
                    confirm = messagebox.askyesno(
                        "Personne déjà présente",
                        "Une personne portant ce prénom et ce nom "
                        "existe déjà. Voulez-vous ouvrir sa fiche ?"
                    )

                    if not confirm:
                        return

                    self.selected_id = existing[0]

                    con.execute("""
                        UPDATE people
                        SET first_name = ?,
                            last_name = ?,
                            late_count = ?,
                            absent_count = ?,
                            notes = ?,
                            updated_at = ?
                        WHERE id = ?
                    """, (
                        first, last, late, absent,
                        notes, now, self.selected_id
                    ))

                else:
                    cursor = con.execute("""
                        INSERT INTO people (
                            first_name, last_name,
                            late_count, absent_count,
                            notes, updated_at
                        )
                        VALUES (?, ?, ?, ?, ?, ?)
                    """, (
                        first, last, late, absent, notes, now
                    ))

                    self.selected_id = cursor.lastrowid

            else:
                con.execute("""
                    UPDATE people
                    SET first_name = ?,
                        last_name = ?,
                        late_count = ?,
                        absent_count = ?,
                        notes = ?,
                        updated_at = ?
                    WHERE id = ?
                """, (
                    first, last, late, absent,
                    notes, now, self.selected_id
                ))

        self.refresh_table()

        if (
            self.selected_id
            and self.tree.exists(str(self.selected_id))
        ):
            self.tree.selection_set(str(self.selected_id))
            self.tree.see(str(self.selected_id))

        self.save_btn.config(text="Mettre à jour la fiche")
        self.status_var.set("Fiche enregistrée ✓")

    # ==================================================
    # NOUVELLE FICHE
    # ==================================================

    def new_person(self):
        self.selected_id = None

        self.first_var.set("")
        self.last_var.set("")
        self.late_var.set("0")
        self.absent_var.set("0")
        self.notes_var.set("")

        selection = self.tree.selection()

        if selection:
            self.tree.selection_remove(selection)

        self.save_btn.config(text="Enregistrer la fiche")
        self.status_var.set("Nouvelle fiche")
        self.search_entry.focus_set()

    # ==================================================
    # SUPPRESSION
    # ==================================================

    def delete_person(self):
        if self.selected_id is None:
            messagebox.showinfo(
                "Aucune sélection",
                "Sélectionnez une personne dans le répertoire."
            )
            return

        name = (
            f"{self.first_var.get()} {self.last_var.get()}"
        ).strip()

        confirm = messagebox.askyesno(
            "Confirmer la suppression",
            f"Supprimer définitivement la fiche de {name} ?"
        )

        if not confirm:
            return

        with sqlite3.connect(DB_PATH) as con:
            con.execute(
                "DELETE FROM people WHERE id = ?",
                (self.selected_id,)
            )

        self.new_person()
        self.refresh_table()
        self.status_var.set("Fiche supprimée")

    # ==================================================
    # EXPORT CSV
    # ==================================================

    def export_csv(self):
        path = filedialog.asksaveasfilename(
            title="Exporter les fiches",
            defaultextension=".csv",
            filetypes=[("Fichier CSV", "*.csv")],
            initialfile="retard_drive.csv"
        )

        if not path:
            return

        with sqlite3.connect(DB_PATH) as con:
            rows = con.execute("""
                SELECT first_name, last_name,
                       late_count, absent_count,
                       notes, updated_at
                FROM people
                ORDER BY last_name, first_name
            """).fetchall()

        try:
            with open(
                path, "w", newline="", encoding="utf-8-sig"
            ) as file:
                writer = csv.writer(file, delimiter=";")

                writer.writerow([
                    "Prénom",
                    "Nom",
                    "Retards",
                    "Absences",
                    "Note",
                    "Dernière mise à jour"
                ])

                writer.writerows(rows)

            messagebox.showinfo(
                "Export terminé",
                f"{len(rows)} fiche(s) exportée(s)."
            )

            self.status_var.set("Export CSV terminé ✓")

        except OSError as exc:
            messagebox.showerror("Erreur d’export", str(exc))


# ==================================================
# DEMARRAGE
# ==================================================

if __name__ == "__main__":
    app = SuiviRetard()
    app.mainloop()
