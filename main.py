import pygame
import random
import time
import math
import os
import asyncio  # <--- 加上这一句
# --- Constants & Configuration ---
FPS = 60
GRID_ROWS = 5
GRID_COLS = 9
CELL_WIDTH = 80
CELL_HEIGHT = 80

UI_HEIGHT = 120 
GRID_START_Y = UI_HEIGHT + 15
BOTTOM_UI_HEIGHT = 55
SCREEN_WIDTH = GRID_COLS * CELL_WIDTH
SCREEN_HEIGHT = GRID_START_Y + (GRID_ROWS * CELL_HEIGHT) + BOTTOM_UI_HEIGHT

C_BG = (20, 160, 50)
C_GRID_ALT = (25, 180, 60)
C_UI_PANEL = (60, 40, 20)

STATE_MENU, STATE_PLAYING, STATE_GAME_OVER, STATE_VICTORY, STATE_PAUSED, STATE_HELP, STATE_LEVEL_SELECT, STATE_REVIVAL_SEQUENCE, STATE_SEED_SELECTION = range(9)

# --- High-Fidelity 3D Graphics Helpers ---
def shade(color, amount):
    return tuple(max(0, min(255, int(c + amount))) for c in color)

def draw_sphere(surface, color, x, y, radius, scale_x=1.0, scale_y=1.0):
    for i in range(5, 0, -1):
        r = radius * (i / 5.0)
        c = shade(color, (5 - i) * 15 - 20) 
        offset = radius * 0.15 * ((5-i)/5.0) 
        rect = pygame.Rect(x - r*scale_x - offset, y - r*scale_y - offset, r*2*scale_x, r*2*scale_y)
        pygame.draw.ellipse(surface, c, rect)

