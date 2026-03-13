"""
PipeRec - Minimal utilitarian console theme.
"""

COLORS = {
    "bg_dark": "#07090d",
    "bg_surface": "#121722",
    "bg_elevated": "#171d29",
    "bg_card": "#0f141d",
    "bg_hover": "#1b2230",
    "bg_shell": "#0b1018",
    "bg_shell_soft": "#141b27",
    "accent_primary": "#ff4d42",
    "accent_secondary": "#45b3ff",
    "accent_success": "#3ddc97",
    "accent_warning": "#ffb84d",
    "accent_error": "#ff6b6b",
    "text_primary": "#f5f7fb",
    "text_secondary": "#9ca8bc",
    "text_muted": "#576175",
    "vu_bg": "#1c2432",
    "vu_low": "#3ddc97",
    "vu_mid": "#45b3ff",
    "vu_high": "#ff4d42",
    "meter_on": "#3ddc97",
    "meter_off": "#1b2230",
    "border": "#252f40",
    "border_soft": "#1c2432",
}

FONTS = {
    "family": "Segoe UI",
    "family_mono": "Consolas",
    "size_title": 14,
    "size_heading": 11,
    "size_body": 10,
    "size_small": 9,
    "size_timer": 40,
}

DIMENSIONS = {
    "window_width": 430,
    "window_height": 455,
    "padding_large": 14,
    "padding_medium": 10,
    "padding_small": 6,
    "border_radius": 10,
    "button_height": 44,
    "vu_height": 14,
    "vu_segments": 18,
}

ANIMATIONS = {
    "vu_update": 50,
    "timer_update": 100,
    "pulse_speed": 640,
}


def configure_ttk_styles(style):
    style.configure(
        ".",
        background=COLORS["bg_dark"],
        foreground=COLORS["text_primary"],
        font=(FONTS["family"], FONTS["size_body"]),
    )
    style.configure("TFrame", background=COLORS["bg_dark"])
    style.configure("Card.TFrame", background=COLORS["bg_card"])
    style.configure("Surface.TFrame", background=COLORS["bg_surface"])
    style.configure(
        "TLabel",
        background=COLORS["bg_dark"],
        foreground=COLORS["text_primary"],
        font=(FONTS["family"], FONTS["size_body"]),
    )
    style.configure("Card.TLabel", background=COLORS["bg_card"])
    style.configure(
        "Status.TLabel",
        background=COLORS["bg_surface"],
        foreground=COLORS["text_secondary"],
        font=(FONTS["family"], FONTS["size_body"]),
    )
    style.configure(
        "TCombobox",
        background=COLORS["bg_elevated"],
        foreground=COLORS["text_primary"],
        fieldbackground=COLORS["bg_elevated"],
        arrowcolor=COLORS["text_secondary"],
        borderwidth=1,
        padding=7,
    )
    style.map(
        "TCombobox",
        fieldbackground=[("readonly", COLORS["bg_elevated"])],
        selectbackground=[("readonly", COLORS["accent_secondary"])],
        selectforeground=[("readonly", COLORS["text_primary"])],
    )
