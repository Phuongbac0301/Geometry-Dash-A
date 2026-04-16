import pygame  # type: ignore
import math
from settings import BLOCK_COLOR, BLOCK_INNER_COLOR, SPIKE_COLOR, TILE_SIZE, BORDER_COLOR, BORDER_THICKNESS  # type: ignore
from utils import draw_flat_rect  # type: ignore

class Block:
    def __init__(self, x, y, color=BLOCK_COLOR, inner_color=BLOCK_INNER_COLOR):
        self.x = x
        self.y = y
        self.width = TILE_SIZE
        self.height = TILE_SIZE
        self.rect = pygame.Rect(self.x, self.y, self.width, self.height)
        self.color = color
        self.inner_color = inner_color

    def draw(self, surface, camera_scroll_x):
        screen_x = self.x - camera_scroll_x
        if -self.width * 2 <= screen_x <= surface.get_width():
            dist_from_right = surface.get_width() - screen_x
            is_fading = 0 <= dist_from_right < 150
            if is_fading:
                prog = dist_from_right / 150.0
                y_offset = max(0, 50 * (1.0 - prog))
                alpha = int(255 * prog)
                t_surf = pygame.Surface((self.width + 4, self.height + 4), pygame.SRCALPHA)
                dx, dy = 2, 2
            else:
                y_offset = 0
                alpha = 255
                t_surf = surface
                dx, dy = screen_x, self.y
                
            draw_rect = pygame.Rect(dx, dy, self.width, self.height)
            draw_flat_rect(t_surf, self.color, draw_rect)
            
            inner_hl = pygame.Rect(dx + 2, dy + 2, self.width - 4, self.height - 4)
            pygame.draw.rect(t_surf, (255, 255, 255), inner_hl, 1)
            
            inner_center = pygame.Rect(dx + 10, dy + 10, self.width - 20, self.height - 20)
            draw_flat_rect(t_surf, self.inner_color, inner_center)
            pygame.draw.rect(t_surf, BORDER_COLOR, inner_center, 2)
            
            pygame.draw.rect(t_surf, BORDER_COLOR, draw_rect, BORDER_THICKNESS)
            
            if is_fading:
                t_surf.set_alpha(alpha)
                surface.blit(t_surf, (screen_x - 2, self.y + y_offset - 2))

class Portal:
    def __init__(self, x, y, mode):
        self.x = x
        self.y = y - TILE_SIZE * 2 # Portals are tall
        self.width = TILE_SIZE * 1.5
        self.height = TILE_SIZE * 3
        self.mode = mode # "SHIP" or "CUBE"
        self.color = (255, 100, 255) if mode == "SHIP" else (100, 255, 100)
        self.rect = pygame.Rect(self.x, self.y, self.width, self.height)
        self.angle = 0.0
        
    def draw(self, surface, camera_scroll_x, dt=0.0):
        screen_x = self.x - camera_scroll_x
        if -self.width * 3 <= screen_x <= surface.get_width():
            self.angle += 180 * dt
            
            # Fade-in check
            dist_from_right = surface.get_width() - screen_x
            is_fading = 0 <= dist_from_right < 150
            if is_fading:
                prog = dist_from_right / 150.0
                alpha = int(255 * prog)
                # target surface big enough for rotation
                t_surf = pygame.Surface((300, 300), pygame.SRCALPHA)
                t_surf.set_alpha(alpha)
                dx, dy = 150, 150
            else:
                t_surf = surface
                dx, dy = screen_x + self.width / 2, self.y + self.height / 2
                
            # Draw Epic Vortex (Spinning overlapping ellipses)
            for i in range(4):
                # We draw by creating a local surface for the ellipse, rotating it, and blitting
                ang_offset = self.angle + i * 45
                
                # Base ellipse logic (since pygame rotates bounding boxes, we create a rect)
                # However, drawing rotated ellipses natively in pure pygame is tricky without surfaces.
                # A fast trick is to draw polygons that circle around
                pass
            
            # Simple Pygame polygon vortex trick:
            points_outer = []
            points_inner = []
            num_points = 20
            for i in range(num_points):
                r_ang = math.radians(self.angle + i * (360/num_points))
                
                # Outer ring distorts into an oval
                rx = math.cos(r_ang) * (self.width / 2)
                ry = math.sin(r_ang) * (self.height / 2) + math.sin(r_ang*2 + self.angle*0.05) * 5
                
                # Inner ring
                irx = math.cos(r_ang - 0.5) * (self.width / 3)
                iry = math.sin(r_ang - 0.5) * (self.height / 3)
                
                points_outer.append((dx + rx, dy + ry))
                points_inner.append((dx + irx, dy + iry))
                
            pygame.draw.polygon(t_surf, self.color, points_outer, 6)
            pygame.draw.polygon(t_surf, BORDER_COLOR, points_outer, 2)
            pygame.draw.polygon(t_surf, (255, 255, 255), points_inner, 3)
            
            # Draw ambient floating sparks from center
            for i in range(6):
                spark_ang = math.radians(self.angle * 2 + i * 60)
                pulse = (math.sin(self.angle * 0.1 + i) + 1) * 15 + 10
                sx = dx + math.cos(spark_ang) * pulse
                sy = dy + math.sin(spark_ang) * pulse
                pygame.draw.circle(t_surf, (255, 255, 255), (int(sx), int(sy)), 2)
                
            if is_fading:
                surface.blit(t_surf, (screen_x + self.width/2 - 150, self.y + self.height/2 - 150))