def draw_3d_rect(surface, color, rect, border_radius=0):
    pygame.draw.rect(surface, shade(color, -40), rect, border_radius=border_radius)
    hl_rect = pygame.Rect(rect.left + 1, rect.top + 1, max(1, rect.width - 2), max(1, rect.height - 4))
    pygame.draw.rect(surface, color, hl_rect, border_radius=border_radius)
    hl_light = pygame.Rect(rect.left + 2, rect.top + 2, max(1, rect.width//3), max(1, rect.height - 6))
    pygame.draw.rect(surface, shade(color, 40), hl_light, border_radius=border_radius)

def draw_eye(surface, x, y, radius, angry=False, sad=False):
    pygame.draw.circle(surface, (255, 255, 255), (int(x), int(y)), radius)
    pygame.draw.circle(surface, (0, 0, 0), (int(x + radius*0.2), int(y)), int(radius * 0.5))
    pygame.draw.circle(surface, (255, 255, 255), (int(x + radius*0.3), int(y - radius*0.2)), int(radius * 0.2))
    if angry: pygame.draw.line(surface, (0, 0, 0), (x - radius*1.2, y - radius*0.8), (x + radius*1.2, y - radius*0.2), 2)
    if sad: pygame.draw.line(surface, (0, 0, 0), (x - radius*1.2, y - radius*0.2), (x + radius*1.2, y - radius*0.8), 2)

def draw_leaf(surface, color, x, y, w, h, angle):
    surf = pygame.Surface((w, h), pygame.SRCALPHA)
    pygame.draw.ellipse(surf, shade(color, -20), (0, 0, w, h))
    pygame.draw.ellipse(surf, color, (1, 1, w-2, h-3))
    pygame.draw.ellipse(surf, shade(color, 50), (w//4, h//4, w//2, h//4))
    rotated = pygame.transform.rotate(surf, angle)
    surface.blit(rotated, (int(x - rotated.get_width()//2), int(y - rotated.get_height()//2)))

def draw_sword(surface, x, y, angle, length=35):
    rad = math.radians(angle)
    hx = x + math.cos(rad) * length
    hy = y - math.sin(rad) * length
    pygame.draw.line(surface, (100,50,20), (x, y), (x - math.cos(rad)*10, y + math.sin(rad)*10), 4)
    draw_sphere(surface, (200,180,50), x - math.cos(rad)*10, y + math.sin(rad)*10, 3) 
    gx1, gy1 = x + math.cos(rad+1.57)*8, y - math.sin(rad+1.57)*8
    gx2, gy2 = x + math.cos(rad-1.57)*8, y - math.sin(rad-1.57)*8
    pygame.draw.line(surface, (200,180,50), (gx1, gy1), (gx2, gy2), 4) 
    pygame.draw.polygon(surface, (220,240,255), [(x + math.cos(rad-1.57)*3, y - math.sin(rad-1.57)*3), (x + math.cos(rad+1.57)*3, y - math.sin(rad+1.57)*3), (hx, hy)])
    pygame.draw.polygon(surface, (150,200,250), [(x, y), (x + math.cos(rad+1.57)*3, y - math.sin(rad+1.57)*3), (hx, hy)])

# --- Safe Asset Loading & Fonts ---
def load_image_safe(filename, scale_size):
    try:
        img = pygame.image.load(filename).convert_alpha()
        return pygame.transform.scale(img, scale_size)
    except Exception as e:
        surf = pygame.Surface(scale_size)
        surf.fill((40, 40, 40))
        pygame.draw.rect(surf, (255,50,50), surf.get_rect(), 4)
        font = pygame.font.Font(None, 24)
        txt = font.render("Image Missing", True, (255,255,255))
        surf.blit(txt, (scale_size[0]//2 - txt.get_width()//2, scale_size[1]//2))
        return surf

def get_chinese_font(size):
    # 直接读取打包在游戏文件夹里的相对路径字体
    # 请确保你复制过来的字体文件名和下面这行保持一致
    font_path = "msyhbd.ttc"  # 如果你用的是微软雅黑，这里改成 "chinese.ttc"
    
    try: 
        return pygame.font.Font(font_path, size)
    except Exception as e: 
        print("Font Error:", e)
        return pygame.font.Font(None, size)

# --- Core Gameplay Classes ---
class Projectile:
    def __init__(self, row, x, y, is_ice=False):
        self.row = row
        self.x = x
        self.y = y
        self.is_ice = is_ice
        self.damage = 20
        self.color = (150, 220, 255) if is_ice else (152, 251, 152)
        self.max_range = 9999
        
    def update(self): 
        self.x += 6
        if self.x > self.max_range: self.x = 9999 
        
    def draw(self, surface): 
        draw_sphere(surface, self.color, self.x, self.y, 6, 1.0, 1.0)
        pygame.draw.circle(surface, (255,255,255), (int(self.x-2), int(self.y-2)), 2)

# --- Core Game Engine ---
class GameEngine:
    def __init__(self):
        pygame.mixer.pre_init(44100, -16, 2, 2048)  # 网页版推荐使用 2048 或 4096
        pygame.init()
        pygame.mixer.init()
        
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        self.canvas = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("PvZ: Ultimate Edition")
        self.clock = pygame.time.Clock()
        self.running = True
        
        self.font_title = pygame.font.Font(None, 80)
        self.font_large = pygame.font.Font(None, 60)
        self.font_medium = pygame.font.Font(None, 36)
        self.font_small = pygame.font.Font(None, 22)
        
        # --- File Path Configurations ---
        img_dir = "picture"
        music_dir = "music"
        
        self.img1 = load_image_safe(os.path.join(img_dir, "boss.png"), (300, 380))
        self.img2 = load_image_safe(os.path.join(img_dir, "pig.png"), (300, 380))
        
        # 直接写死带正斜杠的路径
        self.bgm_menu = "music/menu.ogg"
        self.bgm_game = "music/game.ogg"
        self.bgm_final = "music/final_fight.ogg"
        
        self.current_bgm = None  # <--- 请务必把这一行补回来！
        
        try: self.snd_laugh = pygame.mixer.Sound("music/laugh.ogg")
        except: self.snd_laugh = None
            
        self.state = STATE_MENU
        self.level_manager = LevelManager()
        self.shake = 0
        self.has_revived = False 
        
        self.all_plant_types = [
            {"name": "Sun", "cost": 50, "class": Sunflower},
            {"name": "Pea", "cost": 100, "class": Peashooter},
            {"name": "Repeat", "cost": 200, "class": Repeater},
            {"name": "Gatling", "cost": 250, "class": GatlingPea}, 
            {"name": "Snow", "cost": 175, "class": SnowPea},
            {"name": "Wall", "cost": 50, "class": Wallnut},
            {"name": "Tall", "cost": 125, "class": Tallnut}, 
            {"name": "Mine", "cost": 25, "class": PotatoMine},
            {"name": "Cherry", "cost": 150, "class": CherryBomb},
            {"name": "Squash", "cost": 50, "class": Squash},
            {"name": "Chomp", "cost": 150, "class": Chomper},
            {"name": "Jalap", "cost": 125, "class": Jalapeno},
            {"name": "Puff", "cost": 0, "class": Puffshroom}, 
            {"name": "IceShr", "cost": 75, "class": IceShroom}, 
            {"name": "Spike", "cost": 100, "class": Spikeweed},
            {"name": "RiceG", "cost": 150, "class": RiceGuard},
            {"name": "PigPer", "cost": 200, "class": PigHeadPersimmon}
        ]
        
        self.selected_seeds = []
        self.max_seeds = 8
        self.pending_level = 1
        
        self.reset_game()
        self.play_bgm(self.bgm_menu)

    def play_bgm(self, path):
        if self.current_bgm == path: return
        self.current_bgm = path
        if not pygame.mixer.get_init(): return
        try:
            # 网页版直接强行加载，不要用 os.path.exists 判断！
            pygame.mixer.music.load(path)
            pygame.mixer.music.play(-1) 
        except Exception as e: 
            print("Music Error:", e)

    def reset_game(self):
        self.economy = EconomySystem()
        self.plants, self.zombies, self.projectiles, self.suns, self.particles = [], [], [], [], []
        self.mowers = [LawnMower(r) for r in range(GRID_ROWS)]
        self.selected_plant, self.shovel_active = None, False
        
        self.shake = 0
        self.damage_mult = 1.0 
        self.has_revived = False 
        self.shovel_rect = pygame.Rect(SCREEN_WIDTH - 60, 15, 50, 90)

        self.seed_bank = []
        card_w, spacing, start_x, card_h, card_y = 46, 6, 80, 95, 10
        for i, p_data in enumerate(self.selected_seeds):
            self.seed_bank.append({
                "name": p_data["name"], "cost": p_data["cost"],
                "class": p_data["class"], "rect": pygame.Rect(start_x + (card_w+spacing)*i, card_y, card_w, card_h)
            })

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT: self.running = False
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE and self.state in [STATE_PLAYING, STATE_PAUSED]:
                self.state = STATE_PLAYING if self.state == STATE_PAUSED else STATE_PAUSED
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1: self.handle_click(event.pos)
                elif event.button == 3: self.selected_plant, self.shovel_active = None, False

    def draw_button(self, text, x, y, w, h, base_color):
        rect = pygame.Rect(x, y, w, h)
        is_hovered = rect.collidepoint(pygame.mouse.get_pos())
        color = shade(base_color, 30) if is_hovered else base_color
        
        pygame.draw.rect(self.canvas, shade(color, -50), (x+2, y+5, w, h), border_radius=12)
        pygame.draw.rect(self.canvas, color, rect, border_radius=12)
        pygame.draw.rect(self.canvas, shade(color, 40), (x+2, y+2, w-4, h//2), border_radius=10)
        pygame.draw.rect(self.canvas, (255, 255, 255), rect, 2, border_radius=12)
        
        text_surf = self.font_medium.render(text, True, (255, 255, 255))
        self.canvas.blit(text_surf, (rect.centerx - text_surf.get_width()//2, rect.centery - text_surf.get_height()//2))
        return is_hovered

    def draw_wooden_panel(self, x, y, w, h, title=""):
        pygame.draw.rect(self.canvas, (0, 0, 0, 100), (x+5, y+10, w, h), border_radius=15)
        draw_3d_rect(self.canvas, (120, 70, 30), pygame.Rect(x, y, w, h), 15)
        pygame.draw.rect(self.canvas, shade((120, 70, 30), -40), (x+10, y+10, w-20, h-20), 4, border_radius=10)
        for bx in [x+15, x+w-15]:
            for by in [y+15, y+h-15]:
                draw_sphere(self.canvas, (150, 150, 150), bx, by, 5, 1.0, 1.0)
        if title:
            title_w = self.font_large.render(title, True, (0,0,0)).get_width() + 40
            pygame.draw.rect(self.canvas, (200, 180, 100), (x + w//2 - title_w//2, y - 25, title_w, 50), border_radius=8)
            pygame.draw.rect(self.canvas, (100, 80, 20), (x + w//2 - title_w//2, y - 25, title_w, 50), 3, border_radius=8)
            t_surf = self.font_large.render(title, True, (50, 20, 0))
            self.canvas.blit(t_surf, (x + w//2 - t_surf.get_width()//2, y - 18))

    def handle_click(self, pos):
        # --- 加上这两行唤醒音乐的代码 ---
        if not pygame.mixer.music.get_busy() and self.state == STATE_MENU:
            self.current_bgm = None # 重置状态强制播放
            self.play_bgm(self.bgm_menu)
        # -----------------------------

        if self.state == STATE_MENU:
            if pygame.Rect(SCREEN_WIDTH//2 - 120, 250, 240, 60).collidepoint(pos): self.state = STATE_LEVEL_SELECT
            # ... 保持你原来的代码不变 ...
            elif pygame.Rect(SCREEN_WIDTH//2 - 120, 330, 240, 60).collidepoint(pos): self.state = STATE_HELP
            elif pygame.Rect(SCREEN_WIDTH//2 - 120, 410, 240, 60).collidepoint(pos): self.running = False
            return
        elif self.state == STATE_LEVEL_SELECT:
            if pygame.Rect(SCREEN_WIDTH//2 - 250, 140, 240, 60).collidepoint(pos): self.prepare_level(1)
            elif pygame.Rect(SCREEN_WIDTH//2 + 10, 140, 240, 60).collidepoint(pos): self.prepare_level(2)
            elif pygame.Rect(SCREEN_WIDTH//2 - 250, 220, 240, 60).collidepoint(pos): self.prepare_level(3)
            elif pygame.Rect(SCREEN_WIDTH//2 + 10, 220, 240, 60).collidepoint(pos): self.prepare_level(4)
            elif pygame.Rect(SCREEN_WIDTH//2 - 250, 300, 240, 60).collidepoint(pos): self.prepare_level(5)
            elif pygame.Rect(SCREEN_WIDTH//2 + 10, 300, 240, 60).collidepoint(pos): self.prepare_level(6)
            elif pygame.Rect(SCREEN_WIDTH//2 - 120, 380, 240, 60).collidepoint(pos): self.prepare_level(7)
            elif pygame.Rect(SCREEN_WIDTH//2 - 120, 460, 240, 60).collidepoint(pos): self.state = STATE_MENU
            return
        elif self.state == STATE_SEED_SELECTION:
            card_w, spacing, card_h = 46, 6, 95 
            start_x_avail = 130 
            for i, p_data in enumerate(self.all_plant_types):
                row = i // 9
                col = i % 9
                rect = pygame.Rect(start_x_avail + (card_w+spacing)*col, 260 + row*120, card_w, card_h)
                if rect.collidepoint(pos):
                    if p_data not in self.selected_seeds and len(self.selected_seeds) < self.max_seeds:
                        self.selected_seeds.append(p_data)
                    elif p_data in self.selected_seeds:
                        self.selected_seeds.remove(p_data)
                    return
            
            start_x_sel = 155
            for i, p_data in enumerate(self.selected_seeds):
                rect = pygame.Rect(start_x_sel + (card_w+spacing)*i, 80, card_w, card_h)
                if rect.collidepoint(pos):
                    self.selected_seeds.remove(p_data)
                    return
            
            if len(self.selected_seeds) == self.max_seeds and pygame.Rect(SCREEN_WIDTH//2 - 120, 500, 240, 60).collidepoint(pos):
                self.start_level()
            elif pygame.Rect(20, 15, 100, 40).collidepoint(pos):
                self.state = STATE_LEVEL_SELECT
            return
            
        elif self.state == STATE_HELP:
            if pygame.Rect(SCREEN_WIDTH//2 - 120, 480, 240, 60).collidepoint(pos): self.state = STATE_MENU
            return
        elif self.state in [STATE_GAME_OVER, STATE_VICTORY] and pygame.Rect(SCREEN_WIDTH//2 - 125, 350, 250, 60).collidepoint(pos):
            self.state = STATE_MENU
            self.play_bgm(self.bgm_menu)
            return
        elif self.state == STATE_PAUSED:
            if pygame.Rect(SCREEN_WIDTH//2 - 100, 280, 200, 50).collidepoint(pos): 
                self.state = STATE_PLAYING
            elif pygame.Rect(SCREEN_WIDTH//2 - 100, 350, 200, 50).collidepoint(pos): 
                self.state = STATE_MENU
                self.play_bgm(self.bgm_menu)
            return

        for sun in self.suns:
            if math.hypot(pos[0] - sun.x, pos[1] - sun.y) < 35:
                self.economy.bank += 25; self.suns.remove(sun); return 

        if pos[1] < UI_HEIGHT:
            if self.shovel_rect.collidepoint(pos): self.shovel_active, self.selected_plant = True, None; return
            for seed in self.seed_bank:
                if seed["rect"].collidepoint(pos) and self.economy.bank >= seed["cost"]:
                    self.selected_plant, self.shovel_active = seed, False; return
            return

        col, row = pos[0] // CELL_WIDTH, (pos[1] - GRID_START_Y) // CELL_HEIGHT
        if 0 <= col < GRID_COLS and 0 <= row < GRID_ROWS and pos[1] >= GRID_START_Y:
            existing = next((p for p in self.plants if p.row == row and p.col == col), None)
            if self.shovel_active:
                if existing:
                    self.plants.remove(existing)
                    self.particles.append({"x": pos[0], "y": pos[1], "radius": 25, "color": (139, 69, 19), "life": 15, "max_life": 15})
                self.shovel_active = False 
            elif self.selected_plant and not existing:
                self.economy.bank -= self.selected_plant["cost"]
                
                new_plant = self.selected_plant["class"](row, col)
                self.plants.append(new_plant)
                
                if isinstance(new_plant, PigHeadPersimmon):
                    if self.snd_laugh: self.snd_laugh.play(maxtime=4000)
                        
                self.selected_plant = None

    def prepare_level(self, level):
        self.pending_level = level
        self.selected_seeds = []
        self.state = STATE_SEED_SELECTION

    def start_level(self):
        self.reset_game()
        self.level_manager.reset()
        self.level_manager.start_level(self.pending_level)
        self.state = STATE_PLAYING
        self.play_bgm(self.bgm_game)

    def update(self):
        if self.state == STATE_REVIVAL_SEQUENCE:
            elapsed = time.time() - self.revival_start_time
            if elapsed >= 11.0:
                self.zombies.clear()
                self.economy.bank += 1500
                self.damage_mult = 2.0
                self.state = STATE_PLAYING
                self.play_bgm(self.bgm_final) 
                self.shake = 40
                for _ in range(150):
                    self.particles.append({"x": random.randint(0, SCREEN_WIDTH), "y": random.randint(0, SCREEN_HEIGHT), "radius": random.randint(5, 20), "color": (255, 255, 100), "life": 60, "max_life": 60, "vx": random.uniform(-4, 4), "vy": random.uniform(-10, -2)})
            return

        if self.state != STATE_PLAYING: return
        self.economy.update(self.suns)
        
        if self.level_manager.update(self.zombies, self.has_revived) == "VICTORY": 
            self.state = STATE_VICTORY
            pygame.mixer.music.stop()
        
        self.plants = [p for p in self.plants if p.health > 0]
        self.zombies = [z for z in self.zombies if z.health > 0]
        self.projectiles = [p for p in self.projectiles if p.x <= SCREEN_WIDTH]
        
        for p in self.particles[:]:
            if p.get("type") == "shake":
                self.shake = max(self.shake, p["amount"])
                self.particles.remove(p)
                continue
            p["life"] -= 1
            if p["life"] <= 0: self.particles.remove(p); continue
            
            p["x"] += p.get("vx", 0); p["y"] += p.get("vy", 0)
            if p.get("type") == "ring": p["radius"] += 2.5
            elif p.get("type") == "text": pass 
            else: p["radius"] += 0.5

        for plant in self.plants: plant.update(self.zombies, self.projectiles, self.suns, self.particles, self.damage_mult)
        
        for zombie in self.zombies:
            zombie.update(self.plants, self.particles)
            if zombie.x < 40:
                mower = next((m for m in self.mowers if m.row == zombie.row and not m.active), None)
                if mower: mower.active = True
                elif zombie.x < -20: 
                    if self.level_manager.current_level in [4, 5, 6, 7] and not self.has_revived:
                        self.state = STATE_REVIVAL_SEQUENCE
                        self.revival_start_time = time.time()
                        self.has_revived = True
                        pygame.mixer.music.stop()
                        break 
                    else:
                        self.state = STATE_GAME_OVER
                        pygame.mixer.music.stop()

        for mower in self.mowers[:]:
            if mower.active:
                mower.x += mower.speed
                for z in self.zombies:
                    if z.row == mower.row and abs(z.x - mower.x) < 40 and not getattr(z, 'untargetable', False):
                        z.health = 0
                        self.particles.append({"x": z.x, "y": z.y, "radius": 15, "color": (150, 50, 50), "life": 15, "max_life": 15})
                if mower.x > SCREEN_WIDTH: self.mowers.remove(mower)

        for proj in self.projectiles[:]:
            proj.update()
            for zombie in self.zombies:
                if proj.row == zombie.row and not getattr(zombie, 'untargetable', False) and pygame.Rect(zombie.x - 25, zombie.y - 35, 50, 70).collidepoint(proj.x, proj.y):
                    zombie.take_damage(proj.damage * self.damage_mult, proj.is_ice)
                    for _ in range(5):
                        self.particles.append({"x": proj.x, "y": proj.y, "radius": random.randint(3, 6), "color": proj.color, 
                                               "life": 12, "max_life": 12, "vx": random.uniform(-3, 1), "vy": random.uniform(-3, 3)})
                    if proj in self.projectiles: self.projectiles.remove(proj)
                    break 

    def draw(self):
        self.canvas.fill(C_BG)
        if self.state in [STATE_MENU, STATE_LEVEL_SELECT, STATE_HELP, STATE_SEED_SELECTION]: 
            self.draw_bg_pattern()
            if self.state == STATE_MENU: self.draw_main_menu()
            elif self.state == STATE_LEVEL_SELECT: self.draw_level_select()
            elif self.state == STATE_HELP: self.draw_help_menu()
            elif self.state == STATE_SEED_SELECTION: self.draw_seed_selection()
        elif self.state == STATE_GAME_OVER: self.draw_overlay_menu("ZOMBIES ATE YOUR BRAINS!", (255, 50, 50), "Main Menu")
        elif self.state == STATE_VICTORY: self.draw_overlay_menu("LEVEL CLEARED!", (50, 255, 50), "Continue")
        elif self.state == STATE_REVIVAL_SEQUENCE: self.draw_revival_sequence()
        elif self.state in [STATE_PLAYING, STATE_PAUSED]:
            self.draw_gameplay()
            if self.state == STATE_PAUSED: self.draw_pause_menu()
            
        dx = random.randint(-self.shake, self.shake) if self.shake > 0 else 0
        dy = random.randint(-self.shake, self.shake) if self.shake > 0 else 0
        self.screen.fill((0,0,0))
        self.screen.blit(self.canvas, (dx, dy))
        pygame.display.flip()
        
        if self.shake > 0: self.shake -= 1

    def draw_bg_pattern(self):
        for r in range(GRID_ROWS + 3):
            for c in range(GRID_COLS):
                pygame.draw.rect(self.canvas, (30, 150, 40) if (r + c) % 2 == 0 else (25, 140, 35), (c * CELL_WIDTH, r * CELL_HEIGHT, CELL_WIDTH, CELL_HEIGHT))
        surf = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        surf.fill((0, 0, 0, 100)); self.canvas.blit(surf, (0,0))

    def draw_main_menu(self):
        title = self.font_title.render("Plants vs. Python", True, (255, 255, 255))
        self.canvas.blit(self.font_title.render("Plants vs. Python", True, (0, 0, 0)), (SCREEN_WIDTH//2 - title.get_width()//2 + 3, 103))
        self.canvas.blit(title, (SCREEN_WIDTH//2 - title.get_width()//2, 100))
        self.draw_wooden_panel(SCREEN_WIDTH//2 - 160, 220, 320, 280)
        self.draw_button("Play Game", SCREEN_WIDTH//2 - 120, 250, 240, 60, (50, 150, 50))
        self.draw_button("How to Play", SCREEN_WIDTH//2 - 120, 330, 240, 60, (50, 100, 200))
        self.draw_button("Quit", SCREEN_WIDTH//2 - 120, 410, 240, 60, (200, 50, 50))

    def draw_level_select(self):
        self.draw_wooden_panel(SCREEN_WIDTH//2 - 280, 100, 560, 540, "Select Level")
        self.draw_button("Level 1 (Easy)", SCREEN_WIDTH//2 - 250, 140, 240, 60, (100, 200, 100))
        self.draw_button("Level 2 (Med)", SCREEN_WIDTH//2 + 10, 140, 240, 60, (150, 200, 50))
        self.draw_button("Level 3 (Hard)", SCREEN_WIDTH//2 - 250, 220, 240, 60, (200, 150, 50))
        self.draw_button("Level 4 (Rat Boss)", SCREEN_WIDTH//2 + 10, 220, 240, 60, (180, 50, 200))
        self.draw_button("Level 5 (Fire Bull)", SCREEN_WIDTH//2 - 250, 300, 240, 60, (255, 100, 50))
        self.draw_button("Level 6 (Ultimate)", SCREEN_WIDTH//2 + 10, 300, 240, 60, (255, 50, 50))
        self.draw_button("Level 7 (Dragon)", SCREEN_WIDTH//2 - 120, 380, 240, 60, (100, 50, 150)) 
        self.draw_button("Back to Menu", SCREEN_WIDTH//2 - 120, 460, 240, 60, (100, 100, 100))

    def draw_seed_selection(self):
        self.draw_wooden_panel(SCREEN_WIDTH//2 - 320, 40, 640, 160, "Choose Your Seeds")
        self.draw_wooden_panel(SCREEN_WIDTH//2 - 320, 230, 640, 260, "Available Plants")
        
        card_w, spacing, card_h = 46, 6, 95
        start_x_sel = 155 
        for i in range(self.max_seeds):
            rect = pygame.Rect(start_x_sel + (card_w+spacing)*i, 80, card_w, card_h)
            pygame.draw.rect(self.canvas, (40, 40, 40), rect, border_radius=5)
            pygame.draw.rect(self.canvas, (0, 0, 0), rect, 2, border_radius=5)
            
        for i, p_data in enumerate(self.selected_seeds):
            rect = pygame.Rect(start_x_sel + (card_w+spacing)*i, 80, card_w, card_h)
            draw_3d_rect(self.canvas, (200, 200, 200), rect, 5)
            p_data["class"].draw_model(self.canvas, rect.centerx, rect.centery - 5)
            cost_txt = self.font_small.render(str(p_data["cost"]), True, (0, 0, 0))
            self.canvas.blit(cost_txt, (rect.centerx - cost_txt.get_width()//2, rect.bottom - 20))
            
        start_x_avail = 130 
        for i, p_data in enumerate(self.all_plant_types):
            row = i // 9
            col = i % 9
            rect = pygame.Rect(start_x_avail + (card_w+spacing)*col, 260 + row*120, card_w, card_h)
            
            is_selected = p_data in self.selected_seeds
            color = (100, 100, 100) if is_selected else (200, 200, 200)
            
            draw_3d_rect(self.canvas, color, rect, 5)
            p_data["class"].draw_model(self.canvas, rect.centerx, rect.centery - 5)
            cost_txt = self.font_small.render(str(p_data["cost"]), True, (0, 0, 0))
            self.canvas.blit(cost_txt, (rect.centerx - cost_txt.get_width()//2, rect.bottom - 20))
            
            if is_selected: 
                s = pygame.Surface((card_w, card_h), pygame.SRCALPHA)
                s.fill((0, 0, 0, 150))
                self.canvas.blit(s, rect.topleft)

        if len(self.selected_seeds) == self.max_seeds:
            self.draw_button("Let's Rock!", SCREEN_WIDTH//2 - 120, 500, 240, 60, (50, 200, 50))
        else:
            pygame.draw.rect(self.canvas, (100, 100, 100), (SCREEN_WIDTH//2 - 120, 500, 240, 60), border_radius=12)
            txt = self.font_medium.render(f"Pick {self.max_seeds - len(self.selected_seeds)} More", True, (150, 150, 150))
            self.canvas.blit(txt, (SCREEN_WIDTH//2 - txt.get_width()//2, 515))
            
        self.draw_button("Back", 20, 15, 100, 40, (150, 50, 50))

    def draw_help_menu(self):
        self.draw_wooden_panel(SCREEN_WIDTH//2 - 300, 140, 600, 420, "How to Play")
        lines = [
            "1. Collect falling Sun and Sun from Sunflowers.",
            "2. Click seed cards at the top to plant defenses.",
            "3. Prevent zombies from crossing the left side.",
            "4. Use the Shovel to remove unwanted plants.",
            "5. Red Lawn Mowers offer a one-time save per row.",
            "Press ESC during gameplay to pause."
        ]
        for i, line in enumerate(lines):
            self.canvas.blit(self.font_medium.render(line, True, (255, 255, 255)), (SCREEN_WIDTH//2 - 260, 200 + i * 40))
        self.draw_button("Back to Menu", SCREEN_WIDTH//2 - 120, 480, 240, 60, (100, 100, 100))

    def draw_overlay_menu(self, text, color, btn_text):
        self.draw_gameplay()
        surf = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        surf.fill((0, 0, 0, 180)); self.canvas.blit(surf, (0, 0))
        self.draw_wooden_panel(SCREEN_WIDTH//2 - 250, 250, 500, 200)
        title = self.font_large.render(text, True, color)
        self.canvas.blit(title, (SCREEN_WIDTH//2 - title.get_width()//2, 280))
        self.draw_button(btn_text, SCREEN_WIDTH//2 - 125, 360, 250, 60, (100, 100, 100))

    def draw_pause_menu(self):
        surf = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        surf.fill((0, 0, 0, 150)); self.canvas.blit(surf, (0, 0))
        self.draw_wooden_panel(SCREEN_WIDTH//2 - 150, 220, 300, 220, "PAUSED")
        self.draw_button("Resume", SCREEN_WIDTH//2 - 100, 280, 200, 50, (50, 150, 50))
        self.draw_button("Quit to Menu", SCREEN_WIDTH//2 - 100, 350, 200, 50, (200, 50, 50))

    def draw_revival_sequence(self):
        self.canvas.fill((10, 10, 15)) 
        elapsed = time.time() - self.revival_start_time
        
        if elapsed < 3.0:
            self.canvas.blit(self.img1, (SCREEN_WIDTH//2 - 340, SCREEN_HEIGHT//2 - 190))
            self.canvas.blit(self.img2, (SCREEN_WIDTH//2 + 40, SCREEN_HEIGHT//2 - 190))
        else:
            font = get_chinese_font(26)
            lines = [
                "叮！系统提示：【永暗的魔王】已经觉醒，接下来登场的是",
                "【原初的勇者】【众神加护者】【曾经的救世主】【终焉之人】",
                "【诸神黄昏】【世界之子】【气运眷顾之人】【传说的开始】",
                "【故事的起点】【童谣的原本】【史诗传唱之人】【屠龙者】",
                "【世界毁灭者】【背誓者】【最强的人类】【圣剑之主】。",
                "",
                "叮！系统提示：滋滋…滋…系统…错…误……滋…正在…检…测。",
                "",
                "叮！系统提示：最终资料片——【原初的神话】开启",
                "",
                '"踏上前来，杀死我，向我证明你们才是对的。"'
            ]
            for i, line in enumerate(lines):
                color = (200, 200, 200)
                if "滋滋" in line: color = (255, 100, 100)
                elif "杀死我" in line: color = (255, 50, 50)
                elif "叮" in line: color = (100, 200, 255)
                
                text_surf = font.render(line, True, color)
                self.canvas.blit(text_surf, (SCREEN_WIDTH//2 - text_surf.get_width()//2, 80 + i * 35))

    def draw_gameplay(self):
        for r in range(GRID_ROWS):
            for c in range(GRID_COLS):
                pygame.draw.rect(self.canvas, C_BG if (r+c)%2==0 else C_GRID_ALT, (c*CELL_WIDTH, r*CELL_HEIGHT+GRID_START_Y, CELL_WIDTH, CELL_HEIGHT))

        shadow_surf = pygame.Surface((60, 30), pygame.SRCALPHA)
        pygame.draw.ellipse(shadow_surf, (0, 0, 0, 70), (0, 0, 60, 20))
        for entity in self.plants + self.zombies + self.mowers:
            ex, ey = getattr(entity, 'cx', getattr(entity, 'x', 0)), getattr(entity, 'cy', getattr(entity, 'y', 0))
            if isinstance(entity, Zombie) and getattr(entity, 'untargetable', False):
                continue 
            if isinstance(entity, Zombie): ey += 30
            self.canvas.blit(shadow_surf, (ex - 30, ey + 15))

        for mower in self.mowers: mower.draw(self.canvas)
        for plant in self.plants: plant.draw(self.canvas)
        
        for zombie in sorted(self.zombies, key=lambda z: getattr(z, 'flight_y', 0)): 
            zombie.draw(self.canvas)
            
        for proj in self.projectiles: proj.draw(self.canvas)
        for sun in self.suns: sun.draw(self.canvas)
        
        for p in self.particles:
            if p.get("type") == "shake": continue 
            
            if p.get("type") == "text":
                txt_surf = self.font_small.render(p["text"], True, p["color"])
                self.canvas.blit(txt_surf, (int(p["x"]), int(p["y"])))
                continue
                
            alpha = max(0, min(255, int((p.get("life", 15) / p.get("max_life", 15)) * 255)))
            if p.get("type") == "ring":
                pygame.draw.circle(self.canvas, (*p["color"], alpha), (int(p["x"]), int(p["y"])), int(p["radius"]), 4)
            else:
                surf = pygame.Surface((int(p["radius"]*2), int(p["radius"]*2)), pygame.SRCALPHA)
                pygame.draw.circle(surf, (*p["color"], alpha), (int(p["radius"]), int(p["radius"])), int(p["radius"]))
                self.canvas.blit(surf, (p["x"] - p["radius"], p["y"] - p["radius"]))

        # --- TOP UI PANEL ---
        pygame.draw.rect(self.canvas, C_UI_PANEL, (0, 0, SCREEN_WIDTH, UI_HEIGHT))
        pygame.draw.rect(self.canvas, shade(C_UI_PANEL, -30), (0, UI_HEIGHT-5, SCREEN_WIDTH, 5))
        draw_3d_rect(self.canvas, (200, 180, 150), pygame.Rect(5, 10, 70, 95), 10)
        
        mx, my = 40, 35
        for i in range(8): 
            a = time.time()*2 + i*(math.pi/4)
            pygame.draw.polygon(self.canvas, (255, 180, 0), [(mx+math.cos(a-0.2)*10, my+math.sin(a-0.2)*10), (mx+math.cos(a+0.2)*10, my+math.sin(a+0.2)*10), (mx+math.cos(a)*16, my+math.sin(a)*16)])
        draw_sphere(self.canvas, (255, 240, 50), mx, my, 10, 1.0, 1.0)
        
        sun_txt = self.font_medium.render(str(self.economy.bank), True, (0, 0, 0))
        self.canvas.blit(sun_txt, (40 - sun_txt.get_width()//2, 70))

        for seed in self.seed_bank:
            color = (130, 130, 130) if self.economy.bank < seed["cost"] else (200, 200, 200)
            if self.selected_plant == seed: color = (255, 255, 150)
            draw_3d_rect(self.canvas, color, seed["rect"], 5)
            seed["class"].draw_model(self.canvas, seed["rect"].centerx, seed["rect"].centery - 5)
            cost_txt = self.font_small.render(str(seed["cost"]), True, (0, 0, 0))
            self.canvas.blit(cost_txt, (seed["rect"].centerx - cost_txt.get_width()//2, seed["rect"].bottom - 20))

        sh_color = (255, 100, 100) if self.shovel_active else (150, 150, 150)
        draw_3d_rect(self.canvas, sh_color, self.shovel_rect, 10)
        pygame.draw.rect(self.canvas, (100, 50, 10), (self.shovel_rect.centerx-4, self.shovel_rect.centery-20, 8, 40))
        pygame.draw.polygon(self.canvas, (200, 200, 200), [(self.shovel_rect.centerx-15, self.shovel_rect.centery+10), (self.shovel_rect.centerx+15, self.shovel_rect.centery+10), (self.shovel_rect.centerx, self.shovel_rect.centery+25)])

        # --- BOTTOM UI PANEL ---
        pygame.draw.rect(self.canvas, shade(C_UI_PANEL, -20), (0, SCREEN_HEIGHT - BOTTOM_UI_HEIGHT, SCREEN_WIDTH, BOTTOM_UI_HEIGHT))
        pygame.draw.rect(self.canvas, shade(C_UI_PANEL, 20), (0, SCREEN_HEIGHT - BOTTOM_UI_HEIGHT, SCREEN_WIDTH, 4))
        lvl_lbl = self.font_medium.render(f"Level {self.level_manager.current_level} - Wave {self.level_manager.wave_count}/{self.level_manager.max_waves}", True, (255, 255, 255))
        self.canvas.blit(lvl_lbl, (20, SCREEN_HEIGHT - BOTTOM_UI_HEIGHT + 15))

        bar_w, bar_h, bar_x, bar_y = 240, 20, SCREEN_WIDTH - 270, SCREEN_HEIGHT - BOTTOM_UI_HEIGHT + 20
        pygame.draw.rect(self.canvas, (40, 40, 40), (bar_x, bar_y, bar_w, bar_h), border_radius=10)
        progress = 1.0 if self.level_manager.max_waves == 0 else min(1.0, self.level_manager.wave_count / self.level_manager.max_waves)
        if progress > 0:
            pygame.draw.rect(self.canvas, (50, 200, 50), pygame.Rect(bar_x, bar_y, int(bar_w * progress), bar_h), border_radius=10)
            pygame.draw.rect(self.canvas, (100, 255, 100), (bar_x+2, bar_y+2, int(bar_w * progress)-4, bar_h//2), border_radius=8)
        pygame.draw.rect(self.canvas, (0, 0, 0), (bar_x, bar_y, bar_w, bar_h), 2, border_radius=10)
        
        head_x = bar_x + bar_w - int(bar_w * progress)
        draw_sphere(self.canvas, (100, 200, 100), head_x, bar_y + bar_h//2, 14, 1.0, 1.0)
        draw_eye(self.canvas, head_x-4, bar_y + bar_h//2 - 2, 3, angry=True)

        mouse_pos = pygame.mouse.get_pos()
        if mouse_pos[1] > GRID_START_Y and mouse_pos[1] < SCREEN_HEIGHT - BOTTOM_UI_HEIGHT:
            c, r = mouse_pos[0] // CELL_WIDTH, (mouse_pos[1] - GRID_START_Y) // CELL_HEIGHT
            if self.selected_plant and 0 <= c < GRID_COLS and 0 <= r < GRID_ROWS:
                self.selected_plant["class"].draw_model(self.canvas, c*CELL_WIDTH + CELL_WIDTH//2, r*CELL_HEIGHT + GRID_START_Y + CELL_HEIGHT//2)
            elif self.shovel_active: pygame.draw.rect(self.canvas, (255, 0, 0), (c*CELL_WIDTH, r*CELL_HEIGHT+GRID_START_Y, CELL_WIDTH, CELL_HEIGHT), 3)

    async def run(self):
        while self.running:
            self.handle_events()
            self.update()
            self.draw()
            self.clock.tick(FPS)
            await asyncio.sleep(0)  # <--- 网页版不卡死、能发声全靠这句！
        pygame.quit()

# --- Level & Economy ---
class LevelManager:
    def __init__(self): self.reset()
    def reset(self):
        self.current_level = 1
        self.levels = {
            1: {"waves": 10, "types": ["Normal"], "spawn_rate": 6.5},
            2: {"waves": 20, "types": ["Normal", "Conehead", "Newspaper"], "spawn_rate": 5.0},
            3: {"waves": 30, "types": ["Normal", "Conehead", "Buckethead", "Newspaper", "Flag"], "spawn_rate": 3.5},
            4: {"waves": 40, "types": ["Normal", "Conehead", "RatKing"], "spawn_rate": 4.0}, 
            5: {"waves": 50, "types": ["Normal", "Conehead", "Buckethead", "Newspaper", "RatKing", "FireBull"], "spawn_rate": 3.0},
            6: {"waves": 60, "types": ["Normal", "Conehead", "Buckethead", "Newspaper", "PoleVault", "Football", "RatKing", "FireBull"], "spawn_rate": 2.5},
            7: {"waves": 60, "types": ["Normal", "Conehead", "Buckethead", "Dragon", "Dragon", "FireBull", "RatKing", "Football"], "spawn_rate": 3.0} 
        }
    def start_level(self, level_num=None):
        if level_num is not None: self.current_level = level_num
        if self.current_level not in self.levels: return "VICTORY"
        d = self.levels[self.current_level]
        self.max_waves, self.wave_count, self.spawn_interval, self.last_spawn, self.types = d["waves"], 0, d["spawn_rate"], time.time(), d["types"]
    
    def update(self, zombies_list, has_revived=False):
        if self.current_level > 7: return "VICTORY"
        
        effective_interval = self.spawn_interval * 2.0 if not has_revived else self.spawn_interval / 1.5
        
        if self.wave_count < self.max_waves and time.time() - self.last_spawn > effective_interval:
            self.last_spawn = time.time() 
            self.wave_count += 1
            row, z_type = random.randint(0, GRID_ROWS - 1), random.choice(self.types)
            if self.wave_count > 0 and self.wave_count % 10 == 0: z_type = "Flag"
            if z_type == "Buckethead": zombies_list.append(BucketheadZombie(row))
            elif z_type == "Conehead": zombies_list.append(ConeheadZombie(row))
            elif z_type == "Flag": zombies_list.append(FlagZombie(row))
            elif z_type == "Newspaper": zombies_list.append(NewspaperZombie(row))
            elif z_type == "RatKing": zombies_list.append(RatKingZombie(row)) 
            elif z_type == "FireBull": zombies_list.append(FireBullZombie(row)) 
            elif z_type == "PoleVault": zombies_list.append(PoleVaultingZombie(row)) 
            elif z_type == "Football": zombies_list.append(FootballZombie(row)) 
            elif z_type == "Dragon": zombies_list.append(DragonZombie(row)) 
            else: zombies_list.append(Zombie(row))
        if self.wave_count == self.max_waves and len(zombies_list) == 0: return "VICTORY"
        return "PLAYING"

class EconomySystem:
    def __init__(self): self.bank, self.last_sun = 150, time.time()
    def update(self, suns):
        if time.time() - self.last_sun > 9.0: self.last_sun = time.time(); suns.append(Sun())

class Sun:
    def __init__(self, x=None, y=None, is_drop=False):
        self.x, self.y = x or random.randint(50, SCREEN_WIDTH-50), y or -20
        self.target_y = random.randint(GRID_START_Y + 50, SCREEN_HEIGHT - BOTTOM_UI_HEIGHT - 30) if not is_drop else y + 40
        self.is_drop, self.vy, self.vx, self.birth = is_drop, (-5 if is_drop else 2), (random.uniform(-1.5, 1.5) if is_drop else 0), time.time()
    def update(self):
        if self.y < self.target_y or self.is_drop:
            self.y += self.vy; self.x += self.vx
            if self.is_drop:
                self.vy += 0.3
                if self.y >= self.target_y: self.is_drop, self.y = False, self.target_y
    def draw(self, surface):
        self.update()
        t = time.time()
        pygame.draw.circle(surface, (255, 200, 0, 100), (int(self.x), int(self.y)), int(22 + abs(math.sin((t - self.birth) * 4)) * 3))
        for i in range(8):
            a = (t * 1.5) + i * (math.pi / 4)
            pygame.draw.polygon(surface, (255, 180, 0), [(self.x + math.cos(a - 0.25)*14, self.y + math.sin(a - 0.25)*14), (self.x + math.cos(a + 0.25)*14, self.y + math.sin(a + 0.25)*14), (self.x + math.cos(a)*26, self.y + math.sin(a)*26)])
        draw_sphere(surface, (255, 240, 50), self.x, self.y, 16, 1.0, 1.0)
        pygame.draw.circle(surface, (0, 0, 0), (int(self.x - 4), int(self.y - 3)), 2)
        pygame.draw.circle(surface, (0, 0, 0), (int(self.x + 4), int(self.y - 3)), 2)
        pygame.draw.arc(surface, (0, 0, 0), (int(self.x - 5), int(self.y - 1), 10, 8), math.pi, 2*math.pi, 2)

class LawnMower:
    def __init__(self, row):
        self.row, self.x, self.y, self.active, self.speed = row, 20, row * CELL_HEIGHT + GRID_START_Y + CELL_HEIGHT // 2, False, 12
    def draw(self, surface):
        cx, cy = int(self.x), int(self.y)
        pygame.draw.line(surface, (150, 150, 150), (cx-15, cy), (cx-30, cy-25), 4)
        draw_3d_rect(surface, (220, 30, 30), pygame.Rect(cx-20, cy-10, 40, 20), 5)
        draw_sphere(surface, (50, 50, 50), cx-10, cy+10, 8, 1.0, 1.0); draw_sphere(surface, (50, 50, 50), cx+10, cy+10, 8, 1.0, 1.0)

# --- High-Fidelity Plants ---
class Plant:
    def __init__(self, row, col, health, cost):
        self.row, self.col, self.health, self.max_health, self.cost = row, col, health, health, cost
        self.cx, self.cy, self.recoil, self.birth = col * CELL_WIDTH + CELL_WIDTH // 2, row * CELL_HEIGHT + GRID_START_Y + CELL_HEIGHT // 2, 0, time.time()
    def update(self, zombies, projectiles, suns, particles, damage_mult=1.0):
        if self.recoil > 0: self.recoil -= 1.5
    def draw(self, surface):
        breathe = math.sin((time.time() - self.birth) * 2.5) * 2
        type(self).draw_model(surface, self.cx - self.recoil, self.cy - int(breathe), self)
    @staticmethod
    def draw_model(surface, cx, cy, instance=None): pass

class Sunflower(Plant):
    def __init__(self, row, col): super().__init__(row, col, health=300, cost=50); self.last_sun = time.time()
    def update(self, zombies, projectiles, suns, particles, damage_mult=1.0):
        super().update(zombies, projectiles, suns, particles, damage_mult)
        if time.time() - self.last_sun > 10.0:
            self.last_sun, self.recoil = time.time(), 10; suns.append(Sun(self.cx, self.cy - 20, is_drop=True))
    @staticmethod
    def draw_model(surface, cx, cy, instance=None):
        draw_leaf(surface, (34, 139, 34), cx, cy+10, 20, 10, 20)
        draw_leaf(surface, (34, 139, 34), cx, cy+10, 20, 10, -20)
        draw_3d_rect(surface, (50, 205, 50), pygame.Rect(cx-3, cy-10, 6, 25), 3)
        
        offset = (time.time() - instance.birth) if instance else 0
        for i in range(12): 
            a = i * (math.pi / 6) + offset * 0.5
            px, py = cx + math.cos(a)*14, cy - 15 + math.sin(a)*14
            draw_leaf(surface, (255, 215, 0), px, py, 16, 8, -math.degrees(a))
            
        draw_sphere(surface, (139, 69, 19), cx, cy-15, 14, 1.0, 1.0)
        draw_eye(surface, cx-5, cy-18, 3); draw_eye(surface, cx+5, cy-18, 3) 
        pygame.draw.arc(surface, (0, 0, 0), (cx-6, cy-14, 12, 8), math.pi, 2*math.pi, 2) 

class Peashooter(Plant):
    def __init__(self, row, col): super().__init__(row, col, health=300, cost=100); self.last_shot = time.time()
    def update(self, zombies, projectiles, suns, particles, damage_mult=1.0):
        super().update(zombies, projectiles, suns, particles, damage_mult)
        if any(z.row == self.row and not getattr(z, 'untargetable', False) for z in zombies) and time.time() - self.last_shot > 1.5:
            self.last_shot, self.recoil = time.time(), 15
            particles.append({"x": self.cx + 25, "y": self.cy - 15, "radius": 7, "color": (150, 255, 150), "life": 10, "max_life": 10}) 
            projectiles.append(Projectile(self.row, self.cx + 10, self.cy - 15, False))
    @staticmethod
    def draw_model(surface, cx, cy, instance=None):
        recoil_scale = instance.recoil/3 if instance else 0
        draw_leaf(surface, (34, 139, 34), cx-10, cy+15, 24, 12, 30)
        draw_leaf(surface, (34, 139, 34), cx+10, cy+15, 24, 12, -30)
        draw_3d_rect(surface, (50, 205, 50), pygame.Rect(cx-4, cy-5, 8, 25), 4)
        
        draw_leaf(surface, (50, 205, 50), cx-18, cy-5, 20, 10, -45) 
        draw_sphere(surface, (50, 205, 50), cx, cy-10, 16 + recoil_scale, 1.0, 1.0) 
        draw_3d_rect(surface, (50, 205, 50), pygame.Rect(cx+10, cy-18 - recoil_scale/2, 16 + recoil_scale*2, 14 + recoil_scale), 4) 
        pygame.draw.ellipse(surface, (0, 80, 0), (cx+22 + recoil_scale*2, cy-16 - recoil_scale/2, 6, 10 + recoil_scale)) 
        draw_eye(surface, cx+4, cy-15 - recoil_scale/2, 3.5 + recoil_scale/3) 

class Repeater(Peashooter):
    def __init__(self, row, col): super().__init__(row, col); self.cost, self.shots_queued = 200, 0
    def update(self, zombies, projectiles, suns, particles, damage_mult=1.0):
        super(Peashooter, self).update(zombies, projectiles, suns, particles, damage_mult)
        if any(z.row == self.row and not getattr(z, 'untargetable', False) for z in zombies):
            if time.time() - self.last_shot > 1.5: self.shots_queued, self.last_shot = 2, time.time()
            if self.shots_queued > 0 and time.time() - self.last_shot > (2 - self.shots_queued) * 0.15:
                self.recoil = 15
                particles.append({"x": self.cx + 25, "y": self.cy - 15, "radius": 7, "color": (150, 255, 150), "life": 10, "max_life": 10})
                projectiles.append(Projectile(self.row, self.cx + 10, self.cy - 15, False))
                self.shots_queued -= 1
    @staticmethod
    def draw_model(surface, cx, cy, instance=None):
        Peashooter.draw_model(surface, cx, cy, instance)
        draw_leaf(surface, (34, 139, 34), cx-15, cy-15, 15, 8, -60)
        draw_leaf(surface, (34, 139, 34), cx-12, cy-22, 12, 6, -30)
        pygame.draw.line(surface, (0, 60, 0), (cx-2, cy-20), (cx+8, cy-17), 3)

class GatlingPea(Repeater):
    def __init__(self, row, col): super().__init__(row, col); self.cost = 250
    def update(self, zombies, projectiles, suns, particles, damage_mult=1.0):
        super(Peashooter, self).update(zombies, projectiles, suns, particles, damage_mult)
        if any(z.row == self.row and not getattr(z, 'untargetable', False) for z in zombies):
            if time.time() - self.last_shot > 1.5: self.shots_queued, self.last_shot = 4, time.time()
            if self.shots_queued > 0 and time.time() - self.last_shot > (4 - self.shots_queued) * 0.1:
                self.recoil = 18
                particles.append({"x": self.cx + 25, "y": self.cy - 15, "radius": 7, "color": (150, 255, 150), "life": 10, "max_life": 10})
                projectiles.append(Projectile(self.row, self.cx + 10, self.cy - 15 + random.randint(-4,4), False))
                self.shots_queued -= 1
    @staticmethod
    def draw_model(surface, cx, cy, instance=None):
        recoil_scale = instance.recoil/3 if instance else 0
        draw_leaf(surface, (34, 139, 34), cx-10, cy+15, 24, 12, 30)
        draw_leaf(surface, (34, 139, 34), cx+10, cy+15, 24, 12, -30)
        draw_3d_rect(surface, (50, 205, 50), pygame.Rect(cx-4, cy-5, 8, 25), 4)
        draw_sphere(surface, (50, 205, 50), cx, cy-10, 16 + recoil_scale, 1.0, 1.0) 
        draw_3d_rect(surface, (50, 80, 50), pygame.Rect(cx-18, cy-28, 36, 15), 6)
        for i in range(4):
            by = cy - 22 + i*6 - recoil_scale/2
            draw_3d_rect(surface, (30, 40, 30), pygame.Rect(cx+10, by, 20 + recoil_scale*2, 4), 2)
        draw_eye(surface, cx+4, cy-12 - recoil_scale/2, 3.5 + recoil_scale/3, angry=True) 

class SnowPea(Peashooter):
    def __init__(self, row, col): super().__init__(row, col); self.cost = 175
    def update(self, zombies, projectiles, suns, particles, damage_mult=1.0):
        super(Peashooter, self).update(zombies, projectiles, suns, particles, damage_mult)
        if any(z.row == self.row and not getattr(z, 'untargetable', False) for z in zombies) and time.time() - self.last_shot > 1.5:
            self.last_shot, self.recoil = time.time(), 15
            particles.append({"x": self.cx + 25, "y": self.cy - 15, "radius": 7, "color": (200, 230, 255), "life": 10, "max_life": 10})
            projectiles.append(Projectile(self.row, self.cx + 10, self.cy - 15, True))
    @staticmethod
    def draw_model(surface, cx, cy, instance=None):
        c = (100, 200, 255)
        recoil_scale = instance.recoil/3 if instance else 0
        draw_leaf(surface, (34, 139, 34), cx-10, cy+15, 24, 12, 30)
        draw_leaf(surface, (34, 139, 34), cx+10, cy+15, 24, 12, -30)
        draw_3d_rect(surface, (50, 205, 50), pygame.Rect(cx-4, cy-5, 8, 25), 4)
        
        pygame.draw.polygon(surface, shade(c, 40), [(cx-10, cy-22), (cx-22, cy-12), (cx-5, cy-2)])
        pygame.draw.polygon(surface, c, [(cx-10, cy-22), (cx-22, cy-12), (cx-10, cy-10)])
        
        draw_sphere(surface, c, cx, cy-10, 16 + recoil_scale, 1.0, 1.0)
        draw_3d_rect(surface, c, pygame.Rect(cx+10, cy-18 - recoil_scale/2, 16 + recoil_scale*2, 14 + recoil_scale), 4)
        pygame.draw.ellipse(surface, shade(c,-60), (cx+22 + recoil_scale*2, cy-16 - recoil_scale/2, 6, 10 + recoil_scale))
        draw_eye(surface, cx+4, cy-15 - recoil_scale/2, 3.5 + recoil_scale/3)

class Wallnut(Plant):
    def __init__(self, row, col): super().__init__(row, col, health=2000, cost=50)
    @staticmethod
    def draw_model(surface, cx, cy, instance=None):
        ratio = instance.health / instance.max_health if instance else 1.0
        c = (160, 82, 45)
        draw_sphere(surface, c, cx-2, cy-2, 22, scale_x=0.9, scale_y=1.1)
        
        pygame.draw.circle(surface, shade(c, -30), (int(cx-10), int(cy+10)), 3)
        pygame.draw.circle(surface, shade(c, -30), (int(cx+12), int(cy+5)), 2)
        pygame.draw.circle(surface, shade(c, -30), (int(cx-14), int(cy-5)), 2)
        pygame.draw.circle(surface, shade(c, -30), (int(cx+8), int(cy-10)), 2)

        is_sad = ratio < 0.6
        if is_sad: 
            pygame.draw.line(surface, (100, 40, 20), (cx-10, cy-20), (cx+5, cy-5), 3) 
            pygame.draw.arc(surface, (0,0,0), (cx-5, cy-2, 10, 8), 0, math.pi, 2) 
        else:
            pygame.draw.arc(surface, (0,0,0), (cx-5, cy-2, 10, 8), math.pi, 2*math.pi, 2) 
            
        if ratio < 0.3: 
            pygame.draw.line(surface, (100, 40, 20), (cx+10, cy), (cx-5, cy+15), 3) 
            pygame.draw.rect(surface, (200, 200, 200), (cx-10, cy-20, 15, 6)) 
            
        draw_eye(surface, cx-7, cy-8, 4, sad=is_sad)
        draw_eye(surface, cx+7, cy-8, 4, sad=is_sad)

class Tallnut(Plant):
    def __init__(self, row, col): super().__init__(row, col, health=4000, cost=125)
    @staticmethod
    def draw_model(surface, cx, cy, instance=None):
        ratio = instance.health / instance.max_health if instance else 1.0
        c = (150, 75, 40)
        cy -= 15 
        draw_sphere(surface, c, cx-2, cy-2, 22, scale_x=0.9, scale_y=1.8)
        
        pygame.draw.circle(surface, shade(c, -30), (int(cx-10), int(cy+20)), 3)
        pygame.draw.circle(surface, shade(c, -30), (int(cx+12), int(cy+15)), 2)
        pygame.draw.circle(surface, shade(c, -30), (int(cx-14), int(cy-25)), 2)
        
        is_sad = ratio < 0.6
        if is_sad: pygame.draw.line(surface, (100, 40, 20), (cx-10, cy-30), (cx+10, cy-15), 4) 
        
        draw_eye(surface, cx-8, cy-15, 4.5, angry=not is_sad, sad=is_sad)
        draw_eye(surface, cx+8, cy-15, 4.5, angry=not is_sad, sad=is_sad)
        pygame.draw.line(surface, (0,0,0), (cx-6, cy-5), (cx+6, cy-5), 2) 

class PotatoMine(Plant):
    def __init__(self, row, col): super().__init__(row, col, health=300, cost=25); self.armed = False
    def update(self, zombies, projectiles, suns, particles, damage_mult=1.0):
        if not self.armed and time.time() - self.birth > 3.0: self.armed = True
        if self.armed:
            for z in zombies:
                if z.row == self.row and abs(z.x - self.cx) < 40 and not getattr(z, 'untargetable', False):
                    self.health = 0; z.take_damage(2000 * damage_mult, False)
                    particles.append({"type": "shake", "amount": 12})
                    particles.append({"x": self.cx, "y": self.cy, "radius": 40, "color": (200, 100, 50), "life": 20, "max_life": 20, "type": "ring"})
                    particles.append({"x": self.cx, "y": self.cy, "radius": 25, "color": (255, 100, 50), "life": 15, "max_life": 15}); break
    @staticmethod
    def draw_model(surface, cx, cy, instance=None):
        pygame.draw.ellipse(surface, (80, 50, 20), (cx-18, cy+8, 36, 18))
        pygame.draw.ellipse(surface, (100, 60, 30), (cx-15, cy+10, 30, 15))
        
        if not (instance.armed if instance else True): 
            draw_3d_rect(surface, (200, 200, 200), pygame.Rect(cx-4, cy, 8, 10), 2)
        else:
            draw_sphere(surface, (180, 140, 100), cx, cy-4, 12, 1.0, 1.0) 
            draw_3d_rect(surface, (150, 150, 150), pygame.Rect(cx-2, cy-20, 4, 10), 1) 
            draw_sphere(surface, (255, 50, 50) if int(time.time() * 5) % 2 == 0 else (100, 0, 0), cx, cy-20, 4, 1.0, 1.0) 
            draw_eye(surface, cx-4, cy-4, 2.5); draw_eye(surface, cx+4, cy-4, 2.5) 

class CherryBomb(Plant):
    def __init__(self, row, col): super().__init__(row, col, health=300, cost=150)
    def update(self, zombies, projectiles, suns, particles, damage_mult=1.0):
        dt = time.time() - self.birth
        if dt > 1.2:
            self.health = 0
            particles.append({"type": "shake", "amount": 15})
            particles.append({"x": self.cx, "y": self.cy, "radius": 60, "color": (255, 100, 50), "life": 20, "max_life": 20, "type": "ring"})
            particles.append({"x": self.cx, "y": self.cy, "radius": 45, "color": (255, 50, 50), "life": 25, "max_life": 25})
            for z in zombies:
                if abs(z.row - self.row) <= 1 and abs(z.x - self.cx) <= CELL_WIDTH * 1.5 and not getattr(z, 'untargetable', False): 
                    z.take_damage(1800 * damage_mult, False)
    @staticmethod
    def draw_model(surface, cx, cy, instance=None):
        dt = (time.time() - instance.birth) if instance else 0
        swell = (dt / 1.2)**3 * 18 if instance else 0 
        flash_speed = 10 + (dt * 30)
        is_flashing = math.sin(dt * flash_speed) > 0 if instance else False
        c = (255, 50, 50) if is_flashing else (200, 20, 20)
        cx += random.randint(-2, 2) if (dt > 0.8 and instance) else 0 
        pygame.draw.line(surface, (50, 200, 50), (cx, cy-5), (cx-12, cy-25 - swell), 4) 
        pygame.draw.line(surface, (50, 200, 50), (cx, cy-5), (cx+12, cy-20 - swell), 4) 
        draw_leaf(surface, (50, 200, 50), cx, cy-5, 12, 8, 0) 
        draw_sphere(surface, c, cx-14 - swell//2, cy-5, int(14 + swell), 1.0, 1.0)
        draw_sphere(surface, c, cx+14 + swell//2, cy, int(13 + swell), 1.0, 1.0)
        eye_r = 3 + swell*0.1
        draw_eye(surface, cx-18 - swell//2, cy-8, eye_r, angry=True); draw_eye(surface, cx-10 - swell//2, cy-8, eye_r, angry=True)
        draw_eye(surface, cx+10 + swell//2, cy-3, eye_r, angry=True); draw_eye(surface, cx+18 + swell//2, cy-3, eye_r, angry=True)

class Squash(Plant):
    def __init__(self, row, col): super().__init__(row, col, health=300, cost=50); self.state, self.jump_time = "IDLE", 0
    def update(self, zombies, projectiles, suns, particles, damage_mult=1.0):
        if self.state == "IDLE":
            if any(z.row == self.row and abs(z.x - self.cx) < CELL_WIDTH and not getattr(z, 'untargetable', False) for z in zombies): 
                self.state, self.jump_time = "JUMPING", time.time()
        elif self.state == "JUMPING" and time.time() - self.jump_time > 0.5:
            self.health = 0
            particles.append({"type": "shake", "amount": 10})
            particles.append({"x": self.cx, "y": self.cy, "radius": 30, "color": (50, 150, 50), "life": 20, "max_life": 20})
            for z in zombies:
                if z.row == self.row and abs(z.x - self.cx) < CELL_WIDTH * 1.2 and not getattr(z, 'untargetable', False): 
                    z.take_damage(1800 * damage_mult, False)
    @staticmethod
    def draw_model(surface, cx, cy, instance=None):
        jump_y = -math.sin(((time.time() - instance.jump_time) / 0.5) * math.pi) * 60 if instance and instance.state == "JUMPING" else 0
        c = (50, 150, 50)
        pygame.draw.ellipse(surface, shade(c,-40), (cx-22, cy-30 + int(jump_y), 44, 54))
        pygame.draw.ellipse(surface, c, (cx-20, cy-28 + int(jump_y), 40, 50))
        pygame.draw.ellipse(surface, shade(c, 40), (cx-10, cy-25 + int(jump_y), 15, 40)) 
        draw_3d_rect(surface, (20, 100, 20), pygame.Rect(cx-5, cy-40 + int(jump_y), 10, 15), 3) 
        draw_eye(surface, cx-8, cy-10 + jump_y, 4, angry=True)
        draw_eye(surface, cx+8, cy-10 + jump_y, 4, angry=True)

class Chomper(Plant):
    def __init__(self, row, col): super().__init__(row, col, health=300, cost=150); self.state, self.eat_time = "IDLE", 0
    def update(self, zombies, projectiles, suns, particles, damage_mult=1.0):
        super().update(zombies, projectiles, suns, particles, damage_mult)
        if self.state == "IDLE":
            for z in zombies:
                if z.row == self.row and 0 <= (z.x - self.cx) < CELL_WIDTH and not getattr(z, 'untargetable', False):
                    z.take_damage(2000 * damage_mult, False); self.state, self.eat_time = "CHEWING", time.time()
                    particles.append({"x": self.cx, "y": self.cy, "radius": 30, "color": (138, 43, 226), "life": 15, "max_life": 15}); break
        elif self.state == "CHEWING" and time.time() - self.eat_time > 15.0: self.state = "IDLE"
    @staticmethod
    def draw_model(surface, cx, cy, instance=None):
        draw_leaf(surface, (34, 139, 34), cx, cy+15, 30, 15, 0)
        draw_3d_rect(surface, (50, 205, 50), pygame.Rect(cx-4, cy-5, 8, 25), 4) 
        pygame.draw.polygon(surface, (30, 100, 30), [(cx-4, cy+5), (cx-10, cy+2), (cx-4, cy)])
        
        chew = 0
        if instance and instance.state == "CHEWING":
            dt = time.time() - instance.eat_time
            if dt < 0.2: chew = -18 
            elif dt < 0.4: chew = 6 
            else: chew = math.sin(dt * 15) * 4 
            
        c = (138, 43, 226)
        if chew < 0:
            pygame.draw.ellipse(surface, (30, 0, 50), (cx-15, cy-20+chew, 30, 20 - chew*2))
        
        pygame.draw.ellipse(surface, shade(c, -20), (cx-18, cy-15 - chew//2, 36, 20))
        for i in range(4):
            tx = cx - 14 + i*8
            pygame.draw.polygon(surface, (200, 200, 200), [(tx, cy-10-chew//2), (tx+7, cy-10-chew//2), (tx+3, cy-18-chew//2)]) 
        
        pygame.draw.ellipse(surface, c, (cx-18, cy-32 + chew, 36, 25))
        for i in range(4):
            tx = cx - 14 + i*8
            pygame.draw.polygon(surface, (255, 255, 255), [(tx, cy-15+chew), (tx+7, cy-15+chew), (tx+3, cy-5+chew)])
            
        draw_eye(surface, cx-6, cy-25 + chew, 3, angry=True)

class Jalapeno(Plant):
    def __init__(self, row, col): super().__init__(row, col, health=300, cost=125); self.plant_time = time.time()
    def update(self, zombies, projectiles, suns, particles, damage_mult=1.0):
        if time.time() - self.plant_time > 0.8:
            self.health = 0
            particles.append({"type": "shake", "amount": 15})
            for c in range(GRID_COLS):
                particles.append({"x": c * CELL_WIDTH + 40, "y": self.cy, "radius": 40, "color": (255, 100, 0), "life": 25, "max_life": 25})
                particles.append({"x": c * CELL_WIDTH + 40, "y": self.cy, "radius": 25, "color": (255, 255, 0), "life": 15, "max_life": 15})
            for z in zombies:
                if z.row == self.row and not getattr(z, 'untargetable', False): z.take_damage(2000 * damage_mult, False)
    @staticmethod
    def draw_model(surface, cx, cy, instance=None):
        dt = (time.time() - instance.plant_time) if instance else 0
        swell = (dt / 0.8)**3 * 15 if instance else 0 
        cx += random.randint(-3, 3) if (dt > 0.4 and instance) else 0 
        flash = int(min(1.0, dt / 0.8) * 50) if instance else 0
        c = (min(255, 220 + flash), max(0, 20 - flash), max(0, 20 - flash)) 
        draw_3d_rect(surface, (50, 205, 50), pygame.Rect(cx-3, cy-35 - swell, 6, 15), 3) 
        pygame.draw.arc(surface, (50, 205, 50), (cx-10, cy-40 - swell, 10, 10), 0, math.pi, 3) 
        pygame.draw.ellipse(surface, shade(c,-40), (cx-12 - swell//2, cy-25 - swell//2, 24 + swell, 45 + swell))
        pygame.draw.ellipse(surface, c, (cx-10 - swell//2, cy-23 - swell//2, 20 + swell, 41 + swell))
        pygame.draw.ellipse(surface, shade(c,40), (cx-4, cy-15, 6 + swell//3, 25 + swell//2)) 
        eye_r = 3 + swell*0.1
        draw_eye(surface, cx-5 - swell//4, cy-10, eye_r, angry=True); draw_eye(surface, cx+5 + swell//4, cy-10, eye_r, angry=True)

class Puffshroom(Plant):
    def __init__(self, row, col): super().__init__(row, col, health=150, cost=0); self.last_shot = time.time()
    def update(self, zombies, projectiles, suns, particles, damage_mult=1.0):
        super().update(zombies, projectiles, suns, particles, damage_mult)
        if any(z.row == self.row and 0 <= z.x - self.cx < CELL_WIDTH*3 and not getattr(z, 'untargetable', False) for z in zombies) and time.time() - self.last_shot > 1.5:
            self.last_shot, self.recoil = time.time(), 10
            particles.append({"x": self.cx + 15, "y": self.cy - 5, "radius": 5, "color": (200, 100, 200), "life": 8, "max_life": 8}) 
            p = Projectile(self.row, self.cx + 5, self.cy - 5, False)
            p.damage = 10 * damage_mult 
            p.color = (180, 100, 200) 
            p.max_range = self.cx + CELL_WIDTH * 3 
            projectiles.append(p)
    @staticmethod
    def draw_model(surface, cx, cy, instance=None):
        recoil = instance.recoil/2 if instance else 0
        c = (150, 50, 150)
        draw_3d_rect(surface, (200, 200, 200), pygame.Rect(cx-6, cy-5, 12, 15), 3) 
        pygame.draw.ellipse(surface, shade(c, -40), (cx-14, cy-15, 28 + recoil, 15)) 
        pygame.draw.ellipse(surface, c, (cx-12, cy-14, 24 + recoil, 13)) 
        draw_sphere(surface, (250, 150, 250), cx-6, cy-10, 3, 1.0, 1.0) 
        draw_sphere(surface, (250, 150, 250), cx+6, cy-8, 2, 1.0, 1.0)
        draw_eye(surface, cx-4, cy-2, 2.5); draw_eye(surface, cx+4, cy-2, 2.5)

class IceShroom(Plant):
    def __init__(self, row, col): super().__init__(row, col, health=300, cost=75); self.spawn_time = time.time()
    def update(self, zombies, projectiles, suns, particles, damage_mult=1.0):
        if time.time() - self.spawn_time > 1.0:
            self.health = 0
            particles.append({"type": "shake", "amount": 8})
            for z in zombies:
                if not getattr(z, 'untargetable', False):
                    z.freeze_time = time.time() 
                    z.chill_time = time.time() + 4.0 
            for c in range(GRID_COLS):
                for r in range(GRID_ROWS):
                    if random.random() < 0.3:
                        particles.append({"x": c*CELL_WIDTH+40, "y": r*CELL_HEIGHT+GRID_START_Y+40, "radius": 20, "color": (150, 200, 255), "life": 15, "max_life": 15})
    @staticmethod
    def draw_model(surface, cx, cy, instance=None):
        dt = (time.time() - instance.spawn_time) if instance else 0
        swell = dt * 10 if instance else 0 
        c = (150, 220, 255)
        draw_3d_rect(surface, (100, 150, 200), pygame.Rect(cx-8, cy-5, 16, 15), 3) 
        draw_sphere(surface, c, cx, cy-15, 20 + swell, 1.3, 0.7)
        draw_eye(surface, cx-5, cy-15, 3); draw_eye(surface, cx+5, cy-15, 3)

class Spikeweed(Plant):
    def __init__(self, row, col): super().__init__(row, col, health=300, cost=100); self.last_dmg = 0
    def update(self, zombies, projectiles, suns, particles, damage_mult=1.0):
        t = time.time()
        if t - self.last_dmg > 0.5:
            for z in zombies:
                if z.row == self.row and abs(z.x - self.cx) < CELL_WIDTH//2 and not getattr(z, 'untargetable', False):
                    z.take_damage(15 * damage_mult, False) 
                    self.last_dmg = t
                    particles.append({"x": z.x, "y": self.cy+20, "radius": 3, "color": (150, 150, 150), "life": 5, "max_life": 5})
    @staticmethod
    def draw_model(surface, cx, cy, instance=None):
        cy += 20 
        for i in range(5):
            ox = cx - 15 + i*7
            h = 10 + (i%2)*5
            pygame.draw.polygon(surface, (150, 150, 150), [(ox-3, cy), (ox+3, cy), (ox, cy-h)])
            pygame.draw.polygon(surface, (200, 200, 200), [(ox, cy), (ox+3, cy), (ox, cy-h)]) 

class RiceGuard(Plant):
    def __init__(self, row, col): 
        super().__init__(row, col, health=3000, cost=150)
        self.last_attack = time.time()
        self.is_blocking = False
    
    def update(self, zombies, projectiles, suns, particles, damage_mult=1.0):
        super().update(zombies, projectiles, suns, particles, damage_mult)
        self.is_blocking = any(z.row == self.row and 0 <= z.x - self.cx < CELL_WIDTH and not getattr(z, 'untargetable', False) for z in zombies)
        
        if time.time() - self.last_attack > 1.2:
            target = next((z for z in zombies if z.row == self.row and 0 <= z.x - self.cx <= CELL_WIDTH * 2.2 and not getattr(z, 'untargetable', False)), None)
            if target:
                self.last_attack = time.time()
                self.recoil = 30 
                target.take_damage(51 * damage_mult, False) 
                
                for _ in range(5):
                    particles.append({
                        "x": target.x, "y": self.cy + random.randint(-10, 10), 
                        "radius": random.randint(3, 6), "color": (255, 255, 200), 
                        "life": 12, "max_life": 12, "vx": random.uniform(2, 6), "vy": random.uniform(-2, 2)
                    })

    @staticmethod
    def draw_model(surface, cx, cy, instance=None):
        recoil = instance.recoil if instance else 0
        is_blocking = instance.is_blocking if instance else False
        
        thrust_ext = recoil * 1.5
        spear_x = cx + 5 + thrust_ext
        spear_y = cy + 5
        
        if recoil > 10:
            pygame.draw.line(surface, (200, 200, 200), (cx + 30, spear_y - 2), (spear_x + 20, spear_y - 2), 2)
            pygame.draw.line(surface, (200, 200, 200), (cx + 30, spear_y + 2), (spear_x + 20, spear_y + 2), 2)

        pygame.draw.line(surface, (150, 120, 60), (cx-15, spear_y), (spear_x + 30, spear_y), 4) 
        pygame.draw.polygon(surface, (180, 180, 170), [(spear_x + 30, spear_y-4), (spear_x + 30, spear_y+4), (spear_x + 50, spear_y)]) 
        pygame.draw.polygon(surface, (240, 240, 230), [(spear_x + 30, spear_y-2), (spear_x + 30, spear_y+2), (spear_x + 48, spear_y)]) 
        
        c_body = (235, 195, 85) 
        
        draw_leaf(surface, (80, 160, 40), cx - 5, cy + 15, 15, 8, 30)
        draw_leaf(surface, (80, 160, 40), cx + 5, cy + 15, 15, 8, -30)

        draw_sphere(surface, c_body, cx, cy - 2, 18, scale_x=0.8, scale_y=1.25)
        
        pygame.draw.arc(surface, shade(c_body, -40), (cx-10, cy-22, 20, 40), -math.pi/2, math.pi/2, 2)
        pygame.draw.arc(surface, shade(c_body, 40), (cx-6, cy-20, 12, 36), -math.pi/2, math.pi/2, 2)
        
        draw_eye(surface, cx-4, cy-10, 3.5, angry=True)
        draw_eye(surface, cx+6, cy-10, 3.5, angry=True)
        pygame.draw.line(surface, (0, 0, 0), (cx-2, cy-4), (cx+4, cy-4), 2) 
        
        shield_c = (160, 110, 50) 
        if is_blocking:
            swing_x = math.sin(time.time() * 30) * 5
            swing_y = math.cos(time.time() * 30) * 3
            sx, sy = cx + 8 + swing_x, cy - 14 + swing_y
            draw_3d_rect(surface, shield_c, pygame.Rect(sx, sy, 12, 34), border_radius=4)
            pygame.draw.line(surface, shade(shield_c, -50), (sx+3, sy+4), (sx+3, sy+30), 1)
            pygame.draw.line(surface, shade(shield_c, -50), (sx+8, sy+4), (sx+8, sy+30), 1)
        else:
            sx, sy = cx + 10, cy - 5
            draw_3d_rect(surface, shield_c, pygame.Rect(sx, sy, 10, 26), border_radius=3)
            pygame.draw.line(surface, shade(shield_c, -50), (sx+4, sy+3), (sx+4, sy+23), 1)

class PigHeadPersimmon(Plant):
    def __init__(self, row, col):
        super().__init__(row, col, health=300, cost=200)
        self.spawn_time = time.time()
        self.transformed = False
        self.last_ha = 0
        
    def update(self, zombies, projectiles, suns, particles, damage_mult=1.0):
        dt = time.time() - self.spawn_time
        
        if dt <= 4.0:
            for z in zombies:
                if abs(z.row - self.row) <= 1 and abs(z.x - self.cx) <= CELL_WIDTH * 1.5 and not getattr(z, 'untargetable', False):
                    z.stun_time = time.time() 
            
            if time.time() - self.last_ha > 0.25:
                self.last_ha = time.time()
                particles.append({
                    "type": "text", "text": "Ha!", 
                    "x": self.cx + random.randint(-20, 20), "y": self.cy - random.randint(25, 45), 
                    "color": (255, 220, 50), "life": 25, "max_life": 25, 
                    "vx": random.uniform(-1, 1), "vy": -2
                })
                
        elif not self.transformed:
            self.transformed = True
            self.health = 0 
            
            for i in range(len(zombies)):
                z = zombies[i]
                if abs(z.row - self.row) <= 1 and abs(z.x - self.cx) <= CELL_WIDTH * 1.5 and not getattr(z, 'untargetable', False):
                    new_z = Zombie(z.row)
                    new_z.x = z.x
                    new_z.chill_time = z.chill_time
                    zombies[i] = new_z 
                    
                    particles.append({"type": "shake", "amount": 8})
                    for _ in range(6):
                        particles.append({
                            "x": z.x, "y": z.y, "radius": random.randint(8, 16), 
                            "color": (200, 200, 200), "life": 20, "max_life": 20, 
                            "vx": random.uniform(-3, 3), "vy": random.uniform(-3, 3)
                        })

    @staticmethod
    def draw_model(surface, cx, cy, instance=None):
        dt = (time.time() - instance.spawn_time) if instance else 0
        is_laughing = instance and dt <= 4.0
        
        bob = math.sin(time.time() * 25) * 4 if is_laughing else 0
        cy += int(bob)
        
        c_body = (255, 120, 30) 
        
        draw_leaf(surface, (50, 150, 40), cx-12, cy-15, 14, 8, -30)
        draw_leaf(surface, (50, 150, 40), cx+12, cy-15, 14, 8, 30)
        draw_leaf(surface, (40, 130, 30), cx, cy-20, 14, 8, 0)
        
        pygame.draw.polygon(surface, shade(c_body, 20), [(cx-15, cy-10), (cx-28, cy-20), (cx-5, cy-16)])
        pygame.draw.polygon(surface, shade(c_body, 20), [(cx+15, cy-10), (cx+28, cy-20), (cx+5, cy-16)])
        
        draw_sphere(surface, c_body, cx, cy, 18, 1.2, 0.95)
        
        snout_c = (255, 160, 120)
        pygame.draw.ellipse(surface, shade(snout_c, -30), (cx-11, cy-3, 22, 16))
        pygame.draw.ellipse(surface, snout_c, (cx-9, cy-1, 18, 12))
        pygame.draw.circle(surface, (0,0,0), (cx-4, cy+5), 2)
        pygame.draw.circle(surface, (0,0,0), (cx+4, cy+5), 2)
        
        draw_eye(surface, cx-9, cy-8, 3.5)
        draw_eye(surface, cx+9, cy-8, 3.5)
        
        if is_laughing:
            pygame.draw.ellipse(surface, (50,0,0), (cx-7, cy+11, 14, 10))
            pygame.draw.ellipse(surface, (200,50,50), (cx-5, cy+15, 10, 5))

# --- High-Fidelity Zombies ---
class Zombie:
    def __init__(self, row):
        self.row, self.x, self.y = row, SCREEN_WIDTH, row * CELL_HEIGHT + GRID_START_Y + CELL_HEIGHT // 2
        self.health, self.base_speed = 200, 0.22 
        self.state, self.last_attack, self.chill_time, self.flash_time, self.birth = "WALKING", time.time(), 0, 0, time.time()
        self.stun_time = 0
        self.freeze_time = 0
        self.untargetable = False

    def take_damage(self, amt, is_ice):
        if getattr(self, 'untargetable', False): return
        self.health -= amt; self.flash_time = time.time()
        if is_ice: self.chill_time = time.time()

    def update(self, plants, particles=None):
        if time.time() - getattr(self, 'freeze_time', 0) < 4.0:
            self.state = "FROZEN"
            return
            
        if time.time() - getattr(self, 'stun_time', 0) < 3.0:
            self.state = "LAUGHING"
            return
            
        speed_mod = 0.5 if (time.time() - self.chill_time < 3.0) else 1.0
        my_rect = pygame.Rect(self.x - 20, self.y - 30, 40, 60)
        colliding = next((p for p in plants if p.row == self.row and not isinstance(p, Spikeweed) and my_rect.colliderect(pygame.Rect(p.cx-30, p.cy-30, 60, 60))), None)

        if colliding:
            self.state = "EATING"
            if time.time() - self.last_attack > (1.0 / speed_mod):
                colliding.health -= 25; self.last_attack = time.time()
        else:
            self.state = "WALKING"; self.x -= self.base_speed * speed_mod

    def draw(self, surface):
        cx, cy = int(getattr(self, 'x', 0)), int(getattr(self, 'y', 0)) + int(getattr(self, 'flight_y', 0))
        t = time.time() - self.birth
        
        walk_s = 12 * (self.base_speed / 0.22)
        is_walking = self.state == "WALKING"
        is_eating = self.state == "EATING"
        is_laughing = self.state == "LAUGHING"
        is_frozen = self.state == "FROZEN"

        bob = math.sin(t * walk_s) * 3 if is_walking else 0
        leg_swing = math.sin(t * walk_s) * 8 if is_walking else 0
        leg_lift_l = max(0, math.sin(t * walk_s)) * 6 if is_walking else 0
        leg_lift_r = max(0, -math.sin(t * walk_s)) * 6 if is_walking else 0
        arm_swing = math.sin(t * walk_s + math.pi) * 5 if is_walking else 0 

        eat_t = t * 15 if is_eating else 0
        eat_bob = math.sin(eat_t) * 3 if is_eating else 0
        eat_reach = math.sin(eat_t) * 5 if is_eating else 0
        jaw_drop = max(0, math.sin(eat_t)) * 4 if is_eating else 0
        
        if is_laughing:
            bob = math.sin(time.time() * 30) * 5 

        cy += int(bob)

        is_chilled, is_flashing = (time.time() - self.chill_time < 3.0) or is_frozen, (time.time() - self.flash_time < 0.1)
        skin, coat, pants = ((130, 160, 255) if is_chilled else (90, 150, 90)), ((100, 100, 200) if is_chilled else (139, 69, 19)), ((70, 70, 150) if is_chilled else (90, 90, 110))
        if is_flashing: skin = coat = pants = (255, 255, 255)

        # Arms
        if is_eating:
            draw_3d_rect(surface, coat, pygame.Rect(cx-10 - int(eat_reach), cy-12, 18, 10), 3) 
            draw_3d_rect(surface, skin, pygame.Rect(cx-10 - int(eat_reach) - 6, cy-12, 6, 8), 2) 
        elif is_walking or is_laughing or is_frozen: 
            draw_3d_rect(surface, coat, pygame.Rect(cx-5 + int(arm_swing), cy-12, 10, 14), 4)
            draw_3d_rect(surface, coat, pygame.Rect(cx-5 + int(arm_swing) + 5, cy-2, 12, 8), 3) 

        # Legs
        draw_3d_rect(surface, pants, pygame.Rect(cx-10 - int(leg_swing), cy+5-int(bob) - int(leg_lift_l), 10, 25 - int(leg_lift_l)), 4) 
        draw_3d_rect(surface, pants, pygame.Rect(cx-2 + int(leg_swing), cy+5-int(bob) - int(leg_lift_r), 10, 25 - int(leg_lift_r)), 4)
        
        # Body 
        draw_3d_rect(surface, coat, pygame.Rect(cx-16, cy-20, 32, 32), 6) 
        pygame.draw.rect(surface, (200,200,200), (cx-10, cy-20, 12, 15)) 
        
        # Red Tie
        pygame.draw.polygon(surface, (180, 40, 40), [(cx-4, cy-20), (cx, cy-20), (cx-2, cy-8)]) 
        pygame.draw.polygon(surface, C_BG, [(cx-16, cy+12), (cx-10, cy+6), (cx-4, cy+12), (cx+2, cy+6), (cx+8, cy+12), (cx+16, cy+8), (cx+16, cy+15), (cx-16, cy+15)])

        # Front Arm
        if is_eating:
            draw_3d_rect(surface, coat, pygame.Rect(cx-12 + int(eat_reach), cy-6, 18, 10), 3) 
            draw_3d_rect(surface, skin, pygame.Rect(cx-12 + int(eat_reach) - 6, cy-6, 6, 8), 2) 
        else:
            arm_w, arm_y = (20, cy-12) if is_walking else (12, cy-5)
            draw_3d_rect(surface, coat, pygame.Rect(cx-16 - (arm_w if is_walking else 5) - int(arm_swing), arm_y, arm_w, 10), 4)
            if is_walking or is_laughing or is_frozen: draw_3d_rect(surface, skin, pygame.Rect(cx-16 - arm_w - int(arm_swing) - 8, arm_y+1, 8, 8), 3) 
        
        # Head
        head_y = cy - 48 + int(eat_bob)
        draw_3d_rect(surface, skin, pygame.Rect(cx-18, head_y, 36, 36), 8) 
        eye_c = (255,0,0) if getattr(self, 'angry', False) else (0,0,0)
        draw_eye(surface, cx-6, head_y + 12, 5.5) 
        pygame.draw.circle(surface, eye_c, (cx-6, head_y + 12), 2)
        
        if is_laughing:
            pygame.draw.ellipse(surface, (0,0,0), (cx-12, cy-15+bob, 16, 12))
            pygame.draw.ellipse(surface, (200,50,50), (cx-8, cy-8+bob, 8, 4))
        else:
            jaw_y = cy - 20 + int(eat_bob) + int(jaw_drop)
            draw_3d_rect(surface, shade(skin, -30), pygame.Rect(cx-16, jaw_y, 16, 10 + int(jaw_drop)), 4) 
            pygame.draw.rect(surface, (0,0,0), (cx-12, jaw_y, 12, 4 + int(jaw_drop))) 
            for i in range(3): pygame.draw.rect(surface, (220, 220, 200), (cx-11 + i*4, jaw_y, 3, 4 + int(jaw_drop//2))) 
        
        self.draw_headgear(surface, cx, cy + int(eat_bob))
        
        if is_frozen:
            s = pygame.Surface((60, 90), pygame.SRCALPHA)
            pygame.draw.rect(s, (100, 200, 255, 120), (0, 0, 60, 90), border_radius=10)
            pygame.draw.rect(s, (200, 255, 255, 200), (0, 0, 60, 90), 3, border_radius=10)
            surface.blit(s, (cx - 30, cy - 60))

    def draw_headgear(self, surface, cx, cy): pass

class FlagZombie(Zombie):
    def __init__(self, row): super().__init__(row); self.base_speed = 0.3
    def draw_headgear(self, surface, cx, cy):
        draw_3d_rect(surface, (180, 180, 180), pygame.Rect(cx-20, cy-55, 4, 70), 2)
        pygame.draw.rect(surface, (220, 40, 40), (cx-18, cy-55, 30, 18))
        pygame.draw.rect(surface, (0, 0, 0), (cx-10, cy-50, 15, 8)) 

class ConeheadZombie(Zombie):
    def __init__(self, row): super().__init__(row); self.health = 500
    def draw_headgear(self, surface, cx, cy):
        if self.health > 200: 
            pygame.draw.polygon(surface, (255, 140, 0), [(cx-16, cy-46), (cx+16, cy-46), (cx, cy-85)])
            pygame.draw.polygon(surface, (255, 180, 50), [(cx-6, cy-46), (cx+4, cy-46), (cx, cy-80)]) 
            pygame.draw.ellipse(surface, (255, 140, 0), (cx-18, cy-50, 36, 10))
            pygame.draw.line(surface, (200, 100, 0), (cx-10, cy-65), (cx+10, cy-65), 3) 

class BucketheadZombie(Zombie):
    def __init__(self, row): super().__init__(row); self.health = 1300
    def draw_headgear(self, surface, cx, cy):
        if self.health > 200:
            draw_3d_rect(surface, (180, 180, 180), pygame.Rect(cx-18, cy-75, 36, 30), 2)
            draw_3d_rect(surface, (150, 150, 150), pygame.Rect(cx-20, cy-50, 40, 8), 3)
            pygame.draw.polygon(surface, (150, 0, 0), [(cx-6, cy-65), (cx+6, cy-65), (cx+10, cy-50), (cx-10, cy-50)])

class NewspaperZombie(Zombie):
    def __init__(self, row):
        super().__init__(row); self.health, self.base_speed, self.angry = 300, 0.15, False
    def update(self, plants, particles=None):
        if time.time() - getattr(self, 'freeze_time', 0) < 4.0:
            self.state = "FROZEN"
            return
        if time.time() - getattr(self, 'stun_time', 0) < 3.0:
            self.state = "LAUGHING"
            return
        if self.health <= 150 and not self.angry: self.angry, self.base_speed = True, 0.65
        super().update(plants, particles)
    def draw_headgear(self, surface, cx, cy):
        if not self.angry:
            draw_3d_rect(surface, (240, 240, 230), pygame.Rect(cx-28, cy-35, 24, 34), 2)
            pygame.draw.line(surface, (100, 100, 100), (cx-24, cy-30), (cx-8, cy-30), 2)
            pygame.draw.line(surface, (100, 100, 100), (cx-24, cy-24), (cx-12, cy-24), 2)
            pygame.draw.line(surface, (100, 100, 100), (cx-24, cy-18), (cx-8, cy-18), 2)

class RatKingZombie(Zombie):
    def __init__(self, row):
        super().__init__(row)
        self.health = 400
        self.base_speed = 0.22 
        self.charge_speed = 1.0 
        self.state = "CHARGING"
        self.last_skill_time = 0
        self.skill_cooldown = 8.0
        
    def update(self, plants, particles=None):
        if time.time() - getattr(self, 'freeze_time', 0) < 4.0:
            self.state = "FROZEN"
            return
        if time.time() - getattr(self, 'stun_time', 0) < 3.0:
            self.state = "LAUGHING"
            return
            
        current_time = time.time()
        speed_mod = 0.5 if (current_time - self.chill_time < 3.0) else 1.0
        
        if self.state in ["WALKING", "EATING"] and current_time - self.last_skill_time > self.skill_cooldown:
            self.state = "CHARGING"
            
        if self.state == "CHARGING":
            self.x -= self.charge_speed * speed_mod
            
            if particles is not None and random.random() < 0.4:
                particles.append({"x": self.x + 20, "y": self.y + random.randint(-20, 20), "radius": 4, "color": (200, 200, 255), "life": 10, "max_life": 10})
                
            my_rect = pygame.Rect(self.x - 20, self.y - 30, 40, 60)
            colliding = next((p for p in plants if p.row == self.row and not isinstance(p, Spikeweed) and my_rect.colliderect(pygame.Rect(p.cx-30, p.cy-30, 60, 60))), None)
            
            if colliding:
                self.x = colliding.cx - 50 
                colliding.health -= 1500 
                
                self.state = "EATING" 
                self.last_attack = current_time
                self.last_skill_time = current_time
                
                if particles is not None:
                    particles.append({"type": "shake", "amount": 8})
                    particles.append({"x": colliding.cx, "y": self.y, "radius": 40, "color": (255, 255, 0), "life": 15, "max_life": 15, "type": "ring"}) 
        else:
            super().update(plants, particles)

    def draw(self, surface):
        cx, cy = int(self.x), int(self.y)
        t = time.time() - self.birth
        
        is_charging = self.state == "CHARGING"
        is_eating = self.state == "EATING"
        is_laughing = self.state == "LAUGHING"
        is_frozen = self.state == "FROZEN"
        walk_s = (12 * (self.charge_speed / 0.22)) if is_charging else (12 * (self.base_speed / 0.22))
        
        bob = math.sin(t * walk_s) * 3 if self.state in ["WALKING", "CHARGING"] else 0
        leg_swing = math.sin(t * walk_s) * 8 if self.state in ["WALKING", "CHARGING"] else 0
        leg_lift_l = max(0, math.sin(t * walk_s)) * 6 if self.state in ["WALKING", "CHARGING"] else 0
        leg_lift_r = max(0, -math.sin(t * walk_s)) * 6 if self.state in ["WALKING", "CHARGING"] else 0
        if is_laughing: bob = math.sin(time.time() * 30) * 5
        cy += int(bob)

        is_chilled, is_flashing = (time.time() - self.chill_time < 3.0) or is_frozen, (time.time() - self.flash_time < 0.1)
        
        skin = (130, 160, 255) if is_chilled else (90, 150, 90)
        coat_blue = (100, 100, 255) if is_chilled else (50, 100, 200)
        coat_white = (200, 200, 255) if is_chilled else (240, 240, 240)
        pants = (70, 70, 150) if is_chilled else (50, 50, 50)
        if is_flashing: skin = coat_blue = coat_white = pants = (255, 255, 255)

        if is_eating:
            swing = math.sin(time.time() * 15)
            draw_3d_rect(surface, coat_blue, pygame.Rect(cx-5, cy-15, 12, 10), 3) 
            draw_sword(surface, cx-10, cy-5, 180 + swing*45, 35) 
        else:
            pygame.draw.line(surface, coat_blue, (cx+10, cy-15), (cx, cy-60), 6) 
            draw_sword(surface, cx, cy-60, 135, 40) 

        draw_3d_rect(surface, pants, pygame.Rect(cx-10 - int(leg_swing), cy+5-int(bob) - int(leg_lift_l), 10, 25 - int(leg_lift_l)), 4) 
        draw_3d_rect(surface, pants, pygame.Rect(cx-2 + int(leg_swing), cy+5-int(bob) - int(leg_lift_r), 10, 25 - int(leg_lift_r)), 4)
        
        draw_3d_rect(surface, coat_blue, pygame.Rect(cx-16, cy-20, 32, 32), 6) 
        pygame.draw.polygon(surface, coat_white, [(cx-6, cy-20), (cx+6, cy-20), (cx, cy+5)]) 
        
        if is_eating:
            swing_alt = math.sin(time.time() * 15 + math.pi)
            draw_3d_rect(surface, coat_blue, pygame.Rect(cx-15, cy-12, 15, 10), 4)
            draw_sword(surface, cx-25, cy, 180 - swing_alt*45, 35) 
        else:
            pygame.draw.line(surface, coat_blue, (cx-10, cy-15), (cx, cy-65), 6) 
            draw_sword(surface, cx, cy-65, 45, 40) 
        
        draw_3d_rect(surface, skin, pygame.Rect(cx-16, cy-48, 32, 32), 6) 
        draw_eye(surface, cx-6, cy-36, 5.5, angry=True) 
        pygame.draw.circle(surface, (255, 0, 0), (cx-6, cy-36), 2) 
        
        if is_charging:
            pygame.draw.line(surface, (200, 255, 255), (cx+20, cy), (cx+40, cy), 2)
            pygame.draw.line(surface, (200, 255, 255), (cx+15, cy-20), (cx+35, cy-20), 2)
            
        if is_frozen:
            s = pygame.Surface((60, 90), pygame.SRCALPHA)
            pygame.draw.rect(s, (100, 200, 255, 120), (0, 0, 60, 90), border_radius=10)
            pygame.draw.rect(s, (200, 255, 255, 200), (0, 0, 60, 90), 3, border_radius=10)
            surface.blit(s, (cx - 30, cy - 60))

class FireBullZombie(Zombie):
    def __init__(self, row):
        super().__init__(row)
        self.health = 800  
        self.base_speed = 0.5  
        self.is_burning = True
        self.last_burn = time.time()
        
    def take_damage(self, amt, is_ice):
        super().take_damage(amt, is_ice)
        if is_ice and self.is_burning:
            self.is_burning = False
            self.base_speed = 0.20  

    def update(self, plants, particles=None):
        if time.time() - getattr(self, 'freeze_time', 0) < 4.0:
            self.state = "FROZEN"
            return
        if time.time() - getattr(self, 'stun_time', 0) < 3.0:
            self.state = "LAUGHING"
            return
            
        speed_mod = 0.5 if (time.time() - self.chill_time < 3.0) else 1.0
        
        if self.is_burning and particles is not None and random.random() < 0.6:
            particles.append({
                "x": self.x + random.randint(-20, 20), 
                "y": self.y - random.randint(10, 30), 
                "radius": random.randint(5, 10), 
                "color": random.choice([(255, 50, 0), (255, 150, 0), (255, 200, 50)]), 
                "life": 15, "max_life": 15, 
                "vy": random.uniform(-3, -1),
                "vx": random.uniform(-1, 1)
            })

        if self.is_burning and time.time() - self.last_burn > 0.5:
            for p in plants:
                if p.row == self.row and abs(p.cx - self.x) <= CELL_WIDTH * 1.2:
                    p.health -= 150  
                    self.last_burn = time.time()
                    if particles is not None:
                        particles.append({"type": "shake", "amount": 3})
                        for _ in range(5):
                            particles.append({
                                "x": p.cx + random.randint(-15, 15), 
                                "y": p.cy + random.randint(-15, 15), 
                                "radius": random.randint(3, 7), 
                                "color": (255, 100, 0), 
                                "life": 12, "max_life": 12, 
                                "vy": -3
                            })

        my_rect = pygame.Rect(self.x - 30, self.y - 30, 60, 60)
        colliding = next((p for p in plants if p.row == self.row and not isinstance(p, Spikeweed) and my_rect.colliderect(pygame.Rect(p.cx-30, p.cy-30, 60, 60))), None)

        if colliding:
            self.state = "EATING"
            if time.time() - self.last_attack > (1.0 / speed_mod):
                colliding.health -= 25
                self.last_attack = time.time()
        else:
            self.state = "WALKING"
            self.x -= self.base_speed * speed_mod

    def draw(self, surface):
        cx, cy = int(self.x), int(self.y)
        t = time.time() - self.birth
        
        walk_s = 12 * (self.base_speed / 0.22)
        is_walking = self.state == "WALKING"
        is_eating = self.state == "EATING"
        is_laughing = self.state == "LAUGHING"
        is_frozen = self.state == "FROZEN"

        bob = math.sin(t * walk_s) * 4 if is_walking else 0
        leg_swing = math.sin(t * walk_s) * 12 if is_walking else 0
        if is_laughing: bob = math.sin(time.time() * 30) * 5
        cy += int(bob)

        is_chilled, is_flashing = (time.time() - self.chill_time < 3.0) or is_frozen, (time.time() - self.flash_time < 0.1)
        
        body_c = (70, 30, 10)  
        if is_chilled: body_c = (100, 100, 180)
        if is_flashing: body_c = (255, 255, 255)
        
        draw_3d_rect(surface, body_c, pygame.Rect(cx + 10 - int(leg_swing), cy + 10, 10, 20), 4) 
        draw_3d_rect(surface, body_c, pygame.Rect(cx - 20 + int(leg_swing), cy + 10, 10, 20), 4) 
        draw_3d_rect(surface, shade(body_c, -30), pygame.Rect(cx + 20 + int(leg_swing), cy + 5, 10, 20), 4) 
        draw_3d_rect(surface, shade(body_c, -30), pygame.Rect(cx - 10 - int(leg_swing), cy + 5, 10, 20), 4) 
        
        draw_3d_rect(surface, body_c, pygame.Rect(cx - 30, cy - 20, 60, 40), 15)
        
        head_x = cx - 45
        head_y = cy - 15 + (math.sin(t * 15) * 3 if is_eating else 0)
        draw_3d_rect(surface, body_c, pygame.Rect(head_x, head_y, 35, 30), 8)
        
        pygame.draw.circle(surface, (200, 200, 200), (head_x + 5, head_y + 25), 6, 2)
        
        horn_c = (220, 220, 200)
        pygame.draw.polygon(surface, horn_c, [(head_x + 15, head_y + 5), (head_x + 25, head_y + 5), (head_x + 30, head_y - 15)])
        pygame.draw.polygon(surface, horn_c, [(head_x + 5, head_y + 5), (head_x + 15, head_y + 5), (head_x, head_y - 20)])
        
        eye_c = (255, 50, 0) if self.is_burning else (0, 0, 0)
        draw_eye(surface, head_x + 10, head_y + 12, 4.5, angry=True)
        pygame.draw.circle(surface, eye_c, (head_x + 10, head_y + 12), 2)
        
        if is_laughing:
            pygame.draw.ellipse(surface, (0,0,0), (head_x + 5, head_y + 18 + bob, 15, 10))
        
        if self.is_burning:
            for i in range(5):
                fx = cx - 25 + i * 12 + math.sin(t * 10 + i) * 5
                fy = cy - 25 - math.cos(t * 15 + i) * 5
                draw_leaf(surface, (255, 80, 0), fx, fy, 16, 30, math.sin(t*5+i)*20)
                draw_leaf(surface, (255, 200, 0), fx, fy+5, 10, 20, math.sin(t*5+i)*20)
                
        if is_frozen:
            s = pygame.Surface((80, 80), pygame.SRCALPHA)
            pygame.draw.rect(s, (100, 200, 255, 120), (0, 0, 80, 80), border_radius=10)
            pygame.draw.rect(s, (200, 255, 255, 200), (0, 0, 80, 80), 3, border_radius=10)
            surface.blit(s, (cx - 40, cy - 40))

class PoleVaultingZombie(Zombie):
    def __init__(self, row):
        super().__init__(row)
        self.health = 350
        self.base_speed = 0.5 
        self.has_jumped = False
        self.jump_timer = 0
        
    def update(self, plants, particles=None):
        if time.time() - getattr(self, 'freeze_time', 0) < 4.0:
            self.state = "FROZEN"
            return
        if time.time() - getattr(self, 'stun_time', 0) < 3.0:
            self.state = "LAUGHING"
            return
            
        if self.state == "JUMPING":
            if time.time() - self.jump_timer > 0.5:
                self.state = "WALKING"
                self.base_speed = 0.22 
            else:
                self.x -= 2 
            return

        speed_mod = 0.5 if (time.time() - self.chill_time < 3.0) else 1.0
        my_rect = pygame.Rect(self.x - 20, self.y - 30, 40, 60)
        colliding = next((p for p in plants if p.row == self.row and not isinstance(p, Spikeweed) and my_rect.colliderect(pygame.Rect(p.cx-30, p.cy-30, 60, 60))), None)

        if colliding:
            if not self.has_jumped:
                self.has_jumped = True
                self.state = "JUMPING"
                self.jump_timer = time.time()
                self.x -= CELL_WIDTH * 1.2 
            else:
                self.state = "EATING"
                if time.time() - self.last_attack > (1.0 / speed_mod):
                    colliding.health -= 25; self.last_attack = time.time()
        else:
            self.state = "WALKING"; self.x -= self.base_speed * speed_mod

    def draw(self, surface):
        super().draw(surface)
        cx, cy = int(self.x), int(self.y)
        if not self.has_jumped:
            pygame.draw.line(surface, (150, 100, 50), (cx-30, cy-10), (cx+40, cy+10), 4)

class FootballZombie(Zombie):
    def __init__(self, row):
        super().__init__(row)
        self.health = 1600 
        self.base_speed = 0.4
        
    def draw_headgear(self, surface, cx, cy):
        pygame.draw.ellipse(surface, (200, 40, 40), (cx-22, cy-65, 44, 35))
        pygame.draw.rect(surface, (200, 40, 40), (cx-22, cy-50, 44, 20))
        pygame.draw.line(surface, (255, 255, 255), (cx-25, cy-35), (cx+5, cy-35), 3)
        pygame.draw.line(surface, (255, 255, 255), (cx-25, cy-45), (cx-15, cy-35), 3)
        pygame.draw.ellipse(surface, (255, 255, 255), (cx-25, cy-25, 20, 15))
        pygame.draw.ellipse(surface, (255, 255, 255), (cx+5, cy-25, 20, 15))

class DragonZombie(Zombie):
    def __init__(self, row):
        super().__init__(row)
        self.health = 500  
        self.base_speed = 0.22
        self.untargetable = False
        self.state = "INITIAL"
        self.state_timer = time.time()
        self.is_eating_plant = False
        
    def update(self, plants, particles=None):
        if time.time() - getattr(self, 'freeze_time', 0) < 4.0:
            self.state_timer += (time.time() - getattr(self, 'last_update_time', time.time()))
            self.last_update_time = time.time()
            return
        if time.time() - getattr(self, 'stun_time', 0) < 3.0:
            self.state_timer += (time.time() - getattr(self, 'last_update_time', time.time()))
            self.last_update_time = time.time()
            return

        speed_mod = 0.5 if (time.time() - self.chill_time < 3.0) else 1.0
        t = time.time()
        dt = t - self.state_timer
        
        my_rect = pygame.Rect(self.x - 40, self.y - 40, 80, 80)
        colliding = next((p for p in plants if p.row == self.row and not isinstance(p, Spikeweed) and my_rect.colliderect(pygame.Rect(p.cx-30, p.cy-30, 60, 60))), None)

        if self.state == "INITIAL":
            self.untargetable = False
            if colliding:
                self.is_eating_plant = True
                if time.time() - getattr(self, 'last_attack', 0) > (1.0 / speed_mod):
                    colliding.health -= 25
                    self.last_attack = time.time()
            else:
                self.is_eating_plant = False
                self.x -= self.base_speed * speed_mod
                
            if dt > 3.0:
                self.state = "BLURRED"
                self.untargetable = True
                self.is_eating_plant = False
                self.state_timer = t
                
        elif self.state == "BLURRED":
            self.untargetable = True
            self.x -= (self.base_speed * 0.35) * speed_mod
            if dt > 2.0:
                self.state = "SOLID"
                self.untargetable = False
                self.state_timer = t
                self.last_attack = 0 
                
        elif self.state == "SOLID":
            self.untargetable = False 
            if colliding:
                self.is_eating_plant = True
                if time.time() - getattr(self, 'last_attack', 0) > (1.0 / speed_mod):
                    colliding.health -= 25
                    self.last_attack = time.time()
            else:
                self.is_eating_plant = False
                self.x -= self.base_speed * speed_mod
                
            if dt > 1.0: 
                self.state = "BLURRED"
                self.untargetable = True
                self.state_timer = t
                self.is_eating_plant = False
                
        self.last_update_time = time.time()

    def draw(self, surface):
        cx, cy = int(self.x), int(self.y)
        t = time.time() - self.birth
        
        is_chilled, is_flashing = (time.time() - self.chill_time < 3.0) or getattr(self, 'state', '') == "FROZEN", (time.time() - self.flash_time < 0.1)
        
        c_skin = (180, 70, 40)   
        c_belly = (220, 180, 100) 
        c_wing = (200, 100, 40)  
        c_spike = (240, 220, 180) 

        if self.state == "BLURRED":
            c_skin = (230, 160, 130)
            c_belly = (250, 230, 190)
            c_wing = (240, 180, 130)
            c_spike = (255, 250, 230)
        
        if is_chilled: 
            c_skin = (100, 100, 180)
            c_belly = (140, 140, 200)
            c_wing = (120, 120, 200)
        if is_flashing: 
            c_skin = c_wing = c_belly = c_spike = (255, 255, 255)

        flap = math.sin(t * 5) * 10 
            
        bw_root = (cx + 5, cy - 10)
        bw_mid = (cx + 40, cy - 70 + flap)
        bw_tip1 = (cx + 90, cy - 30 + flap//2)
        bw_tip2 = (cx + 50, cy - 5 + flap//3)
        pygame.draw.polygon(surface, shade(c_wing, -40), [bw_root, bw_mid, bw_tip1, bw_tip2])
        
        tail_base = (cx + 40, cy)
        tail_mid = (cx + 80, cy + 10 + math.sin(t*4)*8)
        tail_tip = (cx + 120, cy - 15 + math.sin(t*4-1)*15)
        pygame.draw.line(surface, shade(c_skin, -20), tail_base, tail_mid, 12)
        pygame.draw.line(surface, shade(c_skin, -20), tail_mid, tail_tip, 6)
        pygame.draw.polygon(surface, c_spike, [tail_tip, (tail_tip[0]+15, tail_tip[1]-10), (tail_tip[0]+12, tail_tip[1]+10)])
        
        draw_sphere(surface, c_skin, cx, cy, 30, scale_x=1.8, scale_y=0.6)
        pygame.draw.ellipse(surface, c_belly, (cx - 35, cy + 4, 70, 12))
        
        leg_swing = math.sin(t * 10) * 10 if self.state != "BLURRED" and not getattr(self, 'is_eating_plant', False) else 0
        draw_3d_rect(surface, shade(c_skin, -20), pygame.Rect(cx-20+leg_swing, cy+10, 10, 25), 4) 
        draw_3d_rect(surface, shade(c_skin, -30), pygame.Rect(cx+20-leg_swing, cy+10, 10, 25), 4) 

        fw_root = (cx - 10, cy - 10)
        fw_mid = (cx + 50, cy - 85 + flap)
        fw_tip1 = (cx + 110, cy - 40 + flap//2)
        fw_tip2 = (cx + 60, cy - 5 + flap//3)
        pygame.draw.polygon(surface, c_wing, [fw_root, fw_mid, fw_tip1, fw_tip2])
        pygame.draw.line(surface, shade(c_skin, -20), fw_root, fw_mid, 5)
        pygame.draw.line(surface, shade(c_skin, -20), fw_mid, fw_tip1, 3)
        pygame.draw.line(surface, shade(c_skin, -20), fw_mid, fw_tip2, 3)
        
        neck_x, neck_y = cx - 40, cy - 5
        head_x, head_y = cx - 60, cy - 40
        pygame.draw.polygon(surface, c_skin, [(neck_x, neck_y+10), (neck_x+10, neck_y-5), (head_x+15, head_y+5), (head_x+5, head_y+15)])
        
        for i in range(4):
            sx = cx - i*15
            sy = cy - 18 + (i*2)
            pygame.draw.polygon(surface, c_spike, [(sx, sy), (sx+6, sy), (sx+3, sy-10)])
            
        is_biting = getattr(self, 'is_eating_plant', False)
        jaw_drop = 15 if is_biting else 0
        
        draw_3d_rect(surface, c_skin, pygame.Rect(head_x-20, head_y-10, 35, 20), 6)
        draw_3d_rect(surface, c_skin, pygame.Rect(head_x-35, head_y-5, 20, 12), 4)
        draw_3d_rect(surface, shade(c_skin, -20), pygame.Rect(head_x-30, head_y+5+jaw_drop, 30, 8), 3)
        
        if is_biting:
            pygame.draw.polygon(surface, (255,255,255), [(head_x-25, head_y+7), (head_x-20, head_y+15), (head_x-15, head_y+7)])
            pygame.draw.polygon(surface, (255,255,255), [(head_x-15, head_y+7), (head_x-10, head_y+15), (head_x-5, head_y+7)])
            pygame.draw.polygon(surface, (255,255,255), [(head_x-5, head_y+7), (head_x, head_y+15), (head_x+5, head_y+7)])
            
        pygame.draw.polygon(surface, shade(c_spike, -30), [(head_x-5, head_y-10), (head_x+5, head_y-5), (head_x+10, head_y-25)])
        pygame.draw.polygon(surface, c_spike, [(head_x+5, head_y-10), (head_x+15, head_y-5), (head_x+25, head_y-35)]) 
        
        pygame.draw.circle(surface, (255, 220, 0), (head_x-8, head_y-2), 4)
        pygame.draw.ellipse(surface, (0, 0, 0), (head_x-9, head_y-5, 2, 6))
        pygame.draw.line(surface, (0, 0, 0), (head_x-15, head_y-6), (head_x-2, head_y-3), 2)
        pygame.draw.circle(surface, (0, 0, 0), (head_x-28, head_y), 2)

        if getattr(self, 'state', '') == "FROZEN":
            s = pygame.Surface((180, 160), pygame.SRCALPHA)
            pygame.draw.rect(s, (100, 200, 255, 120), (0, 0, 180, 160), border_radius=10)
            pygame.draw.rect(s, (200, 255, 255, 200), (0, 0, 180, 160), 3, border_radius=10)
            surface.blit(s, (cx - 90, cy - 90))

if __name__ == "__main__":
    game = GameEngine()
    asyncio.run(game.run())