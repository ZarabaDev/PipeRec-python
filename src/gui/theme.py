"""
PipeRec - Professional Dark Theme for Tkinter
Modern dark theme with vibrant accents.
"""

# Color Palette - Professional Dark Theme
COLORS = {
    # Backgrounds
    'bg_dark': '#0f0f0f',
    'bg_surface': '#1a1a1a',
    'bg_elevated': '#252525',
    'bg_card': '#1e1e1e',
    'bg_hover': '#2a2a2a',
    
    # Accents
    'accent_primary': '#ff3b3b',       # Vibrant red for REC
    'accent_secondary': '#3b82f6',      # Blue
    'accent_success': '#10b981',        # Emerald green
    'accent_warning': '#f59e0b',        # Amber
    'accent_error': '#ef4444',          # Red
    
    # Text
    'text_primary': '#ffffff',
    'text_secondary': '#a3a3a3',
    'text_muted': '#525252',
    
    # VU Meter gradient
    'vu_bg': '#262626',
    'vu_low': '#10b981',               # Green
    'vu_mid': '#f59e0b',               # Yellow
    'vu_high': '#ef4444',              # Red
    
    # Borders
    'border': '#333333',
    'border_focus': '#ff3b3b',
}

# Font settings
FONTS = {
    'family': 'Segoe UI',
    'family_mono': 'Consolas',
    'size_title': 20,
    'size_heading': 14,
    'size_body': 11,
    'size_small': 9,
    'size_timer': 48,
}

# Dimensions
DIMENSIONS = {
    'window_width': 380,
    'window_height': 520,
    'padding_large': 20,
    'padding_medium': 12,
    'padding_small': 8,
    'border_radius': 8,
    'button_height': 50,
    'vu_height': 24,
    'vu_segments': 20,
}

# Animation timings (ms)
ANIMATIONS = {
    'vu_update': 50,
    'timer_update': 100,
    'pulse_speed': 600,
}


def configure_ttk_styles(style):
    """Configure ttk styles for dark theme."""
    
    # General
    style.configure('.',
        background=COLORS['bg_dark'],
        foreground=COLORS['text_primary'],
        font=(FONTS['family'], FONTS['size_body'])
    )
    
    # Frame
    style.configure('TFrame', background=COLORS['bg_dark'])
    style.configure('Card.TFrame', background=COLORS['bg_card'])
    style.configure('Surface.TFrame', background=COLORS['bg_surface'])
    
    # Label
    style.configure('TLabel',
        background=COLORS['bg_dark'],
        foreground=COLORS['text_primary'],
        font=(FONTS['family'], FONTS['size_body'])
    )
    style.configure('Title.TLabel',
        font=(FONTS['family'], FONTS['size_title'], 'bold'),
        foreground=COLORS['text_primary']
    )
    style.configure('Subtitle.TLabel',
        font=(FONTS['family'], FONTS['size_small']),
        foreground=COLORS['text_muted']
    )
    style.configure('Timer.TLabel',
        font=(FONTS['family_mono'], FONTS['size_timer'], 'bold'),
        foreground=COLORS['text_primary']
    )
    style.configure('Status.TLabel',
        font=(FONTS['family'], FONTS['size_body']),
        foreground=COLORS['text_secondary']
    )
    style.configure('Card.TLabel', background=COLORS['bg_card'])
    
    # Button base
    style.configure('TButton',
        background=COLORS['bg_elevated'],
        foreground=COLORS['text_primary'],
        font=(FONTS['family'], FONTS['size_heading'], 'bold'),
        borderwidth=0,
        focusthickness=0,
        padding=(20, 12)
    )
    style.map('TButton',
        background=[('active', COLORS['bg_hover']), ('disabled', COLORS['bg_surface'])],
        foreground=[('disabled', COLORS['text_muted'])]
    )
    
    # Combobox
    style.configure('TCombobox',
        background=COLORS['bg_elevated'],
        foreground=COLORS['text_primary'],
        fieldbackground=COLORS['bg_elevated'],
        arrowcolor=COLORS['text_secondary'],
        borderwidth=1,
        padding=8
    )
    style.map('TCombobox',
        fieldbackground=[('readonly', COLORS['bg_elevated'])],
        selectbackground=[('readonly', COLORS['accent_primary'])],
        selectforeground=[('readonly', COLORS['text_primary'])]
    )
    
    # Separator
    style.configure('TSeparator', background=COLORS['border'])
