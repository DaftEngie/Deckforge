"""DeckForge: tune demanding PC games for the Steam Deck in handheld mode."""

__version__ = "0.0.1"

# Handheld quality target (docs/QUALITY_TARGET.md): 45 fps native.
TARGET_FPS = 45
FRAME_BUDGET_MS = round(1000 / TARGET_FPS, 1)
