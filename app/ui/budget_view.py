from datetime import date

import customtkinter as ctk
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

from .. import charts, config, data_processing as dp, database


class BudgetView(ctk.CTkFrame):
    def __init__(self, parent, theme):
        super().__init__(parent, fg_color=theme["bg"])
        self.theme = theme
        self.sliders = {}
        self.value_labels = {}

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)

        header = ctk.CTkFrame(self, fg_color="transparent")
        header.grid(row=0, column=0, sticky="ew", padx=28, pady=(26, 6))
        header.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(
            header, text="Budgets", font=config.FONTS["h1"], text_color=theme["text"]
        ).grid(row=0, column=0, sticky="w")
        self.save_btn = ctk.CTkButton(
            header, text="Save changes", command=self._save,
            fg_color=theme["accent"], hover_color=theme["accent_hover"],
        )
        self.save_btn.grid(row=0, column=1, sticky="e")

        self.chart_card = ctk.CTkFrame(self, corner_radius=12, fg_color=theme["surface"])
        self.chart_card.grid(row=1, column=0, sticky="ew", padx=24, pady=(6, 10))
        ctk.CTkLabel(
            self.chart_card, text="This month so far", font=config.FONTS["h3"], text_color=theme["text"]
        ).pack(anchor="w", padx=18, pady=(16, 0))
        self.chart_holder = ctk.CTkFrame(self.chart_card, fg_color="transparent", height=220)
        self.chart_holder.pack(fill="both", expand=True, padx=8, pady=8)

        self.sliders_scroll = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.sliders_scroll.grid(row=2, column=0, sticky="nsew", padx=24, pady=(0, 24))
        self.sliders_scroll.grid_columnconfigure(0, weight=1)

        self._build_sliders()
        self.refresh()

    def _build_sliders(self):
        theme = self.theme
        budgets = database.fetch_budgets()
        for i, category in enumerate(config.EXPENSE_CATEGORIES):
            current = budgets.get(category, 0.0)
            row = ctk.CTkFrame(self.sliders_scroll, corner_radius=10, fg_color=theme["surface"])
            row.grid(row=i, column=0, sticky="ew", pady=5)
            row.grid_columnconfigure(0, weight=1)

            top = ctk.CTkFrame(row, fg_color="transparent")
            top.grid(row=0, column=0, sticky="ew", padx=16, pady=(12, 0))
            top.grid_columnconfigure(0, weight=1)
            ctk.CTkLabel(
                top, text=category, font=config.FONTS["body"], text_color=theme["text"]
            ).grid(row=0, column=0, sticky="w")
            value_label = ctk.CTkLabel(
                top, text=f"${current:,.0f} / mo", font=config.FONTS["mono"], text_color=theme["accent"]
            )
            value_label.grid(row=0, column=1, sticky="e")
            self.value_labels[category] = value_label

            ceiling = max(500, int(round(current * 2, -2)) or 500)
            slider = ctk.CTkSlider(
                row, from_=0, to=ceiling, number_of_steps=max(1, int(ceiling // 10)),
                progress_color=theme["accent"], button_color=theme["accent"],
                button_hover_color=theme["accent_hover"],
                command=lambda v, c=category: self._on_slide(c, v),
            )
            slider.set(current)
            slider.grid(row=1, column=0, sticky="ew", padx=16, pady=(6, 14))
            self.sliders[category] = slider

    def _on_slide(self, category, value):
        self.value_labels[category].configure(text=f"${value:,.0f} / mo")

    def _save(self):
        for category, slider in self.sliders.items():
            database.set_budget(category, round(slider.get(), 2))
        self.refresh()
        self.save_btn.configure(text="Saved \u2713")
        self.after(1200, lambda: self.save_btn.configure(text="Save changes"))

    def refresh(self):
        for w in self.chart_holder.winfo_children():
            w.destroy()
        today = date.today()
        df = dp.load_transactions_df()
        budgets = database.fetch_budgets()
        status = dp.budget_status(df, budgets, today.year, today.month)
        fig = charts.budget_bars(status, self.theme, figsize=(9, 2.6))
        canvas = FigureCanvasTkAgg(fig, master=self.chart_holder)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True)