class Spike:
    def __init__(self, x, y, color=SPIKE_COLOR, inner_color=(150, 150, 150), pointing_down=False):
        self.x = x
        self.y = y
        self.width = TILE_SIZE * 0.85
        self.height = TILE_SIZE * 0.85
        self.x = x + TILE_SIZE * 0.075
        self.y = y + TILE_SIZE * 0.15 if not pointing_down else y
        self.rect = pygame.Rect(self.x, self.y, self.width, self.height)
        self.color = color
        self.inner_color = inner_color
        self.pointing_down = pointing_down
        
        # Hitbox (35% smaller than visual size for VERY forgiving gameplay)
        hitbox_margin_x = self.width * 0.35
        hitbox_margin_y = self.height * 0.35
        self.hitbox = pygame.Rect(
            self.x + hitbox_margin_x,
            self.y + hitbox_margin_y,
            self.width - 2 * hitbox_margin_x,
            self.height - hitbox_margin_y
        )

    def draw(self, surface, camera_scroll_x):
        screen_x = self.x - camera_scroll_x
        if -self.width * 2 <= screen_x <= surface.get_width():
            dist_from_right = surface.get_width() - screen_x
            is_fading = 0 <= dist_from_right < 150
            if is_fading:
                prog = dist_from_right / 150.0
                y_offset = max(0, 50 * (1.0 - prog))
                if getattr(self, 'pointing_down', False): y_offset = -y_offset
                alpha = int(255 * prog)
                t_surf = pygame.Surface((self.width + 4, self.height + 4), pygame.SRCALPHA)
                dx, dy = 2, 2
            else:
                y_offset = 0
                alpha = 255
                t_surf = surface
                dx, dy = screen_x, self.y
            
            if not getattr(self, 'pointing_down', False):
                p1 = (dx, dy + self.height)
                p2 = (dx + self.width / 2, dy)
                p3 = (dx + self.width, dy + self.height)
                points = [p1, p2, p3]
                pygame.draw.polygon(t_surf, self.color, points)
                
                ip1 = (dx + 8, dy + self.height - 5)
                ip2 = (dx + self.width / 2, dy + 12)
                ip3 = (dx + self.width - 8, dy + self.height - 5)
                pygame.draw.polygon(t_surf, self.inner_color, [ip1, ip2, ip3])
                pygame.draw.line(t_surf, BORDER_COLOR, p1, p3, BORDER_THICKNESS + 2)
                pygame.draw.polygon(t_surf, BORDER_COLOR, points, width=BORDER_THICKNESS)
            else:
                p1 = (dx, dy)
                p2 = (dx + self.width / 2, dy + self.height)
                p3 = (dx + self.width, dy)
                points = [p1, p2, p3]
                pygame.draw.polygon(t_surf, self.color, points)
                
                ip1 = (dx + 8, dy + 5)
                ip2 = (dx + self.width / 2, dy + self.height - 12)
                ip3 = (dx + self.width - 8, dy + 5)
                pygame.draw.polygon(t_surf, self.inner_color, [ip1, ip2, ip3])
                pygame.draw.line(t_surf, BORDER_COLOR, p1, p3, BORDER_THICKNESS + 2)
                pygame.draw.polygon(t_surf, BORDER_COLOR, points, width=BORDER_THICKNESS)
                
            if is_fading:
                t_surf.set_alpha(alpha)
                surface.blit(t_surf, (screen_x - 2, self.y + y_offset - 2))

