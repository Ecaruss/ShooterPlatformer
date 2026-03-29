import pygame
import math
import sys
import random

# --- ИНИЦИАЛИЗАЦИЯ ---
pygame.init()

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

screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Pygame-ce Platformer Shooter")
clock = pygame.time.Clock()
font = pygame.font.SysFont("Arial", 28, bold=True)

# Переменная камеры
camera_offset = pygame.Vector2(0, 0)

def update_camera(player_pos):
    """Плавное следование камеры за игроком"""
    global camera_offset
    pos = pygame.Vector2(player_pos)
    target_x = -pos.x + SCREEN_WIDTH // 2
    target_y = -pos.y + SCREEN_HEIGHT // 2
    camera_offset.x += (target_x - camera_offset.x) * 0.1
    camera_offset.y += (target_y - camera_offset.y) * 0.1

def apply_camera(rect):
    """Превращает мировые координаты в экранные для отрисовки"""
    return pygame.Rect(rect.x + camera_offset.x, rect.y + camera_offset.y, rect.width, rect.height)

# --- КЛАССЫ ОБЪЕКТОВ ---

class Laser:
    def __init__(self, x, y, target_x, target_y):
        self.pos = pygame.Vector2(x, y)
        direction = pygame.Vector2(target_x, target_y) - self.pos
        if direction.length() > 0:
            self.velocity = direction.normalize() * 18
        else:
            self.velocity = pygame.Vector2(18, 0)
        self.rect = pygame.Rect(0, 0, 12, 4)
        self.distance = 0

    def update(self):
        self.pos += self.velocity
        self.rect.center = self.pos
        self.distance += self.velocity.length()

    def draw(self, surface):
        pygame.draw.rect(surface, COLOR_LASER, apply_camera(self.rect))

class Gear:
    def __init__(self, x, y):
        self.rect = pygame.Rect(x - 10, y - 10, 20, 20)

    def draw(self, surface):
        draw_rect = apply_camera(self.rect)
        pygame.draw.circle(surface, COLOR_GEAR, draw_rect.center, 10)


class Enemy:
    def __init__(self, x, y, platforms):
        self.rect = pygame.Rect(x, y, 36, 36)
        self.platforms = platforms
        self.vel_y = 0
        self.speed = 3 # Враги чуть медленнее игрока
        self.jump_power = -15
        self.gravity = 0.7
        self.on_ground = False
        
    def apply_physics(self):
        # Гравитация
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

    def ai_logic(self, player_rect):
        dx = 0
        dist_x = player_rect.centerx - self.rect.centerx
        dist_y = player_rect.centery - self.rect.centery

        # 1. Движение по горизонтали
        if abs(dist_x) > 10:
            dx = self.speed if dist_x > 0 else -self.speed

        # 2. Логика прыжка
        # Прыгаем если: 
        # - Игрок выше нас
        # - Перед нами стена (коллизия по X)
        # - Мы подошли к краю платформы, а игрок далеко впереди
        should_jump = False
        
        # Проверка препятствия перед собой
        temp_rect = self.rect.copy()
        temp_rect.x += dx * 5
        for p in self.platforms:
            if temp_rect.colliderect(p) and p.top < self.rect.bottom:
                should_jump = True

        # Прыжок если цель выше
        if dist_y < -50 and self.on_ground:
            should_jump = True

        if should_jump and self.on_ground:
            self.vel_y = self.jump_power
            self.on_ground = False

        # Горизонтальная коллизия
        self.rect.x += dx
        for p in self.platforms:
            if self.rect.colliderect(p):
                if dx > 0: self.rect.right = p.left
                if dx < 0: self.rect.left = p.right

    def update(self, player_rect):
        self.apply_physics()
        self.ai_logic(player_rect)

    def draw(self, surface):
        pygame.draw.rect(surface, COLOR_ENEMY, apply_camera(self.rect))

class Player:
    def __init__(self, platforms):
        self.rect = pygame.Rect(0, 0, 36, 36)
        # Точка спавна: x=0 (центр), y=460 (чуть выше пола, который на 500)
        self.start_pos = pygame.Vector2(0, 460) 
        self.platforms = platforms
        self.vel_y = 0
        self.speed = 6 # Немного увеличил скорость для широкого уровня
        self.jump_power = -16
        self.gravity = 0.7
        self.on_ground = False
        
        self.reset_to_start()

    def move(self):
        keys = pygame.key.get_pressed()
        dx = 0
        if keys[pygame.K_a]: dx -= self.speed
        if keys[pygame.K_d]: dx += self.speed
        
        self.rect.x += dx
        for p in self.platforms:
            if self.rect.colliderect(p):
                if dx > 0: self.rect.right = p.left
                if dx < 0: self.rect.left = p.right

        if keys[pygame.K_w] and self.on_ground:
            self.vel_y = self.jump_power
            self.on_ground = False

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

    def reset_to_start(self):
        """Возвращает игрока на пол в центр"""
        self.rect.midbottom = (self.start_pos.x, self.start_pos.y)
        self.vel_y = 0
        self.on_ground = False

    def reset_if_fallen(self):
        """Респаун, если игрок улетел ниже пола"""
        if self.rect.top > 700: # Глубина падения
            self.reset_to_start()

    def draw(self, surface):
        pygame.draw.rect(surface, COLOR_PLAYER, apply_camera(self.rect))

