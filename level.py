import pygame  # type: ignore
import random
from settings import TILE_SIZE, HEIGHT, GROUND_COLOR, GROUND_LINE_COLOR, BORDER_COLOR, BORDER_THICKNESS  # type: ignore
from objects import Block, Spike, Portal, Sawblade, JumpOrb, Star  # type: ignore

class Level:
    def __init__(self, target_duration=60.0, speed=450.0, density=1.2, map_seed=0, block_color=(255, 40, 100), spike_color=(225, 225, 225), theme=None):
        self.block_color = block_color
        self.spike_color = spike_color
        if theme is None:
            self.theme = {"bg": (28, 69, 135), "ground": (20, 50, 100), "line": (255, 255, 255)}
        else:
            self.theme = theme
        self.blocks = []
        self.spikes = []
        self.portals = []
        self.sawblades = []
        self.orbs = []
        self.stars = []
        self.energy_barriers = []  # Visual-only energy walls near portals [(x, height)]
        self.new_stars_collected = 0
        self.ground_y = HEIGHT - 100
        self.total_width = 0
        
        self.generate_and_load_map(target_duration, speed, density, map_seed)

    def generate_and_load_map(self, target_duration, speed, density, map_seed):
        random.seed(map_seed)
        self._pending_barriers = []
        
        # Calculate total required width to match music duration
        self.total_width = target_duration * speed
        cols = int(self.total_width / TILE_SIZE)
        rows = 10
        
        # Start with completely empty map from 1% to 100%
        map_data = [["." for _ in range(cols)] for _ in range(rows)]
        
        # Procedurally build map sequentially without any looping
        col = 25
        mode = "CUBE"
        while col < cols - 20: 
            gap = random.randint(int(4 / density), int(9 / density)) # More dense gaps
            col += gap
            if col >= cols - 20:
                break
                
            # 10% chance to spawn a mode portal
            if random.random() < 0.1:
                new_mode = "SHIP" if mode == "CUBE" else "CUBE"
                char = "P" if new_mode == "SHIP" else "C"
                # Portal fits at row 8 extending downwards
                map_data[8][col] = char
                
                # Store energy barrier positions (visual-only force fields, no collision)
                # These will be drawn as glowing energy walls near the portal
                if col - 2 >= 0:
                    self._pending_barriers.append(col - 2)
                if col + 3 < cols:
                    self._pending_barriers.append(col + 3)
                
                mode = new_mode
                col += 6 # clear gap for smooth transition
                continue
                
            choice = random.choice([1, 2, 3, 4, 5, 6, 7, 8, 9])
            
            # Bottom row is 9, second bottom is 8, etc.
            if choice == 1:
                map_data[9][col] = '^'
                if density > 1.0 and col + 1 < cols and random.random() < 0.5:
                    map_data[9][col+1] = '^'
            elif choice == 2:
                if col + 1 < cols:
                    map_data[9][col] = '^'
                    map_data[9][col+1] = '^'
                    if density > 1.0 and col + 2 < cols and random.random() < 0.5:
                        map_data[9][col+2] = '^'
            elif choice == 3:
                map_data[9][col] = '#'
            elif choice == 4:
                if col + 1 < cols:
                    map_data[9][col] = '#'
                    map_data[9][col+1] = '#'
            elif choice == 5:
                map_data[9][col] = '#'
                map_data[8][col] = '^'
            elif choice == 6:
                # Step up blocks
                if col + 2 < cols:
                    map_data[9][col] = '#'
                    map_data[9][col+1] = '#'
                    map_data[8][col+1] = '#'
                    map_data[9][col+2] = '#'
                    map_data[8][col+2] = '#'
                    map_data[7][col+2] = '#'
            elif choice == 7:
                map_data[9][col] = '*' # Sawblade
                if density > 1.0 and col + 1 < cols and random.random() < 0.5:
                    map_data[9][col+1] = '*' # Epic double sawblade
            elif choice == 8:
                map_data[7][col] = 'O' # Jump Orb (Floating)
            elif choice == 9:
                map_data[8][col] = '$' # Star
                
            if mode == "SHIP":
                # ALWAYS add obstacles both TOP and BOTTOM in ship mode
                ceil_choice = random.choice([1, 2, 3, 4, 5])
                if ceil_choice == 1:
                    # Ceiling spike
                    map_data[0][col] = 'V'
                elif ceil_choice == 2:
                    # Ceiling block + spike
                    if col + 1 < cols:
                        map_data[0][col] = '#'
                        map_data[1][col] = 'V'
                elif ceil_choice == 3:
                    # Ceiling sawblade
                    map_data[1][col] = '*'
                elif ceil_choice == 4:
                    # Double ceiling spike
                    if col + 1 < cols:
                        map_data[0][col] = 'V'
                        map_data[0][col+1] = 'V'
                elif ceil_choice == 5:
                    # Ceiling block pair
                    map_data[0][col] = '#'
                    map_data[1][col] = '#'
                
                # Also add floor obstacles in ship sections
                floor_choice = random.choice([0, 1, 2, 3])
                if floor_choice == 1:
                    map_data[9][col] = '^'
                elif floor_choice == 2:
                    map_data[9][col] = '#'
                    map_data[8][col] = '^'
                elif floor_choice == 3:
                    map_data[9][col] = '*'

        # Load string format
        map_strings = ["".join(r) for r in map_data]
        self.load_map(map_strings)
        
        # Convert pending barrier columns to world-space energy barriers
        for bc in self._pending_barriers:
            bx = bc * TILE_SIZE
            self.energy_barriers.append(bx)
        
        random.seed() # Reset seed so particles remain random

    def load_map(self, map_data):
        rows = len(map_data)
        self.total_width = len(map_data[0]) * TILE_SIZE
        for row_index, row in enumerate(map_data):
            for col_index, char in enumerate(row):
                x = col_index * TILE_SIZE
                y = self.ground_y - (rows - row_index) * TILE_SIZE
                
                if char == '#':
                    self.blocks.append(Block(x, y, color=self.block_color))
                elif char == '^':
                    self.spikes.append(Spike(x, y, color=self.spike_color))
                elif char == 'V':
                    self.spikes.append(Spike(x, y, color=self.spike_color, pointing_down=True))
                elif char == 'P':
                    self.portals.append(Portal(x, y, "SHIP"))
                elif char == 'C':
                    self.portals.append(Portal(x, y, "CUBE"))
                elif char == '*':
                    self.sawblades.append(Sawblade(x, y))
                elif char == 'O':
                    self.orbs.append(JumpOrb(x, y))
                elif char == '$':
                    self.stars.append(Star(x, y))

    def check_collisions(self, player):
        """Phase 5: Accurate collision detection and resolution."""
        # Check portals first
        for portal in self.portals:
            if abs(portal.x - player.x) > TILE_SIZE * 3:
                continue
            if player.rect.colliderect(portal.rect):
                if player.mode != portal.mode:
                    player.mode = portal.mode
                    player.is_grounded = False # Reset state abruptly

        # 1. Spikes & Sawblades Hazard
        for spike in self.spikes:
            if abs(spike.x - player.x) > TILE_SIZE * 3:
                continue
            if player.rect.colliderect(spike.hitbox):
                return "DEATH"
                
        for saw in self.sawblades:
            if abs(saw.x - (player.x + player.width/2)) > TILE_SIZE * 3:
                continue
            # Circle vs AABB approx
            dx = (player.x + player.width/2) - saw.x
            dy = (player.y + player.height/2) - saw.y
            dist = (dx**2 + dy**2)**0.5
            if dist < saw.hitbox_radius + player.width * 0.4:
                return "DEATH"
                
        # Stars collection
        self.new_stars_collected = 0
        for star in self.stars:
            if not star.collected and abs(star.x - (player.x + player.width/2)) < TILE_SIZE * 3:
                dx = (player.x + player.width/2) - star.x
                dy = (player.y + player.height/2) - star.y
                dist = (dx**2 + dy**2)**0.5
                if dist < star.trigger_radius + player.width * 0.5:
                    star.collected = True
                    self.new_stars_collected += 1

        # 2. Blocks Collision (Resolves Top Landing vs Side Crashing)
        for block in self.blocks:
            if abs(block.x - player.x) > TILE_SIZE * 3:
                continue
            if player.rect.colliderect(block.rect):
                prev_bottom = player.prev_y + player.height
                
                # Check for top collision (landing)
                # If player was previously above or at the block's top edge, and is falling
                if prev_bottom - (player.y_vel * 0.016) <= block.y + 10 and player.y_vel >= 0:
                    player.y = block.y - player.height
                    player.y_vel = 0
                    if not player.is_grounded:
                        # Snap rotation immediately exclusively on landing
                        player.rotation_angle = round(player.rotation_angle / 90.0) * 90.0
                    player.is_grounded = True
                    player.rect.y = int(player.y)
                else:
                    # Side or bottom collision implies crashing
                    return "DEATH"

        # 3. Ground Collision Fallback
        if player.y + player.height >= self.ground_y:
            player.y = self.ground_y - player.height
            player.y_vel = 0
            if not player.is_grounded and player.mode == "CUBE":
                player.rotation_angle = round(player.rotation_angle / 90.0) * 90.0
            player.is_grounded = True
            player.rect.y = int(player.y)
            
        # 4. Ceiling Collision (Ship Mode)
        if player.mode == "SHIP" and player.y <= 0:
            player.y = 0
            player.y_vel = 0
            player.rect.y = 0
            
        return "SAFE"
        
    def check_orb_jump(self, player):
        """Called when player presses SPACE. Checks if in range of any jump orb."""
        for orb in self.orbs:
            if abs(orb.x - (player.x + player.width/2)) < TILE_SIZE * 3:
                dx = (player.x + player.width/2) - orb.x
                dy = (player.y + player.height/2) - orb.y
                dist = (dx**2 + dy**2)**0.5
                if dist < orb.trigger_radius + player.width * 0.5:
                    # Provide an orb jump impulse
                    player.y_vel = player.jump_force * 1.05 # slightly stronger than normal jump
                    player.orb_jump_active = True
                    # Orb visual feedback
                    orb.pulse = 10.0 
                    return True
        return False

    def draw(self, surface, camera_scroll_x, dt=0.0):
        # === 1. Parallax Background ===
        bg_scroll_x = camera_scroll_x * 0.15
        bg_color = self.theme["bg"]
        
        # Authentic Geometry Dash Parallax Background (Floating Squares and Pillars)
        import math
        for i in range(12):
            sq_x = (i * 150 - bg_scroll_x * 0.2) % (surface.get_width() + 100) - 50
            sq_y = (math.sin(i * 4.5) * 200) + surface.get_height() // 2 - 100
            size = 30 + (i % 3) * 20
            c_val = min(255, bg_color[0] + 30)
            pygame.draw.rect(surface, (c_val, c_val, c_val, 40), (int(sq_x), int(sq_y), size, size), 2)
            
        # Parallax geometric clouds/pillars
        for i in range(8):
            px = (i * 400 - bg_scroll_x * 0.5) % (surface.get_width() + 200) - 100
            ph = 150 + (i % 3) * 100
            py = self.ground_y - ph
            dark_bg = (max(0, bg_color[0]-15), max(0, bg_color[1]-15), max(0, bg_color[2]-15))
            pygame.draw.rect(surface, dark_bg, (px, py, 120, ph))
            pygame.draw.rect(surface, (bg_color[0], bg_color[1], bg_color[2]), (px+5, py+5, 110, ph))
        
        # Subtle Background Grid
        grid_color = (min(255, bg_color[0]+20), min(255, bg_color[1]+20), min(255, bg_color[2]+20))
        grid_scroll = bg_scroll_x % 80
        for i in range(-1, int(surface.get_width() / 80) + 2):
            x_bg = i * 80 - grid_scroll
            pygame.draw.line(surface, grid_color, (x_bg, 0), (x_bg, self.ground_y), 1)
        for j in range(int(self.ground_y / 80) + 1):
            y_bg = self.ground_y - j * 80
            pygame.draw.line(surface, grid_color, (0, y_bg), (surface.get_width(), y_bg), 1)

        # === 2. Base Ground (Checkerboard Geometry Dash Style) ===
        ground_rect = pygame.Rect(0, self.ground_y, surface.get_width(), surface.get_height() - self.ground_y)
        base_gnd = self.theme["ground"]
        alt_gnd = (max(0, base_gnd[0]-15), max(0, base_gnd[1]-15), max(0, base_gnd[2]-15))
        pygame.draw.rect(surface, base_gnd, ground_rect)
        
        ground_scroll = camera_scroll_x % TILE_SIZE
        g_cols = int(surface.get_width() / TILE_SIZE) + 2
        g_rows = int((surface.get_height() - self.ground_y) / TILE_SIZE) + 1
        
        for row in range(g_rows):
            foffset = (camera_scroll_x // TILE_SIZE)
            for col in range(-1, g_cols):
                if (int(foffset) + col + row) % 2 == 0:
                    gx = col * TILE_SIZE - ground_scroll
                    gy = self.ground_y + row * TILE_SIZE
                    pygame.draw.rect(surface, alt_gnd, (gx, gy, TILE_SIZE, TILE_SIZE))
            
        # Ground Top Border Line (Thick glowing line)
        line_y = self.ground_y
        pygame.draw.line(surface, self.theme["line"], (0, line_y), (surface.get_width(), line_y), BORDER_THICKNESS + 2)
        pygame.draw.line(surface, (255, 255, 255), (0, line_y-2), (surface.get_width(), line_y-2), 1)
        
        for block in self.blocks:
            block.draw(surface, camera_scroll_x)
            
        for spike in self.spikes:
            spike.draw(surface, camera_scroll_x)
            
        for portal in self.portals:
            # Portal approach warning effects
            import math
            p_screen_x = portal.x - camera_scroll_x
            p_cx = p_screen_x + portal.width / 2
            p_cy = portal.y + portal.height / 2
            
            # Only draw effects if portal is approaching (within 600px ahead)
            if -200 < p_screen_x < surface.get_width() + 100:
                # 1. Pulsing vertical glow columns flanking the portal
                t = pygame.time.get_ticks() / 1000.0
                glow_alpha = int((math.sin(t * 6) + 1) * 40 + 20)
                glow_col = (*portal.color[:3], glow_alpha)
                
                glow_s = pygame.Surface((30, surface.get_height()), pygame.SRCALPHA)
                pygame.draw.rect(glow_s, glow_col, (0, 0, 30, surface.get_height()))
                surface.blit(glow_s, (p_cx - 15, 0))
                
                # 2. Horizontal speed-lines converging toward portal
                num_lines = 8
                for li in range(num_lines):
                    ly = portal.y + (li / num_lines) * portal.height
                    line_len = 40 + math.sin(t * 4 + li) * 20
                    line_alpha = int(120 + math.sin(t * 5 + li * 0.7) * 60)
                    line_col = (portal.color[0], portal.color[1], portal.color[2], line_alpha)
                    ls = pygame.Surface((int(line_len), 3), pygame.SRCALPHA)
                    pygame.draw.rect(ls, line_col, (0, 0, int(line_len), 3))
                    surface.blit(ls, (p_cx - portal.width - line_len - 10 + math.sin(t * 8 + li) * 15, ly))
                
                # 3. Warning text above portal
                warn_font = pygame.font.SysFont("Arial", 18, bold=True)
                mode_txt = "SHIP MODE" if portal.mode == "SHIP" else "CUBE MODE"
                warn_s = warn_font.render(mode_txt, True, portal.color)
                warn_s.set_alpha(int((math.sin(t * 4) + 1) * 100 + 55))
                surface.blit(warn_s, (p_cx - warn_s.get_width() // 2, portal.y - 30))
            
            portal.draw(surface, camera_scroll_x, dt)
            
        for saw in self.sawblades:
            saw.draw(surface, camera_scroll_x, dt)
            
        for orb in self.orbs:
            orb.draw(surface, camera_scroll_x, dt)
            
        for star in self.stars:
            star.draw(surface, camera_scroll_x, dt)
            
        # Draw Level End Boundary Wall
        end_wall_x = self.total_width - camera_scroll_x
        if end_wall_x <= surface.get_width():
            # Glowing white boundary line
            pygame.draw.rect(surface, (255, 255, 255), (end_wall_x, 0, 15, surface.get_height()))
            # Complete darkness "out of bounds" zone
            pygame.draw.rect(surface, (10, 10, 10), (end_wall_x + 15, 0, surface.get_width(), surface.get_height()))
        
        # Draw Energy Barriers (glowing force fields near portals)
        import math
        t = pygame.time.get_ticks() / 1000.0
        for bx in self.energy_barriers:
            screen_bx = bx - camera_scroll_x
            if -50 < screen_bx < surface.get_width() + 50:
                barrier_h = self.ground_y
                # Animated shimmer
                shimmer = math.sin(t * 8 + bx * 0.01)
                
                # Translucent energy column
                b_surf = pygame.Surface((12, barrier_h), pygame.SRCALPHA)
                base_alpha = int(60 + shimmer * 25)
                # Gradient from top to bottom
                for by in range(0, barrier_h, 4):
                    seg_alpha = int(base_alpha + math.sin(t * 6 + by * 0.05) * 20)
                    seg_alpha = max(20, min(120, seg_alpha))
                    pygame.draw.rect(b_surf, (100, 200, 255, seg_alpha), (0, by, 12, 4))
                surface.blit(b_surf, (screen_bx, 0))
                
                # Bright edge lines
                edge_alpha = int(100 + shimmer * 50)
                edge_s = pygame.Surface((2, barrier_h), pygame.SRCALPHA)
                pygame.draw.rect(edge_s, (150, 230, 255, edge_alpha), (0, 0, 2, barrier_h))
                surface.blit(edge_s, (screen_bx, 0))
                surface.blit(edge_s, (screen_bx + 10, 0))
                
                # Floating energy dots
                for di in range(6):
                    dy = (di * barrier_h // 6 + int(t * 60 + bx) % barrier_h) % barrier_h
                    dot_alpha = int(150 + math.sin(t * 4 + di) * 80)
                    pygame.draw.circle(surface, (200, 240, 255, dot_alpha), (int(screen_bx + 6), dy), 3)
