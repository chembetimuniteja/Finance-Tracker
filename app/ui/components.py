import customtkinter as ctk

from .. import config


class StatCard(ctk.CTkFrame):
    """A single headline metric: a big monospace figure with a label, and
    a colored left bar that carries meaning (on-track / caution / over) —
    rather than every card sharing one identical decorative accent."""

    def __init__(self, parent, theme, title, value, accent_key="accent", subtitle=""):
        super().__init__(parent, corner_radius=12, fg_color=theme["surface"])
        self.grid_columnconfigure(1, weight=1)

        bar = ctk.CTkFrame(self, width=4, corner_radius=2, fg_color=theme[accent_key])
        bar.grid(row=0, column=0, rowspan=3, sticky="ns", padx=(14, 12), pady=16)

        ctk.CTkLabel(
            self, text=title, font=config.FONTS["small"],
            text_color=theme["text_muted"], anchor="w",
        ).grid(row=0, column=1, sticky="w", pady=(16, 0), padx=(0, 14))

        ctk.CTkLabel(
            self, text=value, font=config.FONTS["figure"],
            text_color=theme["text"], anchor="w",
        ).grid(row=1, column=1, sticky="w", padx=(0, 14))

        ctk.CTkLabel(
            self, text=subtitle, font=config.FONTS["small"],
            text_color=theme["text_muted"], anchor="w", height=16,
        ).grid(row=2, column=1, sticky="w", pady=(0, 16), padx=(0, 14))


class SidebarButton(ctk.CTkFrame):
    """A nav item with a left accent bar that lights up when active — a
    clearer "you are here" signal than a hover-colored background alone."""

    def __init__(self, parent, theme, text, command):
        super().__init__(parent, fg_color="transparent", height=42)
        self.theme = theme
        self.pack_propagate(False)

        # NOTE: the button is deliberately packed rather than gridded with
        # sticky="ew". CTkButton's rounded-corner canvas can fail to draw
        # its fill/text when stretched via grid's sticky mechanism; pack's
        # fill="x" stretches it the same amount without that problem.
        self.indicator = ctk.CTkFrame(self, width=3, fg_color="transparent", corner_radius=0)
        self.indicator.pack(side="left", fill="y")

        self.button = ctk.CTkButton(
            self, text=text, font=config.FONTS["nav"], anchor="w",
            fg_color="transparent", hover_color=theme["surface_alt"],
            text_color=theme["text_muted"], corner_radius=8,
            command=command, height=38,
        )
        self.button.pack(side="left", fill="both", expand=True, padx=(8, 8))

    def set_active(self, active):
        if active:
            self.indicator.configure(fg_color=self.theme["accent"])
            self.button.configure(text_color=self.theme["text"], fg_color=self.theme["surface_alt"])
        else:
            self.indicator.configure(fg_color="transparent")
            self.button.configure(text_color=self.theme["text_muted"], fg_color="transparent")
