import pygame
import random
import json
import os

# --- ИНИЦИАЛИЗАЦИЯ ---
pygame.init()

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Константы
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
FPS = 60

# Цвета
COLOR_BG = (15, 15, 15)
COLOR_PLAYER = (0, 120, 255)
COLOR_PLATFORM = (34, 177, 76)
COLOR_ENEMY = (200, 0, 0)
COLOR_LASER = (255, 255, 0)
COLOR_GEAR = (180, 180, 180)
COLOR_TEXT = (255, 255, 255)
COLOR_PORTAL = (138, 43, 226)

SCORES_FILE = os.path.join(BASE_DIR, "highscores.json")
MAX_NAME_LENGTH = 15
MAX_SCORES = 100
TOP_DISPLAY = 10
COUNTDOWN_DURATION = 3000
MAX_ATTEMPTS = 20
BUTTON_WIDTH = 300
BUTTON_HEIGHT = 50
BUTTON_SPACING = 15


class GameState:
    INPUT = "input"
    MENU = "menu"
    COUNTDOWN = "countdown"
    PLAYING = "playing"
    GAMEOVER = "gameover"
    HISTORY = "history"
    HELP = "help"

screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Pygame-ce Platformer Shooter")
clock = pygame.time.Clock()
font = pygame.font.SysFont("Arial", 24, bold=True)

camera_offset = pygame.Vector2(0, 0)

def update_camera(player_pos):
    global camera_offset
    pos = pygame.Vector2(player_pos)
    target_x = -pos.x + SCREEN_WIDTH // 2
    target_y = -pos.y + SCREEN_HEIGHT // 2
    camera_offset.x += (target_x - camera_offset.x) * 0.1
    camera_offset.y += (target_y - camera_offset.y) * 0.1

def apply_camera(rect):
    return pygame.Rect(rect.x + camera_offset.x, rect.y + camera_offset.y, rect.width, rect.height)


def format_time(ms: int) -> str:
    minutes = ms // 60000
    seconds = (ms % 60000) // 1000
    millis = (ms % 1000) // 10
    return f"{minutes:02d}:{seconds:02d}.{millis:02d}"