class Sawblade:
    def __init__(self, x, y):
        self.x = x + TILE_SIZE / 2
        self.y = y + TILE_SIZE / 2
        self.radius = TILE_SIZE * 0.7  # Visually a bit bigger than tile
        self.hitbox_radius = self.radius * 0.5  # Forgiving hitbox (0.5 instead of 0.7)
        self.angle = 0.0
        self.color = (150, 150, 150)
        
    def draw(self, surface, camera_scroll_x, dt):
        screen_x = self.x - camera_scroll_x
        if -self.radius * 2 <= screen_x <= surface.get_width() + self.radius:
            self.angle += 360 * dt
            
            dist_from_right = surface.get_width() - screen_x
            is_fading = 0 <= dist_from_right < 150
            if is_fading:
                prog = dist_from_right / 150.0
                y_offset = max(0, 50 * (1.0 - prog))
                if self.y < 300: y_offset = -y_offset
                alpha = int(255 * prog)
                # target surface
                t_surf = pygame.Surface((self.radius * 2 + 20, self.radius * 2 + 20), pygame.SRCALPHA)
                dx, dy = self.radius + 10, self.radius + 10
            else:
                y_offset = 0
                alpha = 255
                t_surf = surface
                dx, dy = screen_x, self.y
                
            # Draw Sawblade base
            pygame.draw.circle(t_surf, self.color, (int(dx), int(dy)), int(self.radius))
            pygame.draw.circle(t_surf, BORDER_COLOR, (int(dx), int(dy)), int(self.radius), BORDER_THICKNESS)
            
            # Draw Teeth
            num_teeth = 12
            for i in range(num_teeth):
                rad = math.radians(self.angle + i * (360 / num_teeth))
                cx = dx + math.cos(rad) * self.radius
                cy = dy + math.sin(rad) * self.radius
                px = dx + math.cos(rad) * (self.radius + 8)
                py = dy + math.sin(rad) * (self.radius + 8)
                
                left_rad = math.radians(self.angle + i * (360 / num_teeth) - 10)
                right_rad = math.radians(self.angle + i * (360 / num_teeth) + 10)
                
                lx = dx + math.cos(left_rad) * self.radius
                ly = dy + math.sin(left_rad) * self.radius
                rx = dx + math.cos(right_rad) * self.radius
                ry = dy + math.sin(right_rad) * self.radius
                
                pygame.draw.polygon(t_surf, self.color, [(cx, cy), (px, py), (rx, ry)])
                pygame.draw.polygon(t_surf, BORDER_COLOR, [(cx, cy), (px, py), (rx, ry)], 2)
            
            # Inner circle pattern 
            pygame.draw.circle(t_surf, (100, 100, 100), (int(dx), int(dy)), int(self.radius * 0.5))
            pygame.draw.circle(t_surf, BORDER_COLOR, (int(dx), int(dy)), int(self.radius * 0.5), 2)
            pygame.draw.circle(t_surf, (255, 255, 255), (int(dx), int(dy)), int(self.radius * 0.15))
            
            if is_fading:
                t_surf.set_alpha(alpha)
                surface.blit(t_surf, (screen_x - self.radius - 10, self.y - self.radius - 10 + y_offset))

