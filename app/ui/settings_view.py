from tkinter import messagebox

import customtkinter as ctk

from .. import config, database


class SettingsView(ctk.CTkFrame):
    def __init__(self, parent, theme, on_appearance_change=None):
        super().__init__(parent, fg_color=theme["bg"])
        self.theme = theme
        self.on_appearance_change = on_appearance_change

        ctk.CTkLabel(
            self, text="Settings", font=config.FONTS["h1"], text_color=theme["text"]
        ).pack(anchor="w", padx=28, pady=(26, 16))

        appearance_card = self._make_section_card("Appearance")
        self._appearance_row(appearance_card)

        data_card = self._make_section_card("Data")
        self._action_row(
            data_card, "Load sample data",
            "Fills in a few months of example transactions so you can try the "
            "dashboard and reports right away.",
            self._load_sample,
        )
        self._action_row(
            data_card, "Clear all data",
            "Permanently deletes every transaction. Budgets are kept.",
            self._clear_data, danger=True,
        )

    def _make_section_card(self, title):
        theme = self.theme
        ctk.CTkLabel(
            self, text=title, font=config.FONTS["small"], text_color=theme["text_muted"]
        ).pack(anchor="w", padx=28, pady=(10, 4))
        card = ctk.CTkFrame(self, corner_radius=12, fg_color=theme["surface"])
        card.pack(fill="x", padx=24, pady=(0, 6))
        return card

    def _appearance_row(self, card):
        theme = self.theme
        row = ctk.CTkFrame(card, fg_color="transparent")
        row.pack(fill="x", padx=18, pady=16)
        row.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(
            row, text="Theme", font=config.FONTS["body"], text_color=theme["text"]
        ).grid(row=0, column=0, sticky="w")
        ctk.CTkLabel(
            row, text="Switch between light and dark mode.", font=config.FONTS["small"],
            text_color=theme["text_muted"],
        ).grid(row=1, column=0, sticky="w")

        mode = ctk.get_appearance_mode()
        switch_var = ctk.StringVar(value=mode)
        switch = ctk.CTkSegmentedButton(
            row, values=["Light", "Dark"], variable=switch_var, command=self._change_appearance
        )
        switch.set(mode)
        switch.grid(row=0, column=1, rowspan=2, sticky="e")

    def _change_appearance(self, value):
        ctk.set_appearance_mode(value)
        if self.on_appearance_change:
            self.on_appearance_change(value.lower())

    def _action_row(self, card, title, description, command, danger=False):
        theme = self.theme
        row = ctk.CTkFrame(card, fg_color="transparent")
        row.pack(fill="x", padx=18, pady=14)
        row.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(
            row, text=title, font=config.FONTS["body"], text_color=theme["text"]
        ).grid(row=0, column=0, sticky="w")
        ctk.CTkLabel(
            row, text=description, font=config.FONTS["small"], text_color=theme["text_muted"],
            wraplength=420, justify="left",
        ).grid(row=1, column=0, sticky="w")
        ctk.CTkButton(
            row, text=title, command=command, width=150,
            fg_color=theme["coral"] if danger else "transparent",
            hover_color=theme["coral"] if danger else theme["surface_alt"],
            text_color="#FFFFFF" if danger else theme["text"],
            border_width=0 if danger else 1, border_color=theme["border"],
        ).grid(row=0, column=1, rowspan=2, sticky="e")

    def _load_sample(self):
        database.seed_sample_data()
        messagebox.showinfo("Sample data loaded", "A few months of example transactions were added.")

    def _clear_data(self):
        if messagebox.askyesno(
            "Clear all data", "This will permanently delete every transaction. Continue?"
        ):
            database.clear_all_transactions()
            messagebox.showinfo("Data cleared", "All transactions were removed.")