def load_high_scores() -> list:
    if not os.path.exists(SCORES_FILE):
        return []
    try:
        with open(SCORES_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
            return data.get('scores', [])
    except (json.JSONDecodeError, IOError):
        return []


def get_player_place(scores: list, time_ms: int) -> int:
    place = 1
    for s in scores:
        if time_ms < s['time_ms']:
            break
        place += 1
    return place


def add_high_score(name: str, time_ms: int, score: int) -> tuple:
    try:
        scores = load_high_scores()
        
        existing_idx = None
        for i, s in enumerate(scores):
            if s['name'] == name:
                existing_idx = i
                break
        
        if existing_idx is not None:
            if time_ms >= scores[existing_idx]['time_ms']:
                scores.sort(key=lambda x: x['time_ms'])
                place = get_player_place(scores, time_ms)
                return place, False
            else:
                scores[existing_idx] = {'name': name, 'time_ms': time_ms, 'score': score}
                was_updated = True
        else:
            scores.append({'name': name, 'time_ms': time_ms, 'score': score})
            was_updated = True
        
        scores.sort(key=lambda x: x['time_ms'])
        scores = scores[:MAX_SCORES]
        
        with open(SCORES_FILE, 'w', encoding='utf-8') as f:
            json.dump({'scores': scores}, f, indent=2)
        print(f"DEBUG: Saved high score to {SCORES_FILE}", flush=True)
        
        place = get_player_place(scores, time_ms)
        return place, was_updated
    except Exception as e:
        print(f"ERROR saving high score: {e}", flush=True)
        return 0, False


def get_attempts_filename(name: str) -> str:
    return os.path.join(BASE_DIR, f"attempts_{name}.json")


def load_attempts(player_name: str) -> list:
    filename = get_attempts_filename(player_name)
    if not os.path.exists(filename):
        return []
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return []


def save_attempt(player_name: str, time_ms: int, score: int):
    try:
        attempts = load_attempts(player_name)
        attempts.append({
            'time_ms': time_ms,
            'score': score
        })
        if len(attempts) > MAX_ATTEMPTS:
            attempts = attempts[-MAX_ATTEMPTS:]
        with open(get_attempts_filename(player_name), 'w', encoding='utf-8') as f:
            json.dump(attempts, f)
        print(f"DEBUG: Saved attempt to {get_attempts_filename(player_name)}", flush=True)
    except Exception as e:
        print(f"ERROR saving attempt: {e}", flush=True)


# --- ПОИСК ПУТИ ---
MAX_JUMP_HEIGHT = 180


class PlatformNode:
    def __init__(self, rect):
        self.rect = rect
        self.jump_targets = []
        self.fall_targets = []


def can_jump_to(from_rect, to_rect):
    if to_rect.top >= from_rect.top:
        return False
    if not (from_rect.right > to_rect.left + 10 and from_rect.left < to_rect.right - 10):
        return False
    if from_rect.top - to_rect.top > MAX_JUMP_HEIGHT:
        return False
    return True


def can_fall_to(from_rect, to_rect):
    if to_rect.top <= from_rect.top:
        return False
    if not (from_rect.right > to_rect.left + 10 and from_rect.left < to_rect.right - 10):
        return False
    return True


def build_platform_graph(platforms):
    nodes = [PlatformNode(p) for p in platforms]
    
    for node in nodes:
        for other in nodes:
            if other == node:
                continue
            if can_jump_to(node.rect, other.rect):
                node.jump_targets.append(other)
            if can_fall_to(node.rect, other.rect):
                node.fall_targets.append(other)
    
    return nodes


def find_path(start_node, target_node, nodes):
    from collections import deque
    
    queue = deque([start_node])
    visited = {start_node}
    parent = {start_node: None}
    
    while queue:
        current = queue.popleft()
        
        if current == target_node:
            path = []
            while current:
                path.append(current)
                current = parent[current]
            return path[::-1]
        
        for neighbor in current.jump_targets + current.fall_targets:
            if neighbor not in visited:
                visited.add(neighbor)
                parent[neighbor] = current
                queue.append(neighbor)
    
    return None


# --- КЛАССЫ ОБЪЕКТОВ ---

class Laser:
    def __init__(self, x, y, target_x, target_y):
        self.pos = pygame.Vector2(x, y)
        direction = pygame.Vector2(target_x, target_y) - self.pos
        self.velocity = direction.normalize() * 15 if direction.length() > 0 else pygame.Vector2(15, 0)
        self.rect = pygame.Rect(0, 0, 8, 8)
        self.distance = 0

    def update(self):
        self.pos += self.velocity
        self.rect.center = self.pos
        self.distance += self.velocity.length()

    def draw(self, surface):
        pygame.draw.circle(surface, COLOR_LASER, apply_camera(self.rect).center, 4)

class Enemy:
    def __init__(self, x, y, platforms, platform_graph=None):
        self.rect = pygame.Rect(x, y, 32, 32)
        self.platforms = platforms
        self.platform_graph = platform_graph
        self.vel_y = 0
        self.speed = 2.2
        self.jump_power = -14
        self.gravity = 0.6
        self.on_ground = False
        self.move_dir = 1
        self.path = []
        self.path_timer = 0

    def apply_physics(self):
        self.vel_y += self.gravity
        self.rect.y += self.vel_y
        self.on_ground = False
        for p in self.platforms:
            if self.rect.colliderect(p):
                if self.vel_y > 0:
                    self.rect.bottom = p.top
                    self.vel_y = 0
                    self.on_ground = True
                elif self.vel_y < 0:
                    self.rect.top = p.bottom
                    self.vel_y = 0

    def find_current_platform(self):
        if not self.platform_graph:
            return None
        for node in self.platform_graph:
            if (self.rect.bottom >= node.rect.top - 5 and 
                self.rect.bottom <= node.rect.top + 15 and
                node.rect.left <= self.rect.centerx <= node.rect.right):
                return node
        return None

    def find_player_platform(self, player_rect):
        if not self.platform_graph:
            return None
        for node in self.platform_graph:
            if (player_rect.bottom >= node.rect.top - 5 and 
                player_rect.bottom <= node.rect.top + 15 and
                node.rect.left <= player_rect.centerx <= node.rect.right):
                return node
        return None

    def check_at_edge(self, direction):
        sensor_x = self.rect.right + 5 if direction > 0 else self.rect.left - 5
        sensor_rect = pygame.Rect(sensor_x, self.rect.bottom + 2, 10, 10)
        
        for p in self.platforms:
            if sensor_rect.colliderect(p):
                return False
        return True

    def ai_logic(self, player_rect):
        if not self.platform_graph:
            self.simple_ai(player_rect)
            return

        self.path_timer += 1
        if self.path_timer >= 30:
            self.path_timer = 0
            current_node = self.find_current_platform()
            target_node = self.find_player_platform(player_rect)
            
            if current_node and target_node and current_node != target_node:
                self.path = find_path(current_node, target_node, self.platform_graph) or []
            else:
                self.path = []

        if self.path and len(self.path) > 1:
            self.follow_path(player_rect)
        else:
            self.simple_ai(player_rect)

    def follow_path(self, player_rect):
        if len(self.path) < 2:
            return
        
        next_node = self.path[1]
        
        if next_node.rect.centerx > self.rect.centerx:
            move_dir = 1
        else:
            move_dir = -1
        
        dx = self.speed * move_dir
        
        at_edge = self.check_at_edge(move_dir)
        
        if at_edge and self.on_ground:
            if next_node.rect.top < self.rect.bottom - 20:
                self.vel_y = self.jump_power
        
        self.rect.x += dx
        for p in self.platforms:
            if self.rect.colliderect(p):
                if dx > 0: self.rect.right = p.left
                if dx < 0: self.rect.left = p.right

    def simple_ai(self, player_rect):
        dx = 0
        dist_x = player_rect.centerx - self.rect.centerx
        dist_y = player_rect.centery - self.rect.centery

        if abs(dist_x) > 20:
            dx = self.speed if dist_x > 0 else -self.speed

        if self.on_ground:
            sensor_x = self.rect.right + 5 if dx > 0 else self.rect.left - 5
            sensor_rect = pygame.Rect(sensor_x, self.rect.bottom + 2, 10, 10)
            
            on_edge = True
            for p in self.platforms:
                if sensor_rect.colliderect(p):
                    on_edge = False
                    break
            
            if on_edge:
                if dist_y < -50: self.vel_y = self.jump_power
                elif dist_y > 50: pass
                else: dx = 0

        if self.on_ground and (dist_y < -100 or self.is_stuck(dx)):
            self.vel_y = self.jump_power

        self.rect.x += dx
        for p in self.platforms:
            if self.rect.colliderect(p):
                if dx > 0: self.rect.right = p.left
                if dx < 0: self.rect.left = p.right

    def is_stuck(self, dx):
        temp_rect = self.rect.copy()
        temp_rect.x += dx * 2
        for p in self.platforms:
            if temp_rect.colliderect(p): return True
        return False

    def update(self, player_rect):
        self.apply_physics()
        self.ai_logic(player_rect)

    def draw(self, surface):
        pygame.draw.rect(surface, COLOR_ENEMY, apply_camera(self.rect))

class Portal:
    def __init__(self, x, y, platform_graph=None):
        self.rect = pygame.Rect(x - 30, y - 60, 60, 60)
        self.hp = 10
        self.spawn_timer = 0
        self.platform_graph = platform_graph

    def update(self, enemies, platforms):
        self.spawn_timer += 1
        if self.spawn_timer >= 180:
            enemies.append(Enemy(self.rect.centerx, self.rect.centery, platforms, self.platform_graph))
            self.spawn_timer = 0

    def draw(self, surface):
        pygame.draw.rect(surface, COLOR_PORTAL, apply_camera(self.rect), 4)
        hp_w = (self.hp / 10) * 60
        pygame.draw.rect(surface, (255, 0, 0), apply_camera(pygame.Rect(self.rect.x, self.rect.y - 15, hp_w, 5)))

class Player:
    def __init__(self, platforms):
        self.rect = pygame.Rect(0, 460, 36, 36)
        self.platforms = platforms
        self.vel_y = 0
        self.speed = 6
        self.on_ground = False

    def move(self):
        keys = pygame.key.get_pressed()
        dx = (keys[pygame.K_d] - keys[pygame.K_a]) * self.speed
        self.rect.x += dx
        for p in self.platforms:
            if self.rect.colliderect(p):
                if dx > 0: self.rect.right = p.left
                if dx < 0: self.rect.left = p.right

        if keys[pygame.K_w] and self.on_ground:
            self.vel_y = -16
            self.on_ground = False

        self.vel_y += 0.7
        self.rect.y += self.vel_y
        self.on_ground = False
        for p in self.platforms:
            if self.rect.colliderect(p):
                if self.vel_y > 0:
                    self.rect.bottom = p.top
                    self.vel_y = 0
                    self.on_ground = True
                elif self.vel_y < 0:
                    self.rect.top = p.bottom
                    self.vel_y = 0
        if self.rect.y > 1000: self.rect.topleft = (0, 400)

    def draw(self, surface):
        pygame.draw.rect(surface, COLOR_PLAYER, apply_camera(self.rect))

# --- УРОВЕНЬ ---
def create_level():
    p = []
    bw = 1800
    gy = 500
    p.append(pygame.Rect(-bw//2, gy, bw, 20)) # Пол
    p.append(pygame.Rect(-bw//2-20, gy-1600, 20, 1620)) # Л.Стена
    p.append(pygame.Rect(bw//2, gy-1600, 20, 1620)) # П.Стена
    
    # Платформы
    p.append(pygame.Rect(-700, gy-160, 600, 20)) # 1 ярус л
    p.append(pygame.Rect(100, gy-160, 600, 20)) # 1 ярус п
    
    p.append(pygame.Rect(-500, gy-320, 1000, 20)) # 2 ярус центр
    p.append(pygame.Rect(-bw//2, gy-320, 250, 20)) # 2 ярус мини л
    p.append(pygame.Rect(bw//2-250, gy-320, 250, 20)) # 2 ярус мини п
    
    p.append(pygame.Rect(-700, gy-480, 600, 20)) # 3 ярус л
    p.append(pygame.Rect(100, gy-480, 600, 20)) # 3 ярус п
    
    p.append(pygame.Rect(-200, gy-640, 400, 20)) # 4 ярус (остров)
    return p

# --- MAIN ---
def reset_level():
    platforms = create_level()
    player = Player(platforms)
    portals = [Portal(0, -140), Portal(-850, 180), Portal(850, 180)]
    enemies, lasers = [], []
    score = 0
    won = False
    return platforms, player, portals, enemies, lasers, score, won


def main():
    platforms, player, portals, enemies, lasers, score, won = reset_level()

    game_state = GameState.INPUT
    player_name = ""
    start_time = 0
    countdown_start = 0
    final_time_ms = 0
    player_place = 0
    was_recorded = False

    while True:
        screen.fill(COLOR_BG)
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT: return
            
            if game_state == GameState.INPUT:
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_BACKSPACE:
                        player_name = player_name[:-1]
                    elif event.key == pygame.K_RETURN:
                        if player_name:
                            game_state = GameState.MENU
                    elif len(player_name) < MAX_NAME_LENGTH:
                        player_name += event.unicode
            
            elif game_state == GameState.MENU:
                if event.type == pygame.MOUSEBUTTONDOWN:
                    mx, my = pygame.mouse.get_pos()
                    start_y = 200
                    for i in range(4):
                        btn_rect = pygame.Rect(
                            SCREEN_WIDTH//2 - BUTTON_WIDTH//2,
                            start_y + i * (BUTTON_HEIGHT + BUTTON_SPACING),
                            BUTTON_WIDTH,
                            BUTTON_HEIGHT
                        )
                        if btn_rect.collidepoint(mx, my):
                            if i == 0:  # START GAME
                                platforms, player, portals, enemies, lasers, score, won = reset_level()
                                game_state = GameState.COUNTDOWN
                                countdown_start = pygame.time.get_ticks()
                            elif i == 1:  # HISTORY
                                game_state = GameState.HISTORY
                            elif i == 2:  # CONTROLS
                                game_state = GameState.HELP
                            elif i == 3:  # EXIT
                                pygame.quit()
                                return
            
            elif game_state == GameState.HISTORY or game_state == GameState.HELP:
                if event.type == pygame.MOUSEBUTTONDOWN:
                    mx, my = pygame.mouse.get_pos()
                    back_btn = pygame.Rect(SCREEN_WIDTH//2 - 100, SCREEN_HEIGHT - 80, 200, 50)
                    if back_btn.collidepoint(mx, my):
                        game_state = GameState.MENU
            
            elif game_state == GameState.GAMEOVER:
                if event.type == pygame.MOUSEBUTTONDOWN:
                    mx, my = pygame.mouse.get_pos()
                    restart_btn = pygame.Rect(SCREEN_WIDTH//2 - 220, SCREEN_HEIGHT - 80, 200, 50)
                    menu_btn = pygame.Rect(SCREEN_WIDTH//2 + 20, SCREEN_HEIGHT - 80, 200, 50)
                    if restart_btn.collidepoint(mx, my):
                        platforms, player, portals, enemies, lasers, score, won = reset_level()
                        game_state = GameState.COUNTDOWN
                        countdown_start = pygame.time.get_ticks()
                    elif menu_btn.collidepoint(mx, my):
                        game_state = GameState.MENU
                        won = False
            
            elif game_state == GameState.PLAYING and not won:
                if event.type == pygame.MOUSEBUTTONDOWN:
                    mx, my = pygame.mouse.get_pos()
                    lasers.append(Laser(player.rect.centerx, player.rect.centery, mx-camera_offset.x, my-camera_offset.y))
                if event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE:
                    print("DEBUG: Space pressed - instant win!", flush=True)
                    portals.clear()
                    enemies.clear()
                    print(f"DEBUG: After clear - portals={len(portals)}, enemies={len(enemies)}", flush=True)

        if game_state == GameState.INPUT:
            input_box = pygame.Rect(SCREEN_WIDTH//2 - 150, SCREEN_HEIGHT//2 - 20, 300, 40)
            pygame.draw.rect(screen, COLOR_TEXT, input_box, 2)
            
            title_text = font.render("Enter your name:", True, COLOR_TEXT)
            screen.blit(title_text, (SCREEN_WIDTH//2 - title_text.get_width()//2, SCREEN_HEIGHT//2 - 60))
            
            name_surf = font.render(player_name, True, COLOR_TEXT)
            screen.blit(name_surf, (input_box.x + 10, input_box.y + 8))
            
            if pygame.time.get_ticks() % 1000 < 500:
                cursor_x = input_box.x + 10 + name_surf.get_width()
                pygame.draw.line(screen, COLOR_TEXT, (cursor_x, input_box.y + 5), (cursor_x, input_box.y + 35), 2)
            
            hint_text = font.render("Press ENTER to start", True, (150, 150, 150))
            screen.blit(hint_text, (SCREEN_WIDTH//2 - hint_text.get_width()//2, SCREEN_HEIGHT//2 + 40))

        elif game_state == GameState.MENU:
            title = font.render("PLATFORMER SHOOTER", True, COLOR_TEXT)
            screen.blit(title, (SCREEN_WIDTH//2 - title.get_width()//2, 100))
            
            menu_buttons = [
                ("START GAME", GameState.COUNTDOWN),
                ("HISTORY", GameState.HISTORY),
                ("CONTROLS", GameState.HELP),
                ("EXIT", None)
            ]
            
            menu_rects = []
            start_y = 200
            for i, (text, _) in enumerate(menu_buttons):
                btn_rect = pygame.Rect(
                    SCREEN_WIDTH//2 - BUTTON_WIDTH//2,
                    start_y + i * (BUTTON_HEIGHT + BUTTON_SPACING),
                    BUTTON_WIDTH,
                    BUTTON_HEIGHT
                )
                menu_rects.append((btn_rect, text, _))
                
                pygame.draw.rect(screen, (50, 50, 50), btn_rect)
                pygame.draw.rect(screen, COLOR_TEXT, btn_rect, 2)
                
                text_surf = font.render(text, True, COLOR_TEXT)
                screen.blit(text_surf, (btn_rect.x + BUTTON_WIDTH//2 - text_surf.get_width()//2,
                                       btn_rect.y + BUTTON_HEIGHT//2 - text_surf.get_height()//2))

        elif game_state == GameState.COUNTDOWN:
            for plat in platforms: pygame.draw.rect(screen, COLOR_PLATFORM, apply_camera(plat))
            for p in portals: p.draw(screen)
            for e in enemies: e.draw(screen)
            player.draw(screen)
            
            ready_text = font.render("GET READY!", True, COLOR_TEXT)
            screen.blit(ready_text, (SCREEN_WIDTH//2 - ready_text.get_width()//2, SCREEN_HEIGHT//2 - 150))
            
            elapsed = pygame.time.get_ticks() - countdown_start
            remaining = max(0, (COUNTDOWN_DURATION - elapsed) // 1000 + 1)
            
            countdown_text = font.render(str(remaining), True, (255, 200, 0))
            countdown_text = pygame.transform.scale(countdown_text, (200, 200))
            screen.blit(countdown_text, (SCREEN_WIDTH//2 - 100, SCREEN_HEIGHT//2 - 100))
            
            if elapsed >= COUNTDOWN_DURATION:
                game_state = GameState.PLAYING
                start_time = pygame.time.get_ticks()

        elif game_state == GameState.HISTORY:
            history_title = font.render(f"HISTORY - {player_name}", True, COLOR_TEXT)
            screen.blit(history_title, (SCREEN_WIDTH//2 - history_title.get_width()//2, 30))
            
            attempts = load_attempts(player_name)
            
            if not attempts:
                no_attempts_text = font.render("No attempts yet", True, (150, 150, 150))
                screen.blit(no_attempts_text, (SCREEN_WIDTH//2 - no_attempts_text.get_width()//2, 100))
            else:
                start_y = 70
                for i, attempt in enumerate(attempts):
                    attempt_text = font.render(
                        f"{i+1:02d}. {format_time(attempt['time_ms'])}  Score: {attempt['score']}",
                        True, COLOR_TEXT
                    )
                    screen.blit(attempt_text, (SCREEN_WIDTH//2 - attempt_text.get_width()//2, start_y + i * 28))
            
            back_btn = pygame.Rect(SCREEN_WIDTH//2 - 100, SCREEN_HEIGHT - 80, 200, 50)
            pygame.draw.rect(screen, (50, 50, 50), back_btn)
            pygame.draw.rect(screen, COLOR_TEXT, back_btn, 2)
            back_text = font.render("BACK", True, COLOR_TEXT)
            screen.blit(back_text, (back_btn.x + 100 - back_text.get_width()//2,
                                   back_btn.y + 25 - back_text.get_height()//2))

        elif game_state == GameState.HELP:
            help_title = font.render("CONTROLS", True, COLOR_TEXT)
            screen.blit(help_title, (SCREEN_WIDTH//2 - help_title.get_width()//2, 50))
            
            controls = [
                "W - Jump",
                "A / D - Move Left / Right",
                "Mouse Click - Shoot",
                "",
                "Objective:",
                "Kill all enemies and portals",
                "in minimum time!"
            ]
            
            for i, line in enumerate(controls):
                line_surf = font.render(line, True, COLOR_TEXT)
                screen.blit(line_surf, (SCREEN_WIDTH//2 - line_surf.get_width()//2, 120 + i * 35))
            
            back_btn = pygame.Rect(SCREEN_WIDTH//2 - 100, SCREEN_HEIGHT - 80, 200, 50)
            pygame.draw.rect(screen, (50, 50, 50), back_btn)
            pygame.draw.rect(screen, COLOR_TEXT, back_btn, 2)
            back_text = font.render("BACK", True, COLOR_TEXT)
            screen.blit(back_text, (back_btn.x + 100 - back_text.get_width()//2,
                                   back_btn.y + 25 - back_text.get_height()//2))

        elif game_state == GameState.PLAYING:
            if not won:
                elapsed_time = pygame.time.get_ticks() - start_time
            else:
                elapsed_time = final_time_ms
            
            if not won:
                player.move()
                update_camera(player.rect.center)

                for p in portals[:]:
                    p.update(enemies, platforms)
                    
                for e in enemies: e.update(player.rect)

                for l in lasers[:]:
                    l.update()
                    hit = False
                    for p in portals[:]:
                        if l.rect.colliderect(p.rect):
                            p.hp -= 1
                            if p.hp <= 0: portals.remove(p)
                            hit = True; break
                    if not hit:
                        for plat in platforms:
                            if l.rect.colliderect(plat): hit = True; break
                    if not hit:
                        for e in enemies[:]:
                            if l.rect.colliderect(e.rect):
                                enemies.remove(e); hit = True; score += 1; break
                    if hit or l.distance > 1200: lasers.remove(l)

            import sys
            print(f"DEBUG: portals={len(portals)}, enemies={len(enemies)}, won={won}", flush=True)
            if len(portals) == 0 and len(enemies) == 0 and not won:
                print("DEBUG: WIN CONDITION MET!", flush=True)
                won = True
                final_time_ms = pygame.time.get_ticks() - start_time
                save_attempt(player_name, final_time_ms, score)
                player_place, was_recorded = add_high_score(player_name, final_time_ms, score)
                game_state = GameState.GAMEOVER
                print(f"DEBUG: Game state changed to GAMEOVER", flush=True)

            for plat in platforms: pygame.draw.rect(screen, COLOR_PLATFORM, apply_camera(plat))
            for p in portals: p.draw(screen)
            for e in enemies: e.draw(screen)
            for l in lasers: l.draw(screen)
            player.draw(screen)
            
            screen.blit(font.render(f"GEARS: {score}", True, COLOR_TEXT), (20, 20))
            screen.blit(font.render(format_time(elapsed_time), True, COLOR_TEXT), (20, 50))

        elif game_state == GameState.GAMEOVER:
            for plat in platforms: pygame.draw.rect(screen, COLOR_PLATFORM, apply_camera(plat))
            for p in portals: p.draw(screen)
            for e in enemies: e.draw(screen)
            for l in lasers: l.draw(screen)
            player.draw(screen)
            
            screen.blit(font.render(f"GEARS: {score}", True, COLOR_TEXT), (20, 20))
            screen.blit(font.render(format_time(final_time_ms), True, COLOR_TEXT), (20, 50))
            
            overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 180))
            screen.blit(overlay, (0,0))

            high_scores = load_high_scores()
            
            win_text = font.render("MISSION ACCOMPLISHED", True, (0, 255, 100))
            screen.blit(win_text, (SCREEN_WIDTH//2 - win_text.get_width()//2, 30))
            
            player_info = font.render(f"{player_name}: {format_time(final_time_ms)}", True, COLOR_TEXT)
            screen.blit(player_info, (SCREEN_WIDTH//2 - player_info.get_width()//2, 70))
            
            place_text = font.render(f"Your place: {player_place}", True, (255, 200, 0))
            screen.blit(place_text, (SCREEN_WIDTH//2 - place_text.get_width()//2, 100))
            
            if not was_recorded:
                not_recorded_text = font.render("Not a new record", True, (150, 150, 150))
                screen.blit(not_recorded_text, (SCREEN_WIDTH//2 - not_recorded_text.get_width()//2, 130))
            
            top_y = 180
            top_title = font.render("TOP 10:", True, COLOR_TEXT)
            screen.blit(top_title, (SCREEN_WIDTH//2 - top_title.get_width()//2, top_y))
            
            for i, entry in enumerate(high_scores[:TOP_DISPLAY]):
                entry_text = font.render(f"{i+1:02d}. {entry['name']:<15} {format_time(entry['time_ms'])}", True, COLOR_TEXT)
                screen.blit(entry_text, (SCREEN_WIDTH//2 - entry_text.get_width()//2, top_y + 30 + i * 25))
            
            restart_btn = pygame.Rect(SCREEN_WIDTH//2 - 220, SCREEN_HEIGHT - 80, 200, 50)
            menu_btn = pygame.Rect(SCREEN_WIDTH//2 + 20, SCREEN_HEIGHT - 80, 200, 50)
            
            pygame.draw.rect(screen, (50, 50, 50), restart_btn)
            pygame.draw.rect(screen, COLOR_TEXT, restart_btn, 2)
            restart_text = font.render("RESTART", True, COLOR_TEXT)
            screen.blit(restart_text, (restart_btn.x + 100 - restart_text.get_width()//2,
                                       restart_btn.y + 25 - restart_text.get_height()//2))
            
            pygame.draw.rect(screen, (50, 50, 50), menu_btn)
            pygame.draw.rect(screen, COLOR_TEXT, menu_btn, 2)
            menu_text = font.render("MENU", True, COLOR_TEXT)
            screen.blit(menu_text, (menu_btn.x + 100 - menu_text.get_width()//2,
                                    menu_btn.y + 25 - menu_text.get_height()//2))

        pygame.display.flip()
        clock.tick(FPS)

if __name__ == "__main__": main()