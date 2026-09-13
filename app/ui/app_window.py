import customtkinter as ctk

from .. import config
from . import components
from .budget_view import BudgetView
from .dashboard_view import DashboardView
from .reports_view import ReportsView
from .settings_view import SettingsView
from .transactions_view import TransactionsView


class AppWindow(ctk.CTkFrame):
    NAV_ITEMS = [
        ("Dashboard", DashboardView),
        ("Transactions", TransactionsView),
        ("Budgets", BudgetView),
        ("Reports", ReportsView),
        ("Settings", SettingsView),
    ]

    def __init__(self, master, theme_name, on_logout, on_appearance_change=None):
        super().__init__(master, fg_color="transparent")
        self.theme_name = theme_name
        self.theme = config.PALETTE.get(theme_name, config.PALETTE["dark"])
        self.on_logout = on_logout
        self.on_appearance_change = on_appearance_change
        self.pack(fill="both", expand=True)

        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self.views = {}
        self.nav_buttons = {}
        self._build_sidebar()

        self.content = ctk.CTkFrame(self, fg_color=self.theme["bg"])
        self.content.grid(row=0, column=1, sticky="nsew")
        self.content.grid_columnconfigure(0, weight=1)
        self.content.grid_rowconfigure(0, weight=1)

        self._show("Dashboard")

    def _build_sidebar(self):
        theme = self.theme
        sidebar = ctk.CTkFrame(self, width=220, corner_radius=0, fg_color=theme["surface"])
        sidebar.grid(row=0, column=0, sticky="nsw")
        sidebar.grid_propagate(False)
        sidebar.grid_rowconfigure(len(self.NAV_ITEMS) + 2, weight=1)

        ctk.CTkLabel(
            sidebar, text=config.APP_NAME, font=config.FONTS["h2"], text_color=theme["text"]
        ).grid(row=0, column=0, sticky="w", padx=22, pady=(26, 0))
        ctk.CTkLabel(
            sidebar, text="personal finance", font=config.FONTS["small"], text_color=theme["text_muted"]
        ).grid(row=1, column=0, sticky="w", padx=22, pady=(0, 22))

        for i, (name, _) in enumerate(self.NAV_ITEMS, start=2):
            btn = components.SidebarButton(sidebar, theme, name, command=lambda n=name: self._show(n))
            btn.grid(row=i, column=0, sticky="ew", padx=10, pady=2)
            self.nav_buttons[name] = btn

        footer = ctk.CTkFrame(sidebar, fg_color="transparent")
        footer.grid(row=len(self.NAV_ITEMS) + 3, column=0, sticky="sew", padx=14, pady=18)
        ctk.CTkButton(
            footer, text="Log out", command=self.on_logout,
            fg_color="transparent", border_width=1, border_color=theme["border"],
            text_color=theme["text_muted"], hover_color=theme["surface_alt"],
        ).pack(fill="x")

    def _create_view(self, name):
        if name == "Settings":
            return SettingsView(self.content, self.theme, on_appearance_change=self.on_appearance_change)
        view_cls = dict(self.NAV_ITEMS)[name]
        return view_cls(self.content, self.theme)

    def _show(self, name):
        for n, btn in self.nav_buttons.items():
            btn.set_active(n == name)

        for view in self.views.values():
            view.grid_forget()

        if name not in self.views:
            view = self._create_view(name)
            view.grid(row=0, column=0, sticky="nsew")
            self.views[name] = view
        else:
            view = self.views[name]
            view.grid(row=0, column=0, sticky="nsew")
            if hasattr(view, "refresh"):
                view.refresh()