# --- ГЕНЕРАЦИЯ УРОВНЯ ПО СХЕМЕ image_65a14c.png ---

# --- ГЕНЕРАЦИЯ УРОВНЯ ПО СХЕМЕ image_65a14c.png (СТРОГО) ---

def create_level():
    platforms = []
    
    # 1. ОСНОВАНИЕ (Пол)
    ground_y = 500
    base_w = 1800 
    p_ground = pygame.Rect(-base_w//2, ground_y, base_w, 20)
    platforms.append(p_ground)
    
    # 2. БОКОВЫЕ ГРАНИЦЫ (Стены)
    # Оставим высоту стен 1600, чтобы мир был ограничен
    wall_h = 1600 
    platforms.append(pygame.Rect(-base_w//2 - 20, ground_y - wall_h, 20, wall_h + 20)) # Левая
    platforms.append(pygame.Rect(base_w//2, ground_y - wall_h, 20, wall_h + 20))      # Правая
    
    # 3. ПАРАМЕТРЫ ПЛАТФОРМ
    tier_dist = 160  # Расстояние между этажами
    p_thick = 20     # Толщина платформ
    
    # --- 1-й ЯРУС (Две платформы, дыра в центре) ---
    y1 = ground_y - tier_dist
    p_width_t1 = 600 
    gap_center = 200 
    platforms.append(pygame.Rect(-gap_center//2 - p_width_t1, y1, p_width_t1, p_thick))
    platforms.append(pygame.Rect(gap_center//2, y1, p_width_t1, p_thick))

    # --- 2-й ЯРУС (Центральная + боковые мини-платформы) ---
    y2 = ground_y - (tier_dist * 2)
    p_width_t2_center = 1000 
    platforms.append(pygame.Rect(-p_width_t2_center//2, y2, p_width_t2_center, p_thick))
    
    side_mini_w = 250 
    platforms.append(pygame.Rect(-base_w//2, y2, side_mini_w, p_thick))
    platforms.append(pygame.Rect(base_w//2 - side_mini_w, y2, side_mini_w, p_thick))
    
    # --- 3-й ЯРУС (Снова дыра в центре) ---
    y3 = ground_y - (tier_dist * 3)
    platforms.append(pygame.Rect(-gap_center//2 - p_width_t1, y3, p_width_t1, p_thick))
    platforms.append(pygame.Rect(gap_center//2, y3, p_width_t1, p_thick))

    # --- 4-й ЯРУС (НОВЫЙ, ПАРЯЩИЙ ОСТРОВОК) ---
    y4 = ground_y - (tier_dist * 4)
    p_width_t4_center = 400 # Маленькая парящая платформа
    
    # Монолитная платформа ровно по центру над спавном (x=0)
    # Она не касается боковых стен, так как её ширина всего 400
    platforms.append(pygame.Rect(-p_width_t4_center//2, y4, p_width_t4_center, p_thick))

    return platforms

# --- ОСНОВНОЙ ЦИКЛ ---

def main():
    platforms = create_level()
    player = Player(platforms) # Спавн x=0 над полом
    
    lasers = []
    enemies = []
    gears = []
    score = 0
    spawn_timer = 0
    
    running = True
    while running:
        screen.fill(COLOR_BG)
        mouse_pos = pygame.mouse.get_pos()
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                world_m_x = mouse_pos[0] - camera_offset.x
                world_m_y = mouse_pos[1] - camera_offset.y
                lasers.append(Laser(player.rect.centerx, player.rect.centery, world_m_x, world_m_y))

        # Обновление
        player.move()
        player.reset_if_fallen()
        update_camera(player.rect.center)
        
        for e in enemies:
            e.update(player.rect)

        # Логика лазеров (обновленный блок)
        for l in lasers[:]:
            l.update()
            hit_something = False
            
            # Попадание в стены
            for plat in platforms:
                if l.rect.colliderect(plat):
                    if l in lasers: lasers.remove(l)
                    hit_something = True
                    break
            if hit_something: continue

            # Попадание во врагов
            for e in enemies[:]:
                if l.rect.colliderect(e.rect):
                    gears.append(Gear(e.rect.centerx, e.rect.centery))
                    enemies.remove(e)
                    if l in lasers: lasers.remove(l)
                    break

        # Логика врагов и шестеренок
        for e in enemies: e.update(player.rect)
        for g in gears[:]:
            if player.rect.colliderect(g.rect):
                score += 1
                gears.remove(g)

        # Отрисовка
        for p in platforms: pygame.draw.rect(screen, COLOR_PLATFORM, apply_camera(p))
        for g in gears: g.draw(screen)
        for e in enemies: e.draw(screen)
        for l in lasers: l.draw(screen)
        player.draw(screen)

        # UI
        score_surf = font.render(f"GEARS: {score:03}", True, COLOR_TEXT)
        screen.blit(score_surf, (20, 20))

        pygame.display.flip()
        clock.tick(FPS)

    pygame.quit()

if __name__ == "__main__":
    main()