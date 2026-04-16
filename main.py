import sys
import random
import math
import os
import json
import pygame  # type: ignore
from settings import WIDTH, HEIGHT, TITLE, TARGET_FPS, BG_COLOR, PLAYER_COLOR, PLAYER_INNER_COLOR, DIFFICULTIES, LEVEL_SEEDS, LEVEL_THEMES, GRAVITY  # type: ignore
from player import Player  # type: ignore
from level import Level  # type: ignore

class ExplosionParticle:
    def __init__(self, x, y, vx, vy, size, color, p_type="square"):
        self.x = float(x)
        self.y = float(y)
        self.vx = float(vx)
        self.vy = float(vy)
        self.size = float(size)
        self.color = color
        self.p_type = p_type

class Game:
    def __init__(self):
        pygame.init()
        pygame.mixer.init() # Initiate audio for rhythm sync
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption(TITLE)
        self.clock = pygame.time.Clock()
        
        # Load user music (Vui lòng chèn file level_track.mp3 vào thư mục)
        self.music_duration = 60.0 # Default 60 seconds
        try:
            # We use Sound to get accurate length for level generation
            self.bg_sound = pygame.mixer.Sound("bg_music.mp3")
            self.music_duration = self.bg_sound.get_length()
        except Exception:
            try:
                self.bg_sound = pygame.mixer.Sound("level_track.mp3")
                self.music_duration = self.bg_sound.get_length()
            except Exception:
                print("[AUDIO] Khong tim thay 'bg_music.mp3' hay 'level_track.mp3'. Game se chay im lang hoac voi map 60s.")
                
        # Setup the music mixer for bg streaming playback
        try:
            pygame.mixer.music.load("bg_music.mp3")
        except Exception:
            try:
                pygame.mixer.music.load("level_track.mp3")
            except Exception:
                print("[AUDIO] Mixer load failed.")
        self.running = True
        
        # Save System
        self.save_file = "save_data.json"
        self.user_stats = self.load_save_data()
        self.current_user = None
        
        # State Management
        self.state = "INTRO"
        self.intro_timer = 0.0
        self.username = ""
        self.time_elapsed = 0.0
        self.current_level_idx = 0 # Default: Map 1
        self.current_diff_idx = 1 # Default: Bình Thường
        self.death_timer = 0.0
        self.particles = []
        self.win_particles = []
        self.win_timer = 0.0
        self.title_font = pygame.font.SysFont("Arial", 64, bold=True)
        self.menu_font = pygame.font.SysFont("Arial", 36, bold=True)
        self.sub_font = pygame.font.SysFont("Arial", 24)
        self.small_font = pygame.font.SysFont("Arial", 18)
        # Login screen: list of (pygame.Rect, username) for profile card click detection
        self._login_profile_rects: list = []
        self._login_hovered_card: int = -1
        self._login_btn_rect: pygame.Rect = pygame.Rect(0, 0, 0, 0)
        
        # Declare attributes to satisfy IDE type checker
        self.level: Level
        self.player: Player
        self.camera_scroll_x: float
        
        # Start immediately in reset_level
        self.reset_level_silent()
        
        self._init_sfx()

    def _init_sfx(self):
        import wave, struct, random, io, math
        def make_wav(freq, duration, s_type="sine", vol=0.5):
            sr = 44100
            n = int(sr * duration)
            buf = io.BytesIO()
            with wave.open(buf, 'w') as w:
                w.setnchannels(1); w.setsampwidth(2); w.setframerate(sr)
                for i in range(n):
                    t = i / sr
                    if s_type == "sine":
                        v = math.sin(t * freq * 2 * math.pi) * math.exp(-t*8)
                    elif s_type == "square":
                        v = (1.0 if math.sin(t * freq * 2 * math.pi) > 0 else -1.0) * math.exp(-t*15)
                    elif s_type == "play":
                        f = freq + t * 1500
                        v = math.sin(t * f * 2 * math.pi) * math.exp(-t*4)
                    elif s_type == "crash":
                        v = random.uniform(-1, 1) * math.exp(-t*10)
                    s = int(max(-1.0, min(1.0, v)) * vol * 32767)
                    w.writeframesraw(struct.pack('<h', s))
            buf.seek(0)
            return pygame.mixer.Sound(buf)
        try:
            self.sfx_diff_select = make_wav(600, 0.1, "sine", 0.35)
            self.sfx_map_select = make_wav(1000, 0.15, "square", 0.08)
            self.sfx_play = self._make_play_sfx(sr=44100)
            self.sfx_crash = make_wav(0, 0.6, "crash", 0.5)
        except Exception:
            pass

    def _make_play_sfx(self, sr=44100):
        import wave, struct, math, io
        dur = 0.35
        n = int(sr * dur)
        buf = io.BytesIO()
        with wave.open(buf, 'w') as w:
            w.setnchannels(1); w.setsampwidth(2); w.setframerate(sr)
            for i in range(n):
                t = i / sr
                # Three ascending tones blended
                f1 = 500 + t * 2000
                f2 = 750 + t * 2500
                f3 = 1000 + t * 3000
                v1 = math.sin(t * f1 * 2 * math.pi) * 0.4
                v2 = math.sin(t * f2 * 2 * math.pi) * 0.3
                v3 = math.sin(t * f3 * 2 * math.pi) * 0.2
                env = math.exp(-t * 6) * (1.0 - math.exp(-t * 80))  # attack + decay
                v = (v1 + v2 + v3) * env
                s = int(max(-1.0, min(1.0, v)) * 32767)
                w.writeframesraw(struct.pack('<h', s))
        buf.seek(0)
        return pygame.mixer.Sound(buf)

    def load_save_data(self):
        if os.path.exists(self.save_file):
            try:
                with open(self.save_file, "r") as f:
                    return json.load(f)
            except:
                return {}
        return {}
        
    def save_data(self):
        try:
            with open(self.save_file, "w") as f:
                json.dump(self.user_stats, f, indent=4)
        except:
            pass

    def get_current_stats(self):
        if self.current_user not in self.user_stats:
            self.user_stats[self.current_user] = {
                "attempts": 0,
                "stars": 0,
                "wins": 0,
                "best_maps": [0.0]*len(LEVEL_SEEDS)
            }
        s = self.user_stats[self.current_user]
        # Migrate old saves that lack 'wins'
        if "wins" not in s:
            s["wins"] = 0
        return s

    def reset_level_silent(self):
        diff = DIFFICULTIES[self.current_diff_idx]
        speed = diff["speed"]
        density = diff["density"]
        block_color = diff["block"]
        spike_color = diff["spike"]
        gravity = diff.get("gravity", 3500.0)
        jump_force = diff.get("jump_force", -1150.0)
        ship_gravity = diff.get("ship_gravity", 1600.0)
        flight_force = diff.get("flight_force", 3000.0)
        seed = LEVEL_SEEDS[self.current_level_idx]
        theme = LEVEL_THEMES[self.current_level_idx]
        
        self.level = Level(target_duration=self.music_duration, speed=speed, density=density, map_seed=seed, block_color=block_color, spike_color=spike_color, theme=theme)
        self.player = Player(x=250, y=self.level.ground_y - 200, speed=speed, gravity=gravity, jump_force=jump_force, ship_gravity=ship_gravity, flight_force=flight_force)
        self.current_run_time = 0.0
        self.last_run_pct = 0.0
        self.last_run_stars = 0
        self.run_total_stars = 0
        self.star_hud_pulse = 0.0

    def reset_level(self):
        """Instantly loads Level and Player elements for fast respawns."""
        if self.current_user:
            stats = self.get_current_stats()
            stats["attempts"] += 1
            self.save_data()
            
        self.reset_level_silent()

    def trigger_death(self):
        """Phase 6: Switches to DEATH state and spawns visual explosion."""
        self.state = "DEATH"
        self.death_timer = 1.0  # 1 second respawn time
        self.particles.clear()
        if pygame.mixer.get_init():
            pygame.mixer.music.stop() # Stop music immediately upon death
        if getattr(self, 'sfx_crash', None): self.sfx_crash.play()
        
        # Spawn Flat Vector Explosion Particles
        for _ in range(30):
            self.particles.append(ExplosionParticle(
                x=self.player.x + self.player.width / 2,
                y=self.player.y + self.player.height / 2,
                vx=random.uniform(-600, 600),
                vy=random.uniform(-600, 600),
                size=random.uniform(5, 15),
                color=random.choice([PLAYER_COLOR, PLAYER_INNER_COLOR, (255, 255, 255)])
            ))

    def run(self):
        while self.running:
            dt = self.clock.tick(TARGET_FPS) / 1000.0
            self.events()
            self.update(dt)
            self.draw()
            
        pygame.quit()
        sys.exit()

    def events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.MOUSEMOTION:
                if self.state == "LOGIN":
                    mx, my = event.pos
                    self._login_hovered_card = -1
                    for idx, (rect, _) in enumerate(self._login_profile_rects):
                        if rect.collidepoint(mx, my):
                            self._login_hovered_card = idx
                            break
            elif event.type == pygame.KEYDOWN:
                # Skip intro on any key
                if self.state == "INTRO":
                    self.state = "LOGIN"
                    continue
                if self.state == "LOGIN":
                    if event.key == pygame.K_RETURN:
                        if len(self.username) > 0:
                            self.current_user = self.username
                            self.state = "MENU"
                    elif event.key == pygame.K_BACKSPACE:
                        self.username = self.username[:-1]
                    elif event.key == pygame.K_ESCAPE:
                        self.running = False
                    else:
                        if len(self.username) < 15 and event.unicode.isprintable():
                            self.username += event.unicode
                elif event.key == pygame.K_ESCAPE:
                    if self.state == "POST_GAME":
                        self.state = "MENU"
                        self.reset_level()
                    else:
                        self.running = False
                elif event.key == pygame.K_SPACE:
                    if getattr(self, 'sfx_play', None) and self.state in ("MENU", "POPUP"): self.sfx_play.play()
                    if self.state in ("MENU", "COMPLETE"):
                        self.state = "POPUP"
                    elif self.state in ("POPUP", "POST_GAME"):
                        self.reset_level()
                        self.state = "PLAYING"
                        if pygame.mixer.get_init():
                            pygame.mixer.music.play()
                    elif self.state == "PLAYING":
                        self.level.check_orb_jump(self.player)
                elif event.key == pygame.K_LEFT and self.state == "MENU":
                    self.current_diff_idx = max(0, self.current_diff_idx - 1)
                    if getattr(self, 'sfx_diff_select', None): self.sfx_diff_select.play()
                elif event.key == pygame.K_RIGHT and self.state == "MENU":
                    self.current_diff_idx = min(len(DIFFICULTIES) - 1, self.current_diff_idx + 1)
                    if getattr(self, 'sfx_diff_select', None): self.sfx_diff_select.play()
                elif pygame.K_1 <= event.key <= pygame.K_5 and self.state == "MENU":
                    self.current_level_idx = event.key - pygame.K_1
                    if getattr(self, 'sfx_map_select', None): self.sfx_map_select.play()
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:
                    # Skip intro on click
                    if self.state == "INTRO":
                        self.state = "LOGIN"
                        continue
                    if self.state == "LOGIN":
                        mx, my = event.pos
                        # Click START button for new player
                        if self._login_btn_rect.collidepoint(mx, my) and len(self.username) > 0:
                            self.current_user = self.username
                            self.state = "MENU"
                        else:
                            for rect, uname in self._login_profile_rects:
                                if rect.collidepoint(mx, my):
                                    self.current_user = uname
                                    self.username = uname
                                    self.state = "MENU"
                                    break
                    elif self.state in ("MENU", "COMPLETE"):
                        if getattr(self, 'sfx_play', None): self.sfx_play.play()
                        self.state = "POPUP"
                    elif self.state in ("POPUP", "POST_GAME"):
                        if getattr(self, 'sfx_play', None): self.sfx_play.play()
                        self.reset_level()
                        self.state = "PLAYING"
                        if pygame.mixer.get_init():
                            pygame.mixer.music.play()
                    elif self.state == "PLAYING":
                        self.level.check_orb_jump(self.player)

    def update_best_progress(self, force_100=False):
        if not self.current_user or not hasattr(self, 'level'):
            return
        stats = self.get_current_stats()
        pct = 1.0 if force_100 else min(1.0, max(0.0, self.player.x / self.level.total_width))
        if pct > stats["best_maps"][self.current_level_idx]:
            stats["best_maps"][self.current_level_idx] = pct
            self.save_data()

    def update(self, dt):
        self.time_elapsed += dt
        self.last_dt = dt
        
        if self.state == "INTRO":
            self.intro_timer += dt
            if self.intro_timer >= 10.0:
                self.state = "LOGIN"
            return
        
        if self.state == "PLAYING":
            self.current_run_time += dt
            
            # Pass holding state into update for continuous physics check (ship fly/jump buffer)
            keys = pygame.key.get_pressed()
            mouse = pygame.mouse.get_pressed()
            holding_jump = keys[pygame.K_SPACE] or mouse[0]
                
            self.player.update(dt, holding_jump)
            
            # Camera logic: lock camera when approaching the end wall
            target_scroll = self.player.x - 250
            max_scroll = self.level.total_width - 1180 # Stop scrolling so end wall stays on the right
            self.camera_scroll_x = min(target_scroll, max_scroll)
            
            # Phase 5: Collision Detection
            status = self.level.check_collisions(self.player)
            
            if self.star_hud_pulse > 0:
                self.star_hud_pulse -= dt
                
            if self.level.new_stars_collected > 0:
                self.run_total_stars += self.level.new_stars_collected
                self.star_hud_pulse = 0.5
                if self.current_user:
                    stats = self.get_current_stats()
                    stats["stars"] += self.level.new_stars_collected
                    self.save_data()
                
            if status == "DEATH":
                self.update_best_progress()
                self.trigger_death()
                
            # Phase 7: Win Condition check
            elif self.player.x >= self.level.total_width - 150:
                self.update_best_progress(force_100=True)
                # Stop 150 pixels before the wall
                self.player.x = self.level.total_width - 150
                self.state = "FINISHING_GLIDE"
                self.player.y_vel = 0 # Disable gravity completely
                self.player.is_grounded = False
                
        elif self.state == "FINISHING_GLIDE":
            # Float slowly into the wall
            self.player.x += 150 * dt # Takes 1 second to travel 150px
            
            # Slow backward 180 degree flip
            target_angle = 180.0
            self.player.rotation_angle += (target_angle - self.player.rotation_angle) * 5 * dt
                
            if self.player.x >= self.level.total_width:
                self.player.x = self.level.total_width
                self.state = "FINISHING_EFFECT"
                self.win_timer = 1.5
                self.win_particles = []
                
                center_x = self.level.total_width
                center_y = self.player.y + self.player.height/2
                
                # 1. Expanding Ring
                self.win_particles.append(ExplosionParticle(x=center_x, y=center_y, vx=0, vy=0, size=10, color=(255, 255, 255), p_type="ring"))
                
                # 2. Glowing Rays
                for i in range(12):
                    angle = (i / 12.0) * math.pi * 2
                    self.win_particles.append(ExplosionParticle(
                        x=center_x, y=center_y, 
                        vx=math.cos(angle) * 1500, vy=math.sin(angle) * 1500, 
                        size=60, # length of ray
                        color=random.choice([(255, 255, 255), (0, 200, 255)]),
                        p_type="ray"
                    ))
                    
                # 3. Square fragments
                for _ in range(40):
                    self.win_particles.append(ExplosionParticle(
                        x=center_x, y=center_y,
                        vx=random.uniform(-1200, 200),
                        vy=random.uniform(-1000, 1000),
                        size=random.uniform(10, 25),
                        color=random.choice([PLAYER_COLOR, PLAYER_INNER_COLOR, (255, 255, 255)]),
                        p_type="square"
                    ))
                    
        elif self.state == "FINISHING_EFFECT":
            self.win_timer -= dt
            for p in self.win_particles:
                if p.p_type == "ring":
                    p.size += 1500 * dt # ring expands quickly
                elif p.p_type == "ray":
                    p.x += p.vx * dt
                    p.y += p.vy * dt
                    p.size = max(0.0, p.size - 40 * dt) # Rays get shorter
                    p.vx *= 0.9 # Ray slows down
                    p.vy *= 0.9
                else: # square
                    p.x += p.vx * dt
                    p.y += p.vy * dt
                    p.size = max(0.0, p.size - 15 * dt)
                
            if self.win_timer <= 0:
                self.last_run_pct = 100.0
                self.last_run_stars = self.run_total_stars
                # Record win in save data
                if self.current_user:
                    stats = self.get_current_stats()
                    stats["wins"] = stats.get("wins", 0) + 1
                    self.save_data()
                self.state = "POST_GAME"

        elif self.state == "DEATH":
            self.death_timer -= dt
            # Phase 6: Particles Animation Update
            for p in self.particles:
                p.x += p.vx * dt
                p.y += p.vy * dt
                p.vy += 1000 * dt
                p.size = max(0.0, p.size - 15 * dt)
                
            if self.death_timer <= 0:
                self.last_run_pct = min(1.0, max(0.0, self.player.x / self.level.total_width)) * 100 if self.level.total_width > 0 else 0.0
                self.last_run_stars = self.run_total_stars
                self.state = "POST_GAME"

    def _draw_intro(self):
        """Authentic Geometry Dash-style intro splash screen - 10 seconds."""
        t = self.intro_timer
        self.screen.fill((0, 0, 0))
        cx, cy = WIDTH // 2, HEIGHT // 2
        
        # ====== BACKGROUND (always active) ======
        # Smooth gradient background transition
        if t < 2.0:
            fade = min(1.0, t / 2.0)
        elif t > 9.0:
            fade = max(0.0, 1.0 - (t - 9.0) / 1.0)  # Fade to black at end
        else:
            fade = 1.0
        bg_r = int(8 * fade)
        bg_g = int(12 * fade)
        bg_b = int(35 * fade)
        self.screen.fill((bg_r, bg_g, bg_b))
        
        # Animated grid
        if fade > 0:
            grid_alpha = int(fade * 35)
            grid_scroll = int(t * 30) % 60
            for gx in range(-grid_scroll, WIDTH + 60, 60):
                pygame.draw.line(self.screen, (grid_alpha, grid_alpha, grid_alpha + 15), (gx, 0), (gx, HEIGHT), 1)
            for gy in range(0, HEIGHT, 60):
                pygame.draw.line(self.screen, (grid_alpha, grid_alpha, grid_alpha + 15), (0, gy), (WIDTH, gy), 1)
        
        # Floating particles (always, increasing density)
        num_parts = min(40, int(t * 5))
        for i in range(num_parts):
            px = (i * 73 + int(t * 60)) % WIDTH
            py = (i * 47 + int(t * 30 + i * 30)) % HEIGHT
            sq_size = 3 + (i % 4) * 2
            part_alpha = int(min(1.0, t / 2.0) * fade * 50)
            if part_alpha > 0:
                ps = pygame.Surface((sq_size, sq_size), pygame.SRCALPHA)
                pygame.draw.rect(ps, (255, 255, 255, part_alpha), (0, 0, sq_size, sq_size))
                self.screen.blit(ps, (px, py))
        
        # ====== PHASE 1 (0-3s): Developer credit ======
        if t < 3.0:
            if t > 0.3:
                credit_fade = min(1.0, (t - 0.3) / 1.0)
                if t > 2.2:
                    credit_fade = max(0.0, 1.0 - (t - 2.2) / 0.8)
                credit_alpha = int(credit_fade * 255)
                
                dev_font = pygame.font.SysFont("Arial", 28, bold=True)
                dev_s = dev_font.render("CSLT  HK252  PRESENTS", True, (180, 200, 255))
                dev_s.set_alpha(credit_alpha)
                self.screen.blit(dev_s, (cx - dev_s.get_width()//2, cy - 10))
                
                # Underline
                line_w = int(dev_s.get_width() * min(1.0, (t - 0.3) / 0.8))
                line_s = pygame.Surface((line_w, 2), pygame.SRCALPHA)
                pygame.draw.rect(line_s, (0, 180, 255, credit_alpha), (0, 0, line_w, 2))
                self.screen.blit(line_s, (cx - dev_s.get_width()//2, cy + 28))
        
        # ====== PHASE 2 (2.5-6s): Cube drops in + spinning ======
        if 2.5 < t < 8.5:
            cube_t = min(1.0, (t - 2.5) / 1.2)
            
            # Bounce physics
            if cube_t < 0.5:
                cube_y_pos = int(-120 + (cy - 80) * (cube_t / 0.5) ** 2)
            elif cube_t < 0.7:
                bounce = math.sin((cube_t - 0.5) / 0.2 * math.pi) * 40
                cube_y_pos = int(cy - 80 - bounce)
            elif cube_t < 0.85:
                bounce = math.sin((cube_t - 0.7) / 0.15 * math.pi) * 15
                cube_y_pos = int(cy - 80 - bounce)
            else:
                cube_y_pos = cy - 80
            
            cube_size = 90
            
            # Pulsing glow rings behind cube
            if cube_t > 0.5:
                ring_fade = min(1.0, (cube_t - 0.5) / 0.5)
                for ri in range(3):
                    r_rad = int(60 + ri * 25 + math.sin(t * 3 + ri) * 10)
                    ring_alpha = int(ring_fade * (40 - ri * 10))
                    ring_s = pygame.Surface((r_rad*2+4, r_rad*2+4), pygame.SRCALPHA)
                    pygame.draw.circle(ring_s, (0, 200, 255, ring_alpha), (r_rad+2, r_rad+2), r_rad, 2)
                    self.screen.blit(ring_s, (cx - r_rad - 2, cube_y_pos + cube_size//2 - r_rad - 2))
            
            # Spinning rotation
            spin_angle = 0
            if t > 4.0:
                spin_angle = (t - 4.0) * 180
            if t > 5.5:
                spin_angle = 270 + math.sin((t - 5.5) * 4) * 15  # Settle
            
            cube_surf = pygame.Surface((cube_size, cube_size), pygame.SRCALPHA)
            # Draw cube
            pygame.draw.rect(cube_surf, (255, 255, 0), (0, 0, cube_size, cube_size))
            pygame.draw.rect(cube_surf, (0, 0, 0), (0, 0, cube_size, cube_size), 4)
            m = int(cube_size * 0.16)
            pygame.draw.rect(cube_surf, (0, 200, 255), (m, m, cube_size - m*2, cube_size - m*2))
            pygame.draw.rect(cube_surf, (0, 0, 0), (m, m, cube_size - m*2, cube_size - m*2), 3)
            # Eye
            ew = int(cube_size * 0.16)
            pygame.draw.rect(cube_surf, (255, 255, 255), (int(cube_size*0.25), int(cube_size*0.25), ew, ew))
            pygame.draw.rect(cube_surf, (0, 0, 0), (int(cube_size*0.33), int(cube_size*0.27), int(ew*0.45), int(ew*0.7)))
            
            rotated = pygame.transform.rotate(cube_surf, spin_angle)
            r_rect = rotated.get_rect(center=(cx, cube_y_pos + cube_size//2))
            self.screen.blit(rotated, r_rect.topleft)
        
        # ====== PHASE 3 (4-8s): Title scales in ======
        if t > 4.0:
            title_t = min(1.0, (t - 4.0) / 1.5)
            title_fade = 1.0
            if t > 8.5:
                title_fade = max(0.0, 1.0 - (t - 8.5) / 1.0)
            
            font_size = int(20 + title_t * 55)
            title_font = pygame.font.SysFont("Arial", font_size, bold=True)
            
            title_str = "GEOMETRY DASH"
            # Glow backdrop
            glow_w = int(600 * title_t)
            glow_alpha = int(title_t * title_fade * 50)
            if glow_alpha > 0:
                glow_s = pygame.Surface((glow_w, 80), pygame.SRCALPHA)
                pygame.draw.rect(glow_s, (0, 120, 255, glow_alpha), (0, 0, glow_w, 80), border_radius=40)
                self.screen.blit(glow_s, (cx - glow_w//2, cy + 45))
            
            t_alpha = int(title_t * title_fade * 255)
            # Shadow
            ts_sh = title_font.render(title_str, True, (0, 0, 40))
            ts_sh.set_alpha(t_alpha)
            self.screen.blit(ts_sh, (cx - ts_sh.get_width()//2 + 3, cy + 58))
            # Main
            ts_m = title_font.render(title_str, True, (255, 255, 255))
            ts_m.set_alpha(t_alpha)
            self.screen.blit(ts_m, (cx - ts_m.get_width()//2, cy + 55))
            
            # Subtitle
            if title_t > 0.6:
                sub_t = min(1.0, (title_t - 0.6) / 0.4)
                sub_alpha = int(sub_t * title_fade * 255)
                sub_font = pygame.font.SysFont("Arial", 24)
                sub_s = sub_font.render("C  L  O  N  E", True, (80, 160, 255))
                sub_s.set_alpha(sub_alpha)
                self.screen.blit(sub_s, (cx - sub_s.get_width()//2, cy + 118))
        
        # ====== PHASE 4 (5.5-8.5s): Feature icons row ======
        if 5.5 < t < 9.0:
            feat_t = min(1.0, (t - 5.5) / 1.0)
            feat_fade = 1.0
            if t > 8.0:
                feat_fade = max(0.0, 1.0 - (t - 8.0) / 1.0)
            icons = [
                ("5 LEVELS", (80, 255, 120)),
                ("5 DIFFICULTIES", (255, 220, 0)),
                ("SHIP MODE", (0, 200, 255)),
                ("LEADERBOARD", (255, 100, 200)),
            ]
            icon_spacing = 220
            total_iw = (len(icons) - 1) * icon_spacing
            ix_start = cx - total_iw // 2
            for idx, (label, color) in enumerate(icons):
                delay = idx * 0.2
                if feat_t > delay / 1.0:
                    i_t = min(1.0, (feat_t - delay / 1.0) / 0.4)
                    i_alpha = int(i_t * feat_fade * 220)
                    ix = ix_start + idx * icon_spacing
                    iy = cy + 170
                    
                    # Colored dot
                    dot_s = pygame.Surface((14, 14), pygame.SRCALPHA)
                    pygame.draw.circle(dot_s, (*color, i_alpha), (7, 7), 7)
                    self.screen.blit(dot_s, (ix - 7, iy - 7))
                    
                    feat_font = pygame.font.SysFont("Arial", 16, bold=True)
                    f_s = feat_font.render(label, True, (220, 230, 255))
                    f_s.set_alpha(i_alpha)
                    self.screen.blit(f_s, (ix - f_s.get_width()//2, iy + 14))
        
        # ====== "Press any key" (after 6s) ======
        if t > 6.0:
            pk_fade = min(1.0, (t - 6.0) / 1.0)
            if t > 9.0:
                pk_fade *= max(0.0, 1.0 - (t - 9.0) / 1.0)
            blink = int((math.sin(t * 5) + 1) * 127)
            pk_alpha = int(pk_fade * blink)
            press_font = pygame.font.SysFont("Arial", 20)
            press_s = press_font.render("Press any key to continue...", True, (200, 220, 255))
            press_s.set_alpha(pk_alpha)
            self.screen.blit(press_s, (cx - press_s.get_width()//2, HEIGHT - 90))
        
        # ====== Progress bar ======
        bar_w = 400
        bar_h = 3
        bar_x = cx - bar_w // 2
        bar_y = HEIGHT - 50
        progress = min(1.0, t / 10.0)
        pygame.draw.rect(self.screen, (25, 25, 45), (bar_x, bar_y, bar_w, bar_h), border_radius=2)
        fill_w = int(bar_w * progress)
        if fill_w > 0:
            # Gradient fill
            for px in range(fill_w):
                ratio = px / bar_w
                pc = (int(0 + ratio * 100), int(150 + ratio * 100), 255)
                pygame.draw.line(self.screen, pc, (bar_x + px, bar_y), (bar_x + px, bar_y + bar_h))
        
        # Loading text
        load_font = pygame.font.SysFont("Arial", 14)
        load_s = load_font.render(f"Loading... {int(progress * 100)}%", True, (100, 120, 160))
        self.screen.blit(load_s, (cx - load_s.get_width()//2, bar_y + 10))

    def draw(self):
        bg_color = LEVEL_THEMES[self.current_level_idx]["bg"]
        self.screen.fill(bg_color)
        
        if self.state == "INTRO":
            self._draw_intro()
            pygame.display.flip()
            return
        
        if self.state == "LOGIN":
            # Deep space gradient background
            for y_line in range(0, HEIGHT, 2):
                t = y_line / HEIGHT
                r = int(5 + t * 10)
                g = int(5 + t * 8)
                b = int(30 + t * 60)
                pygame.draw.line(self.screen, (r, g, b), (0, y_line), (WIDTH, y_line), 2)
            
            # Starfield parallax
            for i in range(60):
                sx = (i * 137 + int(self.time_elapsed * (10 + i % 5))) % WIDTH
                sy = (i * 97 + int(self.time_elapsed * (5 + i % 3))) % HEIGHT
                size = 1 if i % 3 else 2
                alpha_val = 150 + int(math.sin(self.time_elapsed * 2 + i) * 55)
                pygame.draw.circle(self.screen, (255, 255, 255), (sx, sy), size)
            
            # Animated neon grid in bottom half
            grid_y_start = HEIGHT // 2
            vp_scroll = (self.time_elapsed * 40) % 60
            for i in range(-1, int(WIDTH / 60) + 2):
                xg = i * 60 - int(vp_scroll)
                pygame.draw.line(self.screen, (30, 0, 80), (xg, grid_y_start), (xg, HEIGHT), 1)
            for j in range(int((HEIGHT - grid_y_start) / 40) + 2):
                yg = grid_y_start + j * 40
                pygame.draw.line(self.screen, (30, 0, 80), (0, yg), (WIDTH, yg), 1)
            
            # Title - modern clean, single color
            bounce_y = int(math.sin(self.time_elapsed * 3) * 5)
            title_str = "GEOMETRY DASH"
            ts_shadow = self.title_font.render(title_str, True, (0, 0, 30))
            ts_main = self.title_font.render(title_str, True, (180, 240, 255))
            self.screen.blit(ts_shadow, (WIDTH // 2 - ts_shadow.get_width() // 2 + 2, 48 + bounce_y + 2))
            self.screen.blit(ts_main, (WIDTH // 2 - ts_main.get_width() // 2, 46 + bounce_y))
            sub_title = self.sub_font.render("C  L  O  N  E", True, (100, 140, 180))
            self.screen.blit(sub_title, (WIDTH // 2 - sub_title.get_width() // 2, 116 + bounce_y))
            
            # === MAIN PANEL ===
            panel_w, panel_h = 900, 470
            panel_x = WIDTH // 2 - panel_w // 2
            panel_y = 140
            
            # Outer glow
            glow_pulse = int((math.sin(self.time_elapsed * 4) + 1) * 5)
            glow_surf = pygame.Surface((panel_w + 30 + glow_pulse * 2, panel_h + 30 + glow_pulse * 2), pygame.SRCALPHA)
            pygame.draw.rect(glow_surf, (0, 180, 255, 30), (0, 0, glow_surf.get_width(), glow_surf.get_height()), border_radius=24)
            self.screen.blit(glow_surf, (panel_x - 15 - glow_pulse, panel_y - 15 - glow_pulse))
            
            # Panel body
            pygame.draw.rect(self.screen, (8, 10, 28), (panel_x, panel_y, panel_w, panel_h), border_radius=20)
            pygame.draw.rect(self.screen, (0, 140, 220), (panel_x, panel_y, panel_w, panel_h), 2, border_radius=20)
            
            # Modern gradient header strip inside panel
            header_h = 48
            for hx in range(panel_w):
                t = hx / panel_w
                hc = (int(0 + t * 20), int(80 + t * 60), int(180 + t * 60))
                pygame.draw.line(self.screen, hc, (panel_x + hx, panel_y), (panel_x + hx, panel_y + header_h))
            # Round top corners mask
            pygame.draw.rect(self.screen, (8, 10, 28), (panel_x, panel_y + header_h, panel_w, 8))
            pygame.draw.rect(self.screen, (0, 140, 220), (panel_x, panel_y, panel_w, header_h + 2), 2, border_radius=0)
            # Header label
            hdr_txt = self.menu_font.render("SELECT  YOUR  PROFILE", True, (255, 255, 255))
            self.screen.blit(hdr_txt, (panel_x + panel_w // 2 - hdr_txt.get_width() // 2, panel_y + header_h // 2 - hdr_txt.get_height() // 2))
            
            panel_y += header_h + 8  # shift content start below header
            
            # === LEFT: NEW PLAYER INPUT ===
            left_x = panel_x + 30
            left_w = 320
            
            new_label = self.menu_font.render("NEW PLAYER", True, (0, 255, 200))
            self.screen.blit(new_label, (left_x, panel_y + 25))
            pygame.draw.line(self.screen, (0, 255, 200), (left_x, panel_y + 65), (left_x + left_w, panel_y + 65), 2)
            
            # Input hint
            hint = self.small_font.render("Enter your name:", True, (160, 160, 200))
            self.screen.blit(hint, (left_x, panel_y + 80))
            
            # Textbox
            box_x = left_x
            box_y = panel_y + 105
            box_w, box_h = left_w, 52
            pulse_b = math.sin(self.time_elapsed * 6)
            border_col = (0, int(180 + pulse_b * 60), 255)
            pygame.draw.rect(self.screen, (20, 22, 50), (box_x, box_y, box_w, box_h), border_radius=10)
            pygame.draw.rect(self.screen, border_col, (box_x, box_y, box_w, box_h), 2, border_radius=10)
            
            name_surf = self.menu_font.render(self.username, True, (255, 255, 100))
            self.screen.blit(name_surf, (box_x + 12, box_y + 8))
            if int(self.time_elapsed * 2) % 2 == 0:
                cur_x = box_x + 14 + name_surf.get_width()
                pygame.draw.rect(self.screen, (255, 255, 255), (cur_x, box_y + 10, 2, 32))
            
            # Enter button - store rect for click detection
            btn_y = box_y + box_h + 18
            btn_rect = pygame.Rect(box_x, btn_y, box_w, 48)
            self._login_btn_rect = btn_rect
            btn_col = (0, 220, 80) if len(self.username) > 0 else (60, 60, 80)
            btn_border = (255, 255, 255) if len(self.username) > 0 else (80, 80, 100)
            pygame.draw.rect(self.screen, btn_col, btn_rect, border_radius=10)
            pygame.draw.rect(self.screen, btn_border, btn_rect, 2, border_radius=10)
            btn_txt = self.menu_font.render("START  ▶", True, (0, 0, 0) if len(self.username) > 0 else (80, 80, 80))
            self.screen.blit(btn_txt, (btn_rect.centerx - btn_txt.get_width() // 2, btn_rect.centery - btn_txt.get_height() // 2))
            
            enter_hint = self.small_font.render("Press ENTER or click Start", True, (100, 100, 140))
            self.screen.blit(enter_hint, (left_x, btn_y + 58))
            
            # === DIVIDER ===
            div_x = panel_x + left_w + 60
            pygame.draw.line(self.screen, (40, 60, 100), (div_x, panel_y + 20), (div_x, panel_y + panel_h - 20), 2)
            or_surf = self.small_font.render("OR", True, (100, 100, 160))
            self.screen.blit(or_surf, (div_x - or_surf.get_width() // 2, panel_y + panel_h // 2 - or_surf.get_height() // 2))
            
            # === RIGHT: PROFILE CARDS ===
            cards_x = div_x + 25
            cards_w = panel_x + panel_w - cards_x - 20
            
            hist_label = self.menu_font.render("PLAY HISTORY", True, (255, 200, 0))
            self.screen.blit(hist_label, (cards_x, panel_y + 25))
            pygame.draw.line(self.screen, (255, 200, 0), (cards_x, panel_y + 65), (cards_x + cards_w, panel_y + 65), 2)
            
            self._login_profile_rects = []
            
            existing_users = list(self.user_stats.keys())
            if not existing_users:
                no_hist = self.sub_font.render("No history yet.", True, (80, 80, 120))
                self.screen.blit(no_hist, (cards_x + 20, panel_y + 100))
            else:
                card_h = 72
                card_gap = 12
                max_visible = 4
                for idx, uname in enumerate(existing_users[:max_visible]):
                    cy = panel_y + 80 + idx * (card_h + card_gap)
                    card_rect = pygame.Rect(cards_x, cy, cards_w, card_h)
                    self._login_profile_rects.append((card_rect, uname))
                    
                    is_hovered = (self._login_hovered_card == idx)
                    card_bg = (30, 50, 100) if is_hovered else (18, 25, 55)
                    card_border = (0, 220, 255) if is_hovered else (50, 80, 140)
                    
                    pygame.draw.rect(self.screen, card_bg, card_rect, border_radius=12)
                    pygame.draw.rect(self.screen, card_border, card_rect, 2, border_radius=12)
                    
                    # Avatar circle
                    av_cx = cards_x + 38
                    av_cy = cy + card_h // 2
                    pygame.draw.circle(self.screen, (0, 150, 255), (av_cx, av_cy), 22)
                    pygame.draw.circle(self.screen, (255, 255, 255), (av_cx, av_cy), 22, 2)
                    init_char = uname[0].upper()
                    init_surf = self.menu_font.render(init_char, True, (255, 255, 255))
                    self.screen.blit(init_surf, (av_cx - init_surf.get_width() // 2, av_cy - init_surf.get_height() // 2))
                    
                    # Stats
                    stats = self.user_stats.get(uname, {})
                    stars_count = stats.get('stars', 0)
                    attempts = stats.get('attempts', 0)
                    best_pct = max(stats.get('best_maps', [0.0])) * 100
                    
                    uname_surf = self.menu_font.render(uname, True, (240, 240, 255))
                    self.screen.blit(uname_surf, (cards_x + 72, cy + 8))
                    
                    detail_str = f"Best: {best_pct:.0f}%   Stars: {stars_count}   Died: {attempts}x"
                    detail_surf = self.small_font.render(detail_str, True, (140, 160, 200))
                    self.screen.blit(detail_surf, (cards_x + 72, cy + 42))
                    
                    # Arrow
                    arr_surf = self.menu_font.render("▶", True, (0, 220, 255) if is_hovered else (60, 80, 120))
                    self.screen.blit(arr_surf, (cards_x + cards_w - arr_surf.get_width() - 12, av_cy - arr_surf.get_height() // 2))
                
                if len(existing_users) > max_visible:
                    more = self.small_font.render(f"+ {len(existing_users)-max_visible} more account(s)...", True, (80, 100, 150))
                    self.screen.blit(more, (cards_x, panel_y + 80 + max_visible * (card_h + card_gap)))
            
        elif self.state == "MENU":
            # Target Background Color based on difficulty selection
            target_diff = DIFFICULTIES[self.current_diff_idx]
            target_diff_color = target_diff.get("menu_color", (30, 80, 150))
            
            # Draw Dynamic Parallax Menu Background
            bg_scroll_x = self.time_elapsed * 100
            
            # Fill base
            self.screen.fill(target_diff_color)
            
            # Authentic Geometry Dash Parallax Background (Floating Squares and Pillars)
            for i in range(12):
                sq_x = (i * 150 - bg_scroll_x * 0.2) % (WIDTH + 100) - 50
                sq_y = (math.sin(i * 4.5) * 200) + HEIGHT // 2 - 100
                size = 30 + (i % 3) * 20
                c_val = min(255, target_diff_color[0] + 30)
                pygame.draw.rect(self.screen, (c_val, c_val, c_val, 40), (sq_x, sq_y, size, size), 2)
                
            # Floating Parallax Clouds/Pillars
            for i in range(10):
                px = (i * 350 - bg_scroll_x * 0.5) % (WIDTH + 200) - 100
                ph = 180 + (i % 4) * 80
                py = HEIGHT - 150 - ph
                dark_bg = (max(0, target_diff_color[0]-15), max(0, target_diff_color[1]-15), max(0, target_diff_color[2]-15))
                pygame.draw.rect(self.screen, dark_bg, (px, py, 140, ph))
                pygame.draw.rect(self.screen, (target_diff_color[0], target_diff_color[1], target_diff_color[2]), (px+5, py+5, 130, ph))
            
            # Subtle Background Grid
            grid_color = (min(255, target_diff_color[0]+20), min(255, target_diff_color[1]+20), min(255, target_diff_color[2]+20))
            grid_scroll = bg_scroll_x % 80
            for i in range(-1, int(WIDTH / 80) + 2):
                x_bg = i * 80 - grid_scroll
                pygame.draw.line(self.screen, grid_color, (x_bg, 0), (x_bg, HEIGHT - 150), 1)
            for j in range(int((HEIGHT - 150) / 80) + 1):
                y_bg = HEIGHT - 150 - j * 80
                pygame.draw.line(self.screen, grid_color, (0, y_bg), (WIDTH, y_bg), 1)

            # MENU Checkerboard Ground
            gnd_y = HEIGHT - 150
            ground_rect = pygame.Rect(0, gnd_y, WIDTH, 150)
            base_gnd = (max(0, target_diff_color[0]-30), max(0, target_diff_color[1]-30), max(0, target_diff_color[2]-30))
            alt_gnd = (max(0, base_gnd[0]-15), max(0, base_gnd[1]-15), max(0, base_gnd[2]-15))
            pygame.draw.rect(self.screen, base_gnd, ground_rect)
            
            TILE_SIZE = 80
            ground_scroll = bg_scroll_x % TILE_SIZE
            g_cols = int(WIDTH / TILE_SIZE) + 2
            g_rows = int(150 / TILE_SIZE) + 1
            
            for row in range(g_rows):
                foffset = (bg_scroll_x // TILE_SIZE)
                for col in range(-1, g_cols):
                    if (int(foffset) + col + row) % 2 == 0:
                        gx = col * TILE_SIZE - ground_scroll
                        gy = gnd_y + row * TILE_SIZE
                        pygame.draw.rect(self.screen, alt_gnd, (gx, gy, TILE_SIZE, TILE_SIZE))
            
            pygame.draw.line(self.screen, (255, 255, 255), (0, gnd_y), (WIDTH, gnd_y), 4)

            # ========= MENU LAYOUT (HEIGHT=720) =========
            # Title with glow
            bounce_y = int(math.sin(self.time_elapsed * 3.5) * 6)
            title_str = "GEOMETRY DASH"
            # Glow behind title
            glow_t = pygame.Surface((600, 80), pygame.SRCALPHA)
            pygame.draw.rect(glow_t, (255, 255, 255, 20), (0, 0, 600, 80), border_radius=40)
            self.screen.blit(glow_t, (WIDTH//2 - 300, 10 + bounce_y))
            ts_shadow = self.title_font.render(title_str, True, (0, 0, 0))
            self.screen.blit(ts_shadow, (WIDTH//2 - ts_shadow.get_width()//2 + 3, 22 + bounce_y + 3))
            ts_main = self.title_font.render(title_str, True, (255, 255, 255))
            self.screen.blit(ts_main, (WIDTH//2 - ts_main.get_width()//2, 20 + bounce_y))
            
            # Horizontal separator
            pygame.draw.line(self.screen, (255, 255, 255, 60), (WIDTH//2 - 300, 95), (WIDTH//2 + 300, 95), 1)
            
            # Level Select label
            i1_surf = self.sub_font.render("SELECT  LEVEL", True, (220, 230, 255))
            self.screen.blit(i1_surf, (WIDTH//2 - i1_surf.get_width()//2, 105))
            
            BOX_WIDTH, BOX_HEIGHT = 160, 120
            SPACING = 20
            total_width = 5 * BOX_WIDTH + 4 * SPACING
            start_x = WIDTH // 2 - total_width // 2
            map_y = 140
            diff_colors = [(80,255,120), (255,220,0), (255,120,60), (255,50,50), (180,80,255)]
            
            for i in range(5):
                m_x = start_x + i * (BOX_WIDTH + SPACING)
                rect = pygame.Rect(m_x, map_y, BOX_WIDTH, BOX_HEIGHT)
                card_col = diff_colors[i]
                
                if i == self.current_level_idx:
                    # Animated glow
                    glow_pulse = int((math.sin(self.time_elapsed * 4 + i) + 1) * 6)
                    glow_s = pygame.Surface((BOX_WIDTH + 30 + glow_pulse*2, BOX_HEIGHT + 30 + glow_pulse*2), pygame.SRCALPHA)
                    pygame.draw.rect(glow_s, (card_col[0], card_col[1], card_col[2], 80), (0, 0, glow_s.get_width(), glow_s.get_height()), border_radius=22)
                    self.screen.blit(glow_s, (m_x - 15 - glow_pulse, map_y - 15 - glow_pulse))
                    
                    # Card body gradient simulation
                    pygame.draw.rect(self.screen, card_col, rect, border_radius=16)
                    # Highlight top half
                    hl_s = pygame.Surface((BOX_WIDTH, BOX_HEIGHT//2), pygame.SRCALPHA)
                    pygame.draw.rect(hl_s, (255, 255, 255, 50), (0, 0, BOX_WIDTH, BOX_HEIGHT//2), border_radius=16)
                    self.screen.blit(hl_s, (m_x, map_y))
                    pygame.draw.rect(self.screen, (255, 255, 255), rect, 4, border_radius=16)
                    text_color = (0, 0, 0)
                else:
                    # Dark card
                    card_s = pygame.Surface((BOX_WIDTH, BOX_HEIGHT), pygame.SRCALPHA)
                    pygame.draw.rect(card_s, (15, 18, 30, 220), (0, 0, BOX_WIDTH, BOX_HEIGHT), border_radius=16)
                    self.screen.blit(card_s, (m_x, map_y))
                    pygame.draw.rect(self.screen, (card_col[0]//3, card_col[1]//3, card_col[2]//3), rect, 2, border_radius=16)
                    text_color = (card_col[0]//2+40, card_col[1]//2+40, card_col[2]//2+40)
                
                # Level number
                num_surf = self.menu_font.render(str(i+1), True, text_color)
                self.screen.blit(num_surf, (m_x + BOX_WIDTH//2 - num_surf.get_width()//2, map_y + 15))
                
                # Level name
                level_names = ["STEREO", "BACK ON", "POLAR", "DRY OUT", "BASE"]
                name_col = text_color if i == self.current_level_idx else (80, 90, 110)
                nm_surf = self.small_font.render(level_names[i], True, name_col)
                self.screen.blit(nm_surf, (m_x + BOX_WIDTH//2 - nm_surf.get_width()//2, map_y + 52))
                
                # Progress percentage
                map_progress = 0
                if self.current_user:
                    stats = self.get_current_stats()
                    map_progress = stats['best_maps'][i] * 100
                    
                prog_str = f"{map_progress:.0f}%"
                if map_progress >= 100:
                    prog_col = (50, 255, 100)
                elif i == self.current_level_idx:
                    prog_col = (255, 255, 255)
                else:
                    prog_col = (130, 140, 170)
                
                p_txt = self.sub_font.render(prog_str, True, prog_col)
                p_txt_x = m_x + BOX_WIDTH//2 - p_txt.get_width()//2
                p_txt_y = map_y + BOX_HEIGHT - 42
                
                # Dark pill behind %
                pill_s = pygame.Surface((p_txt.get_width() + 20, p_txt.get_height() + 6), pygame.SRCALPHA)
                pygame.draw.rect(pill_s, (0, 0, 0, 200), (0, 0, pill_s.get_width(), pill_s.get_height()), border_radius=12)
                self.screen.blit(pill_s, (p_txt_x - 10, p_txt_y - 3))
                self.screen.blit(p_txt, (p_txt_x, p_txt_y))
                
                # Progress bar
                bar_w = BOX_WIDTH - 24
                bar_x = m_x + 12
                bar_y = map_y + BOX_HEIGHT - 12
                pygame.draw.rect(self.screen, (20,20,20), (bar_x, bar_y, bar_w, 6), border_radius=3)
                if map_progress > 0:
                    fill_col = (0, 255, 120) if map_progress >= 100 else (0, 200, 255)
                    pygame.draw.rect(self.screen, fill_col, (bar_x, bar_y, int(bar_w * min(1.0, map_progress/100.0)), 6), border_radius=3)
            
            # Horizontal separator
            pygame.draw.line(self.screen, (255, 255, 255, 40), (WIDTH//2 - 350, 275), (WIDTH//2 + 350, 275), 1)
            
            # Difficulty Selector
            lx = WIDTH//2 - 250
            rx = WIDTH//2 + 250
            arr_y = 340
            # Animated arrows
            arr_pulse = int(math.sin(self.time_elapsed * 6) * 4)
            pygame.draw.polygon(self.screen, (255, 255, 255), [(lx - arr_pulse, arr_y), (lx+22, arr_y-16), (lx+22, arr_y+16)])
            pygame.draw.polygon(self.screen, (255, 255, 255), [(rx + arr_pulse, arr_y), (rx-22, arr_y-16), (rx-22, arr_y+16)])
            
            # Difficulty icon / Face drawing
            dx, dy = WIDTH//2, 340
            d_rad = 38
            # Shadow
            pygame.draw.circle(self.screen, (0, 0, 0, 80), (dx+3, dy+3), d_rad+5)
            pygame.draw.circle(self.screen, (0, 0, 0), (dx, dy), d_rad+4)
            d_color = diff_colors[self.current_diff_idx]
            pygame.draw.circle(self.screen, d_color, (dx, dy), d_rad)
            pygame.draw.circle(self.screen, (255, 255, 255), (dx, dy), d_rad, 3)
            
            # Faces
            if self.current_diff_idx == 0:
                pygame.draw.circle(self.screen, (0,0,0), (dx-14, dy-9), 5)
                pygame.draw.circle(self.screen, (0,0,0), (dx+14, dy-9), 5)
                pygame.draw.arc(self.screen, (0,0,0), (dx-16, dy-10, 32, 32), 3.14, 0, 4)
            elif self.current_diff_idx == 1:
                pygame.draw.circle(self.screen, (0,0,0), (dx-14, dy-9), 5)
                pygame.draw.circle(self.screen, (0,0,0), (dx+14, dy-9), 5)
                pygame.draw.line(self.screen, (0,0,0), (dx-14, dy+11), (dx+14, dy+11), 4)
            elif self.current_diff_idx == 2:
                pygame.draw.line(self.screen, (0,0,0), (dx-18, dy-14), (dx-6, dy-6), 4)
                pygame.draw.line(self.screen, (0,0,0), (dx+18, dy-14), (dx+6, dy-6), 4)
                pygame.draw.circle(self.screen, (0,0,0), (dx-11, dy-4), 4)
                pygame.draw.circle(self.screen, (0,0,0), (dx+11, dy-4), 4)
                pygame.draw.arc(self.screen, (0,0,0), (dx-16, dy+10, 32, 22), 0, 3.14, 4)
            elif self.current_diff_idx == 3:
                pygame.draw.line(self.screen, (0,0,0), (dx-20, dy-16), (dx-6, dy-4), 5)
                pygame.draw.line(self.screen, (0,0,0), (dx+20, dy-16), (dx+6, dy-4), 5)
                pygame.draw.circle(self.screen, (0,0,0), (dx-11, dy-4), 4)
                pygame.draw.circle(self.screen, (0,0,0), (dx+11, dy-4), 4)
                pygame.draw.polygon(self.screen, (0,0,0), [(dx-16, dy+16), (dx-6, dy+9), (dx+6, dy+16), (dx+16, dy+9), (dx+26, dy+16)])
            elif self.current_diff_idx == 4:
                pygame.draw.polygon(self.screen, (200,0,0), [(dx-28, dy-28), (dx-14, dy-38), (dx-16, dy-16)])
                pygame.draw.polygon(self.screen, (200,0,0), [(dx+28, dy-28), (dx+14, dy-38), (dx+16, dy-16)])
                pygame.draw.polygon(self.screen, (0,0,0), [(dx-20, dy-16), (dx-6, dy-4), (dx-14, dy-2)])
                pygame.draw.polygon(self.screen, (0,0,0), [(dx+20, dy-16), (dx+6, dy-4), (dx+14, dy-2)])
                pygame.draw.arc(self.screen, (0,0,0), (dx-22, dy+6, 44, 22), 0, 3.14, 6)

            diff_name = self.menu_font.render(target_diff["name"], True, (255, 255, 255))
            # Shadow
            dns = self.menu_font.render(target_diff["name"], True, (0, 0, 0))
            self.screen.blit(dns, (dx - dns.get_width()//2 + 2, dy + 48 + 2))
            self.screen.blit(diff_name, (dx - diff_name.get_width()//2, dy + 48))
            
            # Key hint
            key_hint = self.small_font.render("← →  CHANGE DIFFICULTY", True, (180, 200, 240))
            self.screen.blit(key_hint, (WIDTH//2 - key_hint.get_width()//2, dy + 85))
            
            # ---- USER STATS PANEL ----
            if self.current_user:
                stats = self.get_current_stats()
                panel_w, panel_h = 620, 55
                panel_x = WIDTH // 2 - panel_w // 2
                panel_y = 450
                
                # Glass background
                p_surf = pygame.Surface((panel_w, panel_h), pygame.SRCALPHA)
                pygame.draw.rect(p_surf, (0, 0, 0, 190), (0, 0, panel_w, panel_h), border_radius=18)
                self.screen.blit(p_surf, (panel_x, panel_y))
                pygame.draw.rect(self.screen, (0, 200, 255), (panel_x, panel_y, panel_w, panel_h), 2, border_radius=18)
                
                # User name
                usr_txt = self.menu_font.render(self.current_user, True, (0, 255, 255))
                self.screen.blit(usr_txt, (panel_x + 25, panel_y + panel_h//2 - usr_txt.get_height()//2))
                
                # Dynamic divider position based on username width
                div_x = panel_x + 25 + usr_txt.get_width() + 20
                pygame.draw.line(self.screen, (0, 180, 220), (div_x, panel_y + 12), (div_x, panel_y + panel_h - 12), 2)
                
                stat_str = f"ATTEMPTS: {stats['attempts']}      STARS: {stats['stars']}      WINS: {stats.get('wins', 0)}"
                stat_surf = self.small_font.render(stat_str, True, (200, 220, 255))
                self.screen.blit(stat_surf, (div_x + 18, panel_y + panel_h//2 - stat_surf.get_height()//2))
            
            # ---- PLAY BUTTON: y=490..570 ----
            play_y = 520
            pulse_a = max(80, int((math.sin(self.time_elapsed * 6) + 1) * 127))
            cx, cy = WIDTH // 2, play_y + 25
            ring_r = 40 + int(math.sin(self.time_elapsed * 5) * 3)
            ring_s = pygame.Surface((ring_r*2+20, ring_r*2+20), pygame.SRCALPHA)
            pygame.draw.circle(ring_s, (0, 255, 100, 50), (ring_r+10, ring_r+10), ring_r+8)
            self.screen.blit(ring_s, (cx-ring_r-10, cy-ring_r-10))
            pygame.draw.circle(self.screen, (0, 160, 50), (cx, cy), ring_r)
            pygame.draw.circle(self.screen, (180, 255, 180), (cx, cy), ring_r, 3)
            pygame.draw.polygon(self.screen, (255, 255, 255), [(cx-10, cy-18), (cx-10, cy+18), (cx+22, cy)])
            play_txt = self.small_font.render("PRESS SPACE  /  CLICK  TO  PLAY", True, (180, 255, 180))
            play_txt.set_alpha(pulse_a)
            self.screen.blit(play_txt, (WIDTH//2 - play_txt.get_width()//2, play_y + 60))
            
            # ---- CONTROLS HINT BAR at bottom ----
            hint_y = HEIGHT - 40
            hint_bg = pygame.Surface((WIDTH, 45), pygame.SRCALPHA)
            pygame.draw.rect(hint_bg, (0, 0, 0, 140), (0, 0, WIDTH, 45))
            self.screen.blit(hint_bg, (0, hint_y - 5))
            controls = [
                ("[1-5]", "Select Map"),
                ("[← →]", "Difficulty"),
                ("[SPACE]", "Play / Jump"),
                ("[CLICK]", "Jump / Fly"),
                ("[ESC]", "Back"),
            ]
            total_cw = 0
            items = []
            for key, desc in controls:
                k_s = self.small_font.render(key, True, (0, 255, 200))
                d_s = self.small_font.render(f" {desc}", True, (180, 190, 220))
                items.append((k_s, d_s, k_s.get_width() + d_s.get_width()))
                total_cw += k_s.get_width() + d_s.get_width()
            spacing = 30
            total_cw += spacing * (len(items) - 1)
            cx_start = WIDTH // 2 - total_cw // 2
            for k_s, d_s, iw in items:
                self.screen.blit(k_s, (cx_start, hint_y + 2))
                self.screen.blit(d_s, (cx_start + k_s.get_width(), hint_y + 2))
                cx_start += iw + spacing
            
        elif self.state == "POPUP":
            # Background: draw game level dimmed
            self.screen.fill(bg_color)
            overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 200))
            self.screen.blit(overlay, (0, 0))
            
            # Authentic GD How to Play Popup (Brown box with gold border)
            pop_w, pop_h = 800, 480
            pop_x, pop_y = WIDTH // 2 - pop_w // 2, HEIGHT // 2 - pop_h // 2
            
            # Card body
            pygame.draw.rect(self.screen, (60, 30, 15), (pop_x, pop_y, pop_w, pop_h), border_radius=15)
            # Inner border
            pygame.draw.rect(self.screen, (100, 60, 30), (pop_x+5, pop_y+5, pop_w-10, pop_h-10), 3, border_radius=12)
            # Outer Gold border
            pygame.draw.rect(self.screen, (255, 200, 50), (pop_x, pop_y, pop_w, pop_h), 5, border_radius=15)
            
            # Header title
            pop_title = self.title_font.render("How to Play", True, (255, 255, 255))
            for ox, oy in [(-2,-2), (2,-2), (-2,2), (2,2), (0,3)]:
                self.screen.blit(self.title_font.render("How to Play", True, (0,0,0)), (WIDTH // 2 - pop_title.get_width() // 2 + ox, pop_y + 15 + oy))
            self.screen.blit(pop_title, (WIDTH // 2 - pop_title.get_width() // 2, pop_y + 15))
            
            content_y = pop_y + 100
            
            # --- Section 1: CUBE MODE ---
            sec1_x = pop_x + 40
            sec1_w = pop_w // 2 - 60
            sec1_h = 160
            
            # Box bg
            pygame.draw.rect(self.screen, (40, 20, 10), (sec1_x, content_y, sec1_w, sec1_h), border_radius=10)
            pygame.draw.rect(self.screen, (80, 40, 20), (sec1_x, content_y, sec1_w, sec1_h), 2, border_radius=10)
            
            # Illustration: player cube jumping over spike
            il_y = content_y + 110
            pygame.draw.line(self.screen, (255, 255, 255), (sec1_x + 20, il_y), (sec1_x + sec1_w - 20, il_y), 3)
            spike_color = (200, 200, 200)
            pygame.draw.polygon(self.screen, spike_color, [
                (sec1_x + sec1_w // 2 + 30, il_y),
                (sec1_x + sec1_w // 2 + 10, il_y),
                (sec1_x + sec1_w // 2 + 20, il_y - 25)])
            pygame.draw.polygon(self.screen, (0,0,0), [
                (sec1_x + sec1_w // 2 + 30, il_y),
                (sec1_x + sec1_w // 2 + 10, il_y),
                (sec1_x + sec1_w // 2 + 20, il_y - 25)], 2)
            pygame.draw.rect(self.screen, (255, 255, 0), (sec1_x + 40, il_y - 30, 28, 28))
            pygame.draw.rect(self.screen, (0, 200, 255), (sec1_x + 46, il_y - 24, 16, 16))
            pygame.draw.rect(self.screen, (0,0,0), (sec1_x + 40, il_y - 30, 28, 28), 2)
            pygame.draw.arc(self.screen, (0, 255, 0), (sec1_x + 38, il_y - 65, 80, 60), 0, 3.14, 3)
            
            # Text
            key1 = self.small_font.render("Click / Space to jump over spikes", True, (255, 255, 255))
            self.screen.blit(key1, (sec1_x + sec1_w // 2 - key1.get_width() // 2, content_y + 20))
            
            # --- Section 2: SHIP MODE ---
            sec2_x = pop_x + pop_w // 2 + 20
            sec2_w = sec1_w
            sec2_h = sec1_h
            
            pygame.draw.rect(self.screen, (40, 20, 10), (sec2_x, content_y, sec2_w, sec2_h), border_radius=10)
            pygame.draw.rect(self.screen, (80, 40, 20), (sec2_x, content_y, sec2_w, sec2_h), 2, border_radius=10)
            
            il2_y = content_y + 90
            pygame.draw.line(self.screen, (255, 255, 255), (sec2_x + 20, il2_y - 45), (sec2_x + sec2_w - 20, il2_y - 45), 3)
            pygame.draw.line(self.screen, (255, 255, 255), (sec2_x + 20, il2_y + 45), (sec2_x + sec2_w - 20, il2_y + 45), 3)
            # Ship body
            pygame.draw.polygon(self.screen, (255,255,0), [
                (sec2_x + 40, il2_y - 12), (sec2_x + 75, il2_y), (sec2_x + 40, il2_y + 12)])
            pygame.draw.polygon(self.screen, (0,0,0), [
                (sec2_x + 40, il2_y - 12), (sec2_x + 75, il2_y), (sec2_x + 40, il2_y + 12)], 2)
            # Animated sine path dots
            for si in range(12):
                dpx = sec2_x + 80 + si * 12
                dpy = int(il2_y + math.sin(si * 0.6 - self.time_elapsed * 5) * 20)
                pygame.draw.circle(self.screen, (0, 255, 0), (dpx, dpy), 3)
            
            key2 = self.small_font.render("Hold to fly up, release to fall", True, (255, 255, 255))
            self.screen.blit(key2, (sec2_x + sec2_w // 2 - key2.get_width() // 2, content_y + 20))
            
            # --- Bottom section (Orbs) ---
            orb_y = content_y + sec1_h + 20
            pygame.draw.rect(self.screen, (40, 20, 10), (sec1_x, orb_y, pop_w - 80, 80), border_radius=10)
            pygame.draw.rect(self.screen, (80, 40, 20), (sec1_x, orb_y, pop_w - 80, 80), 2, border_radius=10)
            
            # Orb Icon
            orb_x = sec1_x + 60
            pygame.draw.circle(self.screen, (255, 200, 0), (orb_x, orb_y + 40), 16)
            pygame.draw.circle(self.screen, (255, 255, 255), (orb_x, orb_y + 40), 8)
            pygame.draw.circle(self.screen, (0, 0, 0), (orb_x, orb_y + 40), 16, 2)
            pygame.draw.circle(self.screen, (255, 200, 0), (orb_x, orb_y + 40), 22, 2)
            
            tip1 = self.menu_font.render("Hit yellow rings to jump in mid-air", True, (255, 255, 255))
            self.screen.blit(tip1, (orb_x + 50, orb_y + 40 - tip1.get_height() // 2))
            
            # --- Start pulse button ---
            pulse_a = max(100, int((math.sin(self.time_elapsed * 8) + 1) * 127))
            start_txt = self.menu_font.render("PRESS SPACE TO RESUME", True, (0, 255, 100))
            start_txt.set_alpha(pulse_a)
            self.screen.blit(start_txt, (WIDTH // 2 - start_txt.get_width() // 2, pop_y + pop_h + 20))
            
        elif self.state in ("PLAYING", "FINISHING_GLIDE", "FINISHING_EFFECT"):
            dt = getattr(self, 'last_dt', 0.0)
            self.level.draw(self.screen, self.camera_scroll_x, dt)
            
            if self.state in ("PLAYING", "FINISHING_GLIDE"):
                self.player.draw(self.screen, self.camera_scroll_x)
            elif self.state == "FINISHING_EFFECT":
                for p in self.win_particles:
                    if p.size > 0:
                        screen_x = p.x - self.camera_scroll_x
                        if p.p_type == "ring":
                            pygame.draw.circle(self.screen, p.color, (int(screen_x), int(p.y)), int(p.size), max(1, 15 - int(p.size/100)))
                        elif p.p_type == "ray":
                            angle = math.atan2(p.vy, p.vx)
                            end_x = screen_x + math.cos(angle) * p.size
                            end_y = p.y + math.sin(angle) * p.size
                            pygame.draw.line(self.screen, p.color, (screen_x, p.y), (end_x, end_y), 6)
                        else:
                            rect = pygame.Rect(screen_x, p.y, p.size, p.size)
                            pygame.draw.rect(self.screen, p.color, rect)
                            
            # Authentic Geometry Dash Attempt text at center start
            if self.state == "PLAYING" and self.current_run_time < 3.0:
                fade_alpha = 255
                if self.current_run_time > 1.5:
                    fade_alpha = max(0, int(255 * (1.0 - (self.current_run_time - 1.5) / 1.5)))
                if fade_alpha > 0:
                    att_n = self.get_current_stats()['attempts'] + 1
                    att_str = f"Attempt {att_n}"
                    
                    ats_shadow = self.title_font.render(att_str, True, (0, 0, 0))
                    ats_shadow.set_alpha(fade_alpha)
                    self.screen.blit(ats_shadow, (WIDTH // 2 - ats_shadow.get_width() // 2 + 4, HEIGHT // 2 - 100 + 4))
                    
                    ats = self.title_font.render(att_str, True, (255, 255, 255))
                    ats.set_alpha(fade_alpha)
                    self.screen.blit(ats, (WIDTH // 2 - ats.get_width() // 2, HEIGHT // 2 - 100))
            
            # Phase 7: Progress Bar Integration (Strict Flat Vector)
            bar_width = 400
            bar_height = 15
            bar_x = WIDTH // 2 - bar_width // 2
            bar_y = 30
            
            progress = min(1.0, max(0.0, self.player.x / self.level.total_width)) if self.level.total_width > 0 else 0
            
            # Background
            bg_rect = pygame.Rect(bar_x, bar_y, bar_width, bar_height)
            pygame.draw.rect(self.screen, (30, 30, 30), bg_rect)
            # Fill indicator
            fill_rect = pygame.Rect(bar_x, bar_y, int(bar_width * progress), bar_height)
            pygame.draw.rect(self.screen, (0, 200, 255), fill_rect) # Cyan GD style
            # 2px Strict Outline
            pygame.draw.rect(self.screen, (0, 0, 0), bg_rect, 2)
            
            # Format percentage without leading zeros (e.g. 5.0% or 100.0%)
            pct_str = f"{progress * 100:.1f}%"
            
            # Draw strong 2px outline for text readability
            for ox, oy in [(-2,-2), (2,-2), (-2,2), (2,2), (-2,0), (2,0), (0,-2), (0,2)]:
                outline = self.sub_font.render(pct_str, True, (0, 0, 0))
                self.screen.blit(outline, (bar_x + bar_width + 15 + ox, bar_y - (outline.get_height() - bar_height) // 2 + oy))
            
            # Draw core white text
            text = self.sub_font.render(pct_str, True, (255, 255, 255))
            self.screen.blit(text, (bar_x + bar_width + 15, bar_y - (text.get_height() - bar_height) // 2))
            
            # --- HUD STAR COUNTER (Top-Right Corner Glassmorphism Pill) ---
            star_pulse_scale = 1.0 + max(0, self.star_hud_pulse) * 0.5
            
            # Pill at top-right corner
            pill_w, pill_h = 130, 38
            pill_x = WIDTH - pill_w - 14
            pill_y = 14
            
            # Background glass pill
            pill_surf = pygame.Surface((pill_w, pill_h), pygame.SRCALPHA)
            pygame.draw.rect(pill_surf, (0, 0, 0, 160), (0, 0, pill_w, pill_h), border_radius=pill_h // 2)
            self.screen.blit(pill_surf, (pill_x, pill_y))
            
            # Neon gold border
            border_col_hud = (255, min(255, 200 + (50 if self.star_hud_pulse > 0 else 0)), 0)
            pygame.draw.rect(self.screen, border_col_hud, (pill_x, pill_y, pill_w, pill_h), 2, border_radius=pill_h // 2)
            
            # Spinning star inside pill
            star_cx = pill_x + 22
            star_cy = pill_y + pill_h // 2
            star_rad_hud = int(11 * star_pulse_scale)
            star_angle = self.time_elapsed * 90
            star_pts = []
            for i in range(10):
                r = star_rad_hud if i % 2 == 0 else star_rad_hud * 0.42
                theta = math.radians(star_angle + i * 36 - 90)
                star_pts.append((star_cx + math.cos(theta) * r, star_cy + math.sin(theta) * r))
            if self.star_hud_pulse > 0:
                pygame.draw.circle(self.screen, (255, 255, 100), (star_cx, star_cy), star_rad_hud + 5)
            pygame.draw.polygon(self.screen, (255, 220, 0), star_pts)
            pygame.draw.polygon(self.screen, (180, 120, 0), star_pts, 1)
            
            # Count text
            star_str = f"x {self.run_total_stars}"
            x_surf = self.menu_font.render(star_str, True, (255, 255, 255))
            self.screen.blit(x_surf, (pill_x + 40, pill_y + pill_h // 2 - x_surf.get_height() // 2))
            
        elif self.state == "DEATH":
            self.level.draw(self.screen, self.camera_scroll_x)
            # Draw Strict Flat Particles (no gradients, 2px precise black borders)
            for p in self.particles:
                if p.size > 0:
                    screen_x = p.x - self.camera_scroll_x
                    rect = pygame.Rect(screen_x, p.y, p.size, p.size)
                    pygame.draw.rect(self.screen, p.color, rect)
                    pygame.draw.rect(self.screen, (0, 0, 0), rect, 1)
                
        elif self.state == "COMPLETE":
            self.level.draw(self.screen, self.camera_scroll_x)
            
            # Draw Level Complete overlay text
            title_text = self.menu_font.render("LEVEL COMPLETE!", True, (46, 204, 113))
            sub_text = self.sub_font.render("Press SPACE to Continue", True, (200, 200, 200))
            self.screen.blit(title_text, (WIDTH//2 - title_text.get_width()//2, HEIGHT//2 - 50))
            self.screen.blit(sub_text, (WIDTH//2 - sub_text.get_width()//2, HEIGHT//2 + 20))
            
        elif self.state == "POST_GAME":
            self.level.draw(self.screen, self.camera_scroll_x)
            # Subtle Dimming Overlay
            overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 170))
            self.screen.blit(overlay, (0, 0))
            
            pop_w, pop_h = 500, 320
            
            is_win = self.last_run_pct >= 100
            
            if is_win:
                float_y = math.sin(self.time_elapsed * 3) * 10
                pop_x, pop_y = WIDTH // 2 - pop_w // 2, int(HEIGHT // 2 - pop_h // 2 + float_y)
                color = (255, 200, 0) # Gold
                title = "LEVEL COMPLETED!"
                # Draw Confetti/Sparks ONLY for WIN
                for i in range(25):
                    sx = WIDTH // 2 + math.cos(self.time_elapsed * 2 + i) * (200 + i*10)
                    sy = HEIGHT // 2 + math.sin(self.time_elapsed * 3 + i) * (150 + (i%5)*20) + float_y
                    pygame.draw.circle(self.screen, (255, 255, 100), (int(sx), int(sy)), 3)
                    
                # Draw Card Body inside Popup for WIN
                pygame.draw.rect(self.screen, (20, 20, 25), (pop_x, pop_y, pop_w, pop_h), border_radius=15)
                pygame.draw.rect(self.screen, color, (pop_x, pop_y, pop_w, pop_h), 4, border_radius=15)
            else:
                pop_x, pop_y = WIDTH // 2 - pop_w // 2, HEIGHT // 2 - pop_h // 2
                color = (255, 60, 60) # Red
                title = "GAME OVER"
                
                # Glow pulse effect restored ONLY for DEATH
                glow_pulse = int((math.sin(self.time_elapsed * 5) + 1) * 20)
                pygame.draw.rect(self.screen, (color[0], color[1], color[2], 50), (pop_x - 10 - glow_pulse, pop_y - 10 - glow_pulse, pop_w + 20 + glow_pulse*2, pop_h + 20 + glow_pulse*2), border_radius=20)
                
                # Draw Card Body inside Popup for DEATH
                pygame.draw.rect(self.screen, (20, 25, 40), (pop_x, pop_y, pop_w, pop_h), border_radius=15)
                pygame.draw.rect(self.screen, color, (pop_x, pop_y, pop_w, pop_h), 4, border_radius=15)
            
            # Title
            t_surf = self.title_font.render(title, True, color)
            for ox, oy in [(-2,0), (2,0), (0,-2), (0,2)]:
                self.screen.blit(self.title_font.render(title, True, (0,0,0)), (WIDTH // 2 - t_surf.get_width() // 2 + ox, pop_y + 25 + oy))
            self.screen.blit(t_surf, (WIDTH // 2 - t_surf.get_width() // 2, pop_y + 25))
            
            # Geometry Dash style progress bar inside the popup
            bar_w = 400
            bar_h = 24
            bar_x = WIDTH // 2 - bar_w // 2
            bar_y = pop_y + 140
            
            pygame.draw.rect(self.screen, (10, 10, 10), (bar_x, bar_y, bar_w, bar_h), border_radius=12)
            fill_w = int((self.last_run_pct / 100.0) * bar_w)
            if fill_w > 0:
                pygame.draw.rect(self.screen, color, (bar_x, bar_y, fill_w, bar_h), border_radius=12)
            pygame.draw.rect(self.screen, (255, 255, 255), (bar_x, bar_y, bar_w, bar_h), 2, border_radius=12)
            
            pct_surf = self.menu_font.render(f"{self.last_run_pct:.1f}%", True, (255,255,255))
            for ox, oy in [(-2,-2), (2,2), (-2,2), (2,-2)]:
                self.screen.blit(self.menu_font.render(f"{self.last_run_pct:.1f}%", True, (0,0,0)), (WIDTH // 2 - pct_surf.get_width() // 2 + ox, bar_y - 35 + oy))
            self.screen.blit(pct_surf, (WIDTH // 2 - pct_surf.get_width() // 2, bar_y - 35))
            
            # Balanced Grid Stats (Time, Attempts, Stars)
            font_stat = self.menu_font
            grid_y = pop_y + 190
            
            att_txt = font_stat.render(f"Attempts: {self.get_current_stats()['attempts']}", True, (200, 200, 200))
            self.screen.blit(att_txt, (WIDTH // 2 - att_txt.get_width() // 2, grid_y))
            
            time_txt = font_stat.render(f"Time: {self.current_run_time:.1f}s", True, (200, 200, 200))
            self.screen.blit(time_txt, (WIDTH // 2 - time_txt.get_width() // 2, grid_y + 35))
            
            star_txt = font_stat.render(f"Stars Collected: {self.last_run_stars}", True, (255, 255, 50))
            self.screen.blit(star_txt, (WIDTH // 2 - star_txt.get_width() // 2, grid_y + 70))
            
            # Action text
            pulse_a = max(80, int((math.sin(self.time_elapsed * 8) + 1) * 127))
            act = self.sub_font.render("Press SPACE to Play | ESC to Menu", True, (255, 255, 255))
            act.set_alpha(pulse_a)
            self.screen.blit(act, (WIDTH // 2 - act.get_width() // 2, pop_y + pop_h - 40))
                
        pygame.display.flip()

if __name__ == "__main__":
    game = Game()
    game.run()
