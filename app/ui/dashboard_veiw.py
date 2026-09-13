"""
dashboard_view.py — the landing page: headline numbers for the selected
month, plus a category donut and a budget-vs-actual chart underneath.
"""

import calendar
from datetime import date

import customtkinter as ctk
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

from .. import charts, config, data_processing as dp, database
from . import components


class DashboardView(ctk.CTkFrame):
    def __init__(self, parent, theme):
        super().__init__(parent, fg_color=theme["bg"])
        self.theme = theme
        today = date.today()
        self.year, self.month = today.year, today.month

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)

        self._build_header()
        self._build_stat_row()
        self._build_charts_row()
        self.refresh()

    def _build_header(self):
        theme = self.theme
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.grid(row=0, column=0, sticky="ew", padx=28, pady=(26, 6))
        header.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(
            header, text="Dashboard", font=config.FONTS["h1"], text_color=theme["text"]
        ).grid(row=0, column=0, sticky="w")

        nav = ctk.CTkFrame(header, fg_color="transparent")
        nav.grid(row=0, column=2, sticky="e")
        ctk.CTkButton(
            nav, text="<", width=32, command=self._prev_month,
            fg_color=theme["surface"], hover_color=theme["surface_alt"], text_color=theme["text"],
        ).pack(side="left", padx=2)
        self.month_label = ctk.CTkLabel(
            nav, text="", font=config.FONTS["h3"], text_color=theme["text"], width=140
        )
        self.month_label.pack(side="left", padx=6)
        ctk.CTkButton(
            nav, text=">", width=32, command=self._next_month,
            fg_color=theme["surface"], hover_color=theme["surface_alt"], text_color=theme["text"],
        ).pack(side="left", padx=2)

    def _build_stat_row(self):
        self.stats_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.stats_frame.grid(row=1, column=0, sticky="ew", padx=24, pady=6)
        for i in range(4):
            self.stats_frame.grid_columnconfigure(i, weight=1)

    def _build_charts_row(self):
        theme = self.theme
        row = ctk.CTkFrame(self, fg_color="transparent")
        row.grid(row=2, column=0, sticky="nsew", padx=24, pady=(10, 20))
        row.grid_columnconfigure(0, weight=3)
        row.grid_columnconfigure(1, weight=4)
        row.grid_rowconfigure(0, weight=1)

        self.donut_card = ctk.CTkFrame(row, corner_radius=12, fg_color=theme["surface"])
        self.donut_card.grid(row=0, column=0, sticky="nsew", padx=(0, 10))
        ctk.CTkLabel(
            self.donut_card, text="Where it went", font=config.FONTS["h3"], text_color=theme["text"]
        ).pack(anchor="w", padx=18, pady=(16, 0))
        self.donut_holder = ctk.CTkFrame(self.donut_card, fg_color="transparent")
        self.donut_holder.pack(fill="both", expand=True, padx=8, pady=8)

        self.budget_card = ctk.CTkFrame(row, corner_radius=12, fg_color=theme["surface"])
        self.budget_card.grid(row=0, column=1, sticky="nsew", padx=(10, 0))
        ctk.CTkLabel(
            self.budget_card, text="Budget vs. actual", font=config.FONTS["h3"], text_color=theme["text"]
        ).pack(anchor="w", padx=18, pady=(16, 0))
        self.budget_holder = ctk.CTkFrame(self.budget_card, fg_color="transparent")
        self.budget_holder.pack(fill="both", expand=True, padx=8, pady=8)

    def _prev_month(self):
        self.month -= 1
        if self.month == 0:
            self.month, self.year = 12, self.year - 1
        self.refresh()

    def _next_month(self):
        self.month += 1
        if self.month == 13:
            self.month, self.year = 1, self.year + 1
        self.refresh()

    def refresh(self):
        theme = self.theme
        self.month_label.configure(text=f"{calendar.month_name[self.month]} {self.year}")

        df = dp.load_transactions_df()
        income, expense, net = dp.month_summary(df, self.year, self.month)
        budgets = database.fetch_budgets()
        total_budget = sum(budgets.values())
        savings = dp.savings_rate(income, expense)

        for w in self.stats_frame.winfo_children():
            w.destroy()

        cards = [
            ("Income", f"${income:,.0f}", "blue", ""),
            (
                "Expenses",
                f"${expense:,.0f}",
                "coral" if total_budget and expense > total_budget else "accent",
                f"of ${total_budget:,.0f} budgeted" if total_budget else "no budget set",
            ),
            ("Net", f"${net:,.0f}", "accent" if net >= 0 else "coral", ""),
            ("Savings rate", f"{savings:,.0f}%", "amber" if savings < 15 else "accent", ""),
        ]
        for i, (title, value, key, subtitle) in enumerate(cards):
            card = components.StatCard(self.stats_frame, theme, title, value, key, subtitle)
            card.grid(row=0, column=i, sticky="ew", padx=6)

        for holder in (self.donut_holder, self.budget_holder):
            for w in holder.winfo_children():
                w.destroy()

        breakdown = dp.category_breakdown(df, self.year, self.month)
        fig1 = charts.category_donut(breakdown, theme)
        canvas1 = FigureCanvasTkAgg(fig1, master=self.donut_holder)
        canvas1.draw()
        canvas1.get_tk_widget().pack(fill="both", expand=True)

        status = dp.budget_status(df, budgets, self.year, self.month)
        fig2 = charts.budget_bars(status, theme)
        canvas2 = FigureCanvasTkAgg(fig2, master=self.budget_holder)
        canvas2.draw()
        canvas2.get_tk_widget().pack(fill="both", expand=True)