class JumpOrb:
    def __init__(self, x, y):
        # Center of the tile
        self.x = x + TILE_SIZE / 2
        self.y = y + TILE_SIZE / 2
        self.radius = 18
        self.trigger_radius = 45 # Easy to hit
        self.color = (255, 200, 0)
        self.pulse = 0.0
        
    def draw(self, surface, camera_scroll_x, dt):
        screen_x = self.x - camera_scroll_x
        if -self.trigger_radius * 2 <= screen_x <= surface.get_width() + self.trigger_radius:
            self.pulse += 5 * dt
            
            dist_from_right = surface.get_width() - screen_x
            is_fading = 0 <= dist_from_right < 150
            if is_fading:
                prog = dist_from_right / 150.0
                y_offset = max(0, 50 * (1.0 - prog))
                alpha = int(255 * prog)
                # glow radius is up to radius+5+4 = ~27
                t_surf = pygame.Surface((60, 60), pygame.SRCALPHA)
                dx, dy = 30, 30
            else:
                y_offset = 0
                alpha = 255
                t_surf = surface
                dx, dy = screen_x, self.y
                
            # Glowing outline
            glow_rad = self.radius + 5 + math.sin(self.pulse) * 4
            pygame.draw.circle(t_surf, (self.color[0], self.color[1], max(0, self.color[2] - 100)), (int(dx), int(dy)), int(glow_rad), 3)
            
            # Core
            pygame.draw.circle(t_surf, self.color, (int(dx), int(dy)), self.radius)
            pygame.draw.circle(t_surf, (255, 255, 255), (int(dx), int(dy)), int(self.radius * 0.6))
            pygame.draw.circle(t_surf, BORDER_COLOR, (int(dx), int(dy)), self.radius, BORDER_THICKNESS)
            
            if is_fading:
                t_surf.set_alpha(alpha)
                surface.blit(t_surf, (screen_x - 30, self.y - 30 + y_offset))

class Star:
    def __init__(self, x, y):
        self.x = x + TILE_SIZE / 2
        self.y = y + TILE_SIZE / 2
        self.radius = 15
        self.trigger_radius = 25
        self.angle = 0.0
        self.color = (255, 255, 0)
        self.collected = False
        
    def draw(self, surface, camera_scroll_x, dt):
        if self.collected: return
        screen_x = self.x - camera_scroll_x
        if -self.radius * 2 <= screen_x <= surface.get_width() + self.radius:
            self.angle += 120 * dt
            
            dist_from_right = surface.get_width() - screen_x
            is_fading = 0 <= dist_from_right < 150
            if is_fading:
                prog = dist_from_right / 150.0
                y_offset = max(0, 50 * (1.0 - prog))
                if self.y < 300: y_offset = -y_offset
                alpha = int(255 * prog)
                t_surf = pygame.Surface((40, 40), pygame.SRCALPHA)
                dx, dy = 20, 20
            else:
                y_offset = 0
                alpha = 255
                t_surf = surface
                dx, dy = screen_x, self.y
                
            points = []
            for i in range(10):
                r = self.radius if i % 2 == 0 else self.radius * 0.4
                theta = math.radians(self.angle + i * 36)
                points.append((dx + math.cos(theta) * r, dy + math.sin(theta) * r))
                
            pygame.draw.polygon(t_surf, self.color, points)
            pygame.draw.polygon(t_surf, BORDER_COLOR, points, 2)
            
            if is_fading:
                t_surf.set_alpha(alpha)
                surface.blit(t_surf, (screen_x - 20, self.y - 20 + y_offset))

