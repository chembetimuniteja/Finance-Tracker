from datetime import date

import customtkinter as ctk
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

from .. import charts, config, data_processing as dp


class ReportsView(ctk.CTkFrame):
    def __init__(self, parent, theme):
        super().__init__(parent, fg_color=theme["bg"])
        self.theme = theme
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)

        ctk.CTkLabel(
            self, text="Reports", font=config.FONTS["h1"], text_color=theme["text"]
        ).grid(row=0, column=0, sticky="w", padx=28, pady=(26, 6))

        self.trend_card = ctk.CTkFrame(self, corner_radius=12, fg_color=theme["surface"])
        self.trend_card.grid(row=1, column=0, sticky="ew", padx=24, pady=(6, 10))
        ctk.CTkLabel(
            self.trend_card, text="Income vs. expenses \u2014 last 6 months",
            font=config.FONTS["h3"], text_color=theme["text"],
        ).pack(anchor="w", padx=18, pady=(16, 0))
        self.trend_holder = ctk.CTkFrame(self.trend_card, fg_color="transparent")
        self.trend_holder.pack(fill="both", expand=True, padx=8, pady=8)

        self.rank_card = ctk.CTkFrame(self, corner_radius=12, fg_color=theme["surface"])
        self.rank_card.grid(row=2, column=0, sticky="nsew", padx=24, pady=(0, 24))
        ctk.CTkLabel(
            self.rank_card, text="Top categories this month", font=config.FONTS["h3"],
            text_color=theme["text"],
        ).pack(anchor="w", padx=18, pady=(16, 8))
        self.rank_list = ctk.CTkScrollableFrame(self.rank_card, fg_color="transparent")
        self.rank_list.pack(fill="both", expand=True, padx=18, pady=(0, 16))

        self.refresh()

    def refresh(self):
        theme = self.theme
        for w in self.trend_holder.winfo_children():
            w.destroy()
        for w in self.rank_list.winfo_children():
            w.destroy()

        df = dp.load_transactions_df()
        trend = dp.monthly_trend(df, months=6)
        fig = charts.trend_lines(trend, theme)
        canvas = FigureCanvasTkAgg(fig, master=self.trend_holder)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True)

        today = date.today()
        breakdown = dp.category_breakdown(df, today.year, today.month)
        if breakdown.empty:
            ctk.CTkLabel(
                self.rank_list, text="No expenses logged this month yet.",
                text_color=theme["text_muted"], font=config.FONTS["body"],
            ).pack(anchor="w")
            return

        total = breakdown.sum()
        for i, (category, amount) in enumerate(breakdown.head(6).items()):
            row = ctk.CTkFrame(self.rank_list, fg_color="transparent")
            row.pack(fill="x", pady=5)
            row.grid_columnconfigure(1, weight=1)
            color = charts.CAT_PALETTE[i % len(charts.CAT_PALETTE)]

            ctk.CTkLabel(
                row, text=category, font=config.FONTS["body"], text_color=theme["text"],
                width=160, anchor="w",
            ).grid(row=0, column=0, sticky="w")

            bar_bg = ctk.CTkFrame(row, fg_color=theme["border"], height=10, corner_radius=5)
            bar_bg.grid(row=0, column=1, sticky="ew", padx=10)
            pct = (amount / total) if total else 0
            fill = ctk.CTkFrame(bar_bg, fg_color=color, corner_radius=5)
            fill.place(relx=0, rely=0, relwidth=max(0.02, pct), relheight=1)

            ctk.CTkLabel(
                row, text=f"${amount:,.0f}", font=config.FONTS["mono"], text_color=theme["text_muted"],
                width=80, anchor="e",
            ).grid(row=0, column=2, sticky="e")
