# settings.py

# ==========================================
# WINDOW & DISPLAY SETTINGS
# ==========================================
WIDTH = 1280
HEIGHT = 720
TARGET_FPS = 60
TITLE = "Geometry Dash Clone - Flat Vector"

# ==========================================
# GAMEPLAY CONSTANTS (Base values, mostly overwritten by Difficulty)
# ==========================================
GRAVITY = 3500.0          # pixels per second squared
JUMP_FORCE = -1150.0       # jump impulse
ROTATION_SPEED = 450.0    # degrees per second

# Ship Physics
SHIP_GRAVITY = 1600.0
FLIGHT_FORCE = 3000.0
SHIP_MAX_VEL = 600.0

# ==========================================
# DIFFICULTY SETTINGS
# ==========================================
DIFFICULTIES = [
    {"name": "EASY", "speed": 350.0, "density": 0.5, "block": (100, 255, 100), "spike": (200, 255, 200),
     "gravity": 3500.0, "jump_force": -1150.0, "ship_gravity": 1600.0, "flight_force": 3000.0, "menu_color": (30, 80, 150)},
    {"name": "NORMAL", "speed": 450.0, "density": 0.8, "block": (255, 40, 100), "spike": (225, 225, 225),
     "gravity": 3800.0, "jump_force": -1200.0, "ship_gravity": 1800.0, "flight_force": 3300.0, "menu_color": (35, 100, 50)},
    {"name": "HARD", "speed": 600.0, "density": 1.2, "block": (255, 50, 50), "spike": (255, 100, 100),
     "gravity": 4200.0, "jump_force": -1300.0, "ship_gravity": 2000.0, "flight_force": 3600.0, "menu_color": (150, 40, 20)},
    {"name": "INTENSE", "speed": 750.0, "density": 1.6, "block": (255, 120, 30), "spike": (255, 150, 50),
     "gravity": 4800.0, "jump_force": -1400.0, "ship_gravity": 2300.0, "flight_force": 4000.0, "menu_color": (100, 20, 80)},
    {"name": "EXTREME", "speed": 900.0, "density": 2.0, "block": (255, 0, 0), "spike": (255, 50, 50),
     "gravity": 5500.0, "jump_force": -1500.0, "ship_gravity": 2600.0, "flight_force": 4500.0, "menu_color": (120, 0, 0)}
]

# 5 Levels corresponding to 5 different static maps
LEVEL_SEEDS = [42, 100, 666, 777, 999]

LEVEL_THEMES = [
    {"bg": (28, 69, 135), "ground": (20, 50, 100), "line": (255, 255, 255)}, # Map 1: Blue
    {"bg": (35, 100, 50), "ground": (20, 75, 30), "line": (100, 255, 100)},  # Map 2: Green
    {"bg": (100, 30, 100), "ground": (70, 20, 70), "line": (255, 100, 255)}, # Map 3: Purple
    {"bg": (150, 60, 20), "ground": (100, 40, 15), "line": (255, 200, 0)},   # Map 4: Orange
    {"bg": (30, 30, 40), "ground": (20, 20, 25), "line": (255, 50, 50)}      # Map 5: Dark
]

# ==========================================
# FLAT VECTOR COLOR PALETTE (RGB) DEFAULT FALLBACKS
# ==========================================
BG_COLOR = (28, 69, 135)        # Deep blue background
GROUND_COLOR = (20, 50, 100)   # Darker blue ground
GROUND_LINE_COLOR = (255, 255, 255) # White top border for ground
PLAYER_COLOR = (255, 255, 0)   # GD bright yellow
PLAYER_INNER_COLOR = (0, 200, 255) # Cyan inner square
BLOCK_COLOR = (255, 40, 100)  # Pinkish red blocks
BLOCK_INNER_COLOR = (40, 40, 40) # Dark center
SPIKE_COLOR = (225, 225, 225)   # White/grey spikes
TEXT_COLOR = (255, 255, 255)   # Solid white text
BORDER_COLOR = (0, 0, 0)       # Solid black 2px borders

# ==========================================
# LAYOUT & RENDERING
# ==========================================
BORDER_THICKNESS = 2
TILE_SIZE = 68             # Base grid size (smaller for easier gameplay)
PLAYER_SIZE = 68           # Player matches tile size
