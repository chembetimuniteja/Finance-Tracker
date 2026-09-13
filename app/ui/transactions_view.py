from datetime import date
from tkinter import messagebox, ttk

import customtkinter as ctk

from .. import config, database


class TransactionsView(ctk.CTkFrame):
    def __init__(self, parent, theme):
        super().__init__(parent, fg_color=theme["bg"])
        self.theme = theme

        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(1, weight=1)

        ctk.CTkLabel(
            self, text="Transactions", font=config.FONTS["h1"], text_color=theme["text"]
        ).grid(row=0, column=0, columnspan=2, sticky="w", padx=28, pady=(26, 10))

        self._build_form()
        self._build_table()
        self.refresh()

    # -- entry form -----------------------------------------------------
    def _build_form(self):
        theme = self.theme
        card = ctk.CTkFrame(self, corner_radius=12, fg_color=theme["surface"], width=280)
        card.grid(row=1, column=0, sticky="nsw", padx=(24, 12), pady=(0, 24))
        card.grid_propagate(False)
        card.grid_columnconfigure(0, weight=1)

        pad = dict(padx=20, pady=(10, 0))
        ctk.CTkLabel(
            card, text="Add transaction", font=config.FONTS["h3"], text_color=theme["text"]
        ).grid(row=0, column=0, sticky="w", padx=20, pady=(20, 6))

        self.type_var = ctk.StringVar(value="expense")
        ctk.CTkSegmentedButton(
            card, values=["expense", "income"], variable=self.type_var,
            command=lambda _v: self._refresh_categories(),
        ).grid(row=1, column=0, sticky="ew", **pad)

        ctk.CTkLabel(
            card, text="Date (YYYY-MM-DD)", font=config.FONTS["small"], text_color=theme["text_muted"]
        ).grid(row=2, column=0, sticky="w", **pad)
        self.date_entry = ctk.CTkEntry(card)
        self.date_entry.insert(0, date.today().isoformat())
        self.date_entry.grid(row=3, column=0, sticky="ew", padx=20, pady=(2, 0))

        ctk.CTkLabel(
            card, text="Category", font=config.FONTS["small"], text_color=theme["text_muted"]
        ).grid(row=4, column=0, sticky="w", **pad)
        self.category_var = ctk.StringVar(value=config.EXPENSE_CATEGORIES[0])
        self.category_menu = ctk.CTkOptionMenu(
            card, variable=self.category_var, values=config.EXPENSE_CATEGORIES
        )
        self.category_menu.grid(row=5, column=0, sticky="ew", padx=20, pady=(2, 0))

        ctk.CTkLabel(
            card, text="Description", font=config.FONTS["small"], text_color=theme["text_muted"]
        ).grid(row=6, column=0, sticky="w", **pad)
        self.desc_entry = ctk.CTkEntry(card, placeholder_text="Optional")
        self.desc_entry.grid(row=7, column=0, sticky="ew", padx=20, pady=(2, 0))

        ctk.CTkLabel(
            card, text="Amount", font=config.FONTS["small"], text_color=theme["text_muted"]
        ).grid(row=8, column=0, sticky="w", **pad)
        self.amount_entry = ctk.CTkEntry(card, placeholder_text="0.00")
        self.amount_entry.grid(row=9, column=0, sticky="ew", padx=20, pady=(2, 0))
        self.amount_entry.bind("<Return>", lambda _e: self._add_transaction())

        self.error_label = ctk.CTkLabel(
            card, text="", text_color=theme["coral"], font=config.FONTS["small"], wraplength=240, justify="left"
        )
        self.error_label.grid(row=10, column=0, sticky="w", padx=20, pady=(8, 0))

        # Wrapped in its own pack-managed frame rather than gridded directly
        # with sticky="ew" — see the note in components.SidebarButton for why.
        btn_wrap = ctk.CTkFrame(card, fg_color="transparent")
        btn_wrap.grid(row=11, column=0, sticky="ew", padx=20, pady=(14, 20))
        ctk.CTkButton(
            btn_wrap, text="Add transaction", command=self._add_transaction,
            fg_color=theme["accent"], hover_color=theme["accent_hover"],
        ).pack(fill="x")

    def _refresh_categories(self):
        cats = (
            config.EXPENSE_CATEGORIES if self.type_var.get() == "expense" else config.INCOME_CATEGORIES
        )
        self.category_menu.configure(values=cats)
        self.category_var.set(cats[0])

    # -- table ------------------------------------------------------------
    def _build_table(self):
        theme = self.theme
        card = ctk.CTkFrame(self, corner_radius=12, fg_color=theme["surface"])
        card.grid(row=1, column=1, sticky="nsew", padx=(12, 24), pady=(0, 24))
        card.grid_columnconfigure(0, weight=1)
        card.grid_rowconfigure(1, weight=1)

        toolbar = ctk.CTkFrame(card, fg_color="transparent")
        toolbar.grid(row=0, column=0, columnspan=2, sticky="ew", padx=16, pady=(16, 6))
        ctk.CTkLabel(
            toolbar, text="All transactions", font=config.FONTS["h3"], text_color=theme["text"]
        ).pack(side="left")
        ctk.CTkButton(
            toolbar, text="Delete selected", width=140, command=self._delete_selected,
            fg_color="transparent", border_width=1, border_color=theme["border"],
            text_color=theme["text_muted"], hover_color=theme["surface_alt"],
        ).pack(side="right")

        style = ttk.Style()
        style.theme_use("clam")
        style.configure(
            "Ledger.Treeview", background=theme["surface"], fieldbackground=theme["surface"],
            foreground=theme["text"], rowheight=30, borderwidth=0, font=(config.UI_FONT, 11),
        )
        style.configure(
            "Ledger.Treeview.Heading", background=theme["surface_alt"], foreground=theme["text_muted"],
            borderwidth=0, font=(config.UI_FONT, 10, "bold"),
        )
        style.map(
            "Ledger.Treeview",
            background=[("selected", theme["accent"])],
            foreground=[("selected", "#FFFFFF")],
        )

        # No separate "Type" column: the +/- sign on Amount already says
        # income vs. expense, and dropping it leaves enough room for Date
        # and Category to display in full instead of getting clipped.
        columns = ("date", "category", "description", "amount")
        self.tree = ttk.Treeview(card, columns=columns, show="headings", style="Ledger.Treeview")
        headers = {
            "date": "Date", "category": "Category", "description": "Description", "amount": "Amount",
        }
        # Fixed widths for everything except Description, which stretches
        # to absorb whatever space is left — this keeps Amount (the most
        # important column) always on-screen instead of getting pushed
        # past the visible edge when the window is narrower than the sum
        # of every column's "ideal" width.
        widths = {"date": 100, "category": 150, "description": 150, "amount": 110}
        stretch = {"date": False, "category": False, "description": True, "amount": False}
        for col in columns:
            self.tree.heading(col, text=headers[col])
            self.tree.column(
                col, width=widths[col], minwidth=widths[col],
                stretch=stretch[col], anchor="w" if col != "amount" else "e",
            )
        self.tree.grid(row=1, column=0, sticky="nsew", padx=(16, 0), pady=(0, 16))

        v_scroll = ttk.Scrollbar(card, orient="vertical", command=self.tree.yview)
        h_scroll = ttk.Scrollbar(card, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=v_scroll.set, xscrollcommand=h_scroll.set)
        v_scroll.grid(row=1, column=1, sticky="ns", padx=(0, 16), pady=(0, 16))
        h_scroll.grid(row=2, column=0, sticky="ew", padx=(16, 0), pady=(0, 12))

    def _add_transaction(self):
        self.error_label.configure(text="")
        tx_date_raw = self.date_entry.get().strip()
        category = self.category_var.get()
        description = self.desc_entry.get().strip()
        amount_raw = self.amount_entry.get().strip()

        try:
            parsed_date = date.fromisoformat(tx_date_raw)
        except ValueError:
            self.error_label.configure(text="Date must look like 2026-09-11.")
            return
        try:
            amount = float(amount_raw)
            if amount <= 0:
                raise ValueError
        except ValueError:
            self.error_label.configure(text="Amount must be a number greater than 0.")
            return

        database.add_transaction(
            parsed_date.isoformat(), self.type_var.get(), category, description, amount
        )
        self.amount_entry.delete(0, "end")
        self.desc_entry.delete(0, "end")
        self.refresh()

    def _delete_selected(self):
        selected = self.tree.selection()
        if not selected:
            return
        if not messagebox.askyesno("Delete transaction", "Remove the selected transaction(s)?"):
            return
        for item in selected:
            tx_id = int(self.tree.item(item, "tags")[0])
            database.delete_transaction(tx_id)
        self.refresh()

    def refresh(self):
        theme = self.theme
        for row in self.tree.get_children():
            self.tree.delete(row)
        self.tree.tag_configure("income_row", foreground=theme["blue"])
        self.tree.tag_configure("expense_row", foreground=theme["text"])
        for tx_id, tx_date, tx_type, category, description, amount in database.fetch_all_transactions():
            sign = "+" if tx_type == "income" else "-"
            self.tree.insert(
                "", "end", tags=(str(tx_id), f"{tx_type}_row"),
                values=(tx_date, category, description or "-", f"{sign}${amount:,.2f}"),
            )
