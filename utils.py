import pygame  # type: ignore
from settings import BORDER_COLOR, BORDER_THICKNESS  # type: ignore

def draw_flat_rect(surface, color, rect):
    """
    Draws a flat solid rectangle with a strict black border.
    Complies with the strict Flat Vector aesthetic.
    """
    # 1. Fill the solid internal color
    pygame.draw.rect(surface, color, rect)
    
    # 2. Draw the strict 2px solid black border around it
    pygame.draw.rect(surface, BORDER_COLOR, rect, width=BORDER_THICKNESS)
