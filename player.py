import pygame  # type: ignore
import random
from settings import (  # type: ignore
    PLAYER_SIZE, PLAYER_COLOR, PLAYER_INNER_COLOR, BORDER_COLOR,
    ROTATION_SPEED, SHIP_MAX_VEL
)
from utils import draw_flat_rect  # type: ignore

class Player:
    def __init__(self, x, y, speed=400.0, gravity=3500.0, jump_force=-1150.0, ship_gravity=1600.0, flight_force=3000.0):
        self.x = float(x)
        self.y = float(y)
        self.prev_y = self.y
        self.width = PLAYER_SIZE
        self.height = PLAYER_SIZE
        
        self.y_vel = 0.0
        self.speed = speed
        self.gravity = gravity
        self.jump_force = jump_force
        self.ship_gravity = ship_gravity
        self.flight_force = flight_force
        
        self.is_grounded = False
        self.rotation_angle = 0.0
        
        self.trail = []
        self.exhaust_particles = []
        self.trail_timer = 0.0
        self.mode = "CUBE"
        self.orb_jump_active = False
        
        self.rect = pygame.Rect(self.x, self.y, self.width, self.height)

    def update(self, dt, holding_jump):
        """Updates physics and kinematics."""
        self.prev_y = self.y
        
        self.x += self.speed * dt
        
        if self.mode == "CUBE":
            if holding_jump and self.is_grounded:
                self.y_vel = self.jump_force
                self.is_grounded = False
                
            self.y_vel += self.gravity * dt
            self.y += self.y_vel * dt
            
            if not self.is_grounded:
                self.rotation_angle -= ROTATION_SPEED * dt
                
        elif self.mode == "SHIP":
            if holding_jump:
                self.y_vel -= self.flight_force * dt
                # Exhaust particles
                self.exhaust_particles.append({
                    "x": self.x,
                    "y": self.y + self.height/2,
                    "vx": -400.0 + random.uniform(-60, 60),
                    "vy": 120.0 + random.uniform(-120, 120),
                    "life": 0.4
                })
            else:
                self.y_vel += self.ship_gravity * dt
                
            self.y_vel = max(-SHIP_MAX_VEL, min(SHIP_MAX_VEL, self.y_vel))
            self.y += self.y_vel * dt
            
            # Simple ship rotation
            self.rotation_angle = max(-30.0, min(30.0, -self.y_vel * 0.05))

        # Manage trail
        self.trail_timer -= dt
        if self.trail_timer <= 0:
            self.trail.append([self.x, self.y, self.rotation_angle, 0.4]) # [x, y, angle, lifetime]
            self.trail_timer = 0.05
            
        for t in self.trail:
            t[3] -= dt
        self.trail = [t for t in self.trail if t[3] > 0]
        
        for p in self.exhaust_particles:
            p["x"] += p["vx"] * dt
            p["y"] += p["vy"] * dt
            p["life"] -= dt
        self.exhaust_particles = [p for p in self.exhaust_particles if p["life"] > 0]

        # Reset state; correct state will be dictated by level collision checks
        self.is_grounded = False
        self.orb_jump_active = False
        
        self.rect.x = int(self.x)
        self.rect.y = int(self.y)

    def draw(self, surface, camera_scroll_x):
        # Draw Trail
        for t in self.trail:
            tx, ty, tang, tlife = t
            t_surface = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
            alpha = int((tlife / 0.4) * 100) # Fade out
            pygame.draw.rect(t_surface, (*PLAYER_COLOR[:3], alpha), (0, 0, self.width, self.height))
            
            rotated_t = pygame.transform.rotate(t_surface, tang)
            t_screen_x = tx - camera_scroll_x
            t_rect = rotated_t.get_rect(center=(t_screen_x + self.width/2, ty + self.height/2))
            surface.blit(rotated_t, t_rect.topleft)

        # Draw Exhaust Particles in world space
        for p in self.exhaust_particles:
            if p["life"] > 0:
                p_screen_x = p["x"] - camera_scroll_x
                p_rect = pygame.Rect(p_screen_x, p["y"], 6, 6)
                color = (255, random.randint(100, 200), 0) # Fire
                pygame.draw.rect(surface, color, p_rect)

        # Draw Main Player
        player_surface = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        local_rect = pygame.Rect(0, 0, self.width, self.height)
        
        # Base Shape
        if self.mode == "CUBE":
            draw_flat_rect(player_surface, PLAYER_COLOR, local_rect)
            pygame.draw.rect(player_surface, BORDER_COLOR, local_rect, 2) # Outer border
            
            # Inner Square
            m = int(self.width * 0.15)
            inner_rect = pygame.Rect(m, m, self.width - m*2, self.height - m*2)
            draw_flat_rect(player_surface, PLAYER_INNER_COLOR, inner_rect)
            pygame.draw.rect(player_surface, BORDER_COLOR, inner_rect, 2)
            
            # Detail (Eye)
            eye_s = int(self.width * 0.14)
            eye_rect = pygame.Rect(int(self.width * 0.25), int(self.height * 0.25), eye_s, eye_s)
            pygame.draw.rect(player_surface, (255, 255, 255), eye_rect)
        elif self.mode == "SHIP":
            w, h = self.width, self.height
            # === Authentic GD Ship: flat bottom hull + triangular dorsal fin ===
            
            # 1. Main hull (flat bottom, tapered nose)
            hull_poly = [
                (w*0.05, h*0.55),   # back-bottom
                (w*0.05, h*0.35),   # back-top of hull
                (w*0.95, h*0.42),   # nose-top
                (w*0.95, h*0.55),   # nose-bottom
            ]
            pygame.draw.polygon(player_surface, PLAYER_COLOR, hull_poly)
            pygame.draw.polygon(player_surface, BORDER_COLOR, hull_poly, 3)
            
            # 2. Dorsal fin / wing (triangle rising from hull top)
            fin_poly = [
                (w*0.10, h*0.35),   # base-left
                (w*0.35, h*0.08),   # peak
                (w*0.60, h*0.35),   # base-right
            ]
            pygame.draw.polygon(player_surface, PLAYER_COLOR, fin_poly)
            pygame.draw.polygon(player_surface, BORDER_COLOR, fin_poly, 3)
            
            # 3. Lighter inner highlight on hull
            inner_hull = [
                (w*0.12, h*0.52),
                (w*0.12, h*0.40),
                (w*0.88, h*0.44),
                (w*0.88, h*0.52),
            ]
            pygame.draw.polygon(player_surface, PLAYER_INNER_COLOR, inner_hull)
            pygame.draw.polygon(player_surface, BORDER_COLOR, inner_hull, 2)
            
            # 4. Cockpit window / eye area (small bright square on hull)
            eye_x, eye_y = w*0.55, h*0.40
            eye_s = w*0.12
            pygame.draw.rect(player_surface, (255, 255, 255), (eye_x, eye_y, eye_s, eye_s))
            pygame.draw.rect(player_surface, BORDER_COLOR, (eye_x, eye_y, eye_s, eye_s), 2)
            # Pupil
            pygame.draw.rect(player_surface, (0, 0, 0), (eye_x + eye_s*0.5, eye_y + eye_s*0.2, eye_s*0.35, eye_s*0.6))
            
            # 5. Engine exhaust nozzle (back)
            nozzle_poly = [
                (0, h*0.35),
                (w*0.08, h*0.38),
                (w*0.08, h*0.55),
                (0, h*0.58),
            ]
            pygame.draw.polygon(player_surface, (120, 120, 130), nozzle_poly)
            pygame.draw.polygon(player_surface, BORDER_COLOR, nozzle_poly, 2)
            
            # 6. Ventral fin (small triangle under hull)
            vent_poly = [
                (w*0.25, h*0.55),
                (w*0.35, h*0.75),
                (w*0.50, h*0.55),
            ]
            pygame.draw.polygon(player_surface, PLAYER_COLOR, vent_poly)
            pygame.draw.polygon(player_surface, BORDER_COLOR, vent_poly, 2)
        
        rotated_surface = pygame.transform.rotate(player_surface, self.rotation_angle)
        
        screen_x = self.x - camera_scroll_x
        screen_y = self.y
        
        rotated_rect = rotated_surface.get_rect(center=(screen_x + self.width/2, screen_y + self.height/2))
        surface.blit(rotated_surface, rotated_rect.topleft)
