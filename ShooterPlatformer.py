import pygame
import math
import sys

# Инициализация
pygame.init()

# Константы
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
FPS = 60

# Цвета
COLOR_BG = (30, 30, 30)
COLOR_PLAYER = (0, 120, 255)
COLOR_PLATFORM = (34, 177, 76)
COLOR_ENEMY = (200, 0, 0)
COLOR_LASER = (255, 255, 0)
COLOR_GEAR = (160, 160, 160)
COLOR_TEXT = (255, 255, 255)

screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Pygame-ce Platformer Shooter")
clock = pygame.time.Clock()
font = pygame.font.SysFont("Arial", 24)

# Переменная камеры
camera_offset = pygame.Vector2(0, 0)

def update_camera(player_pos):
    """Обновляет смещение камеры, следуя за игроком"""
    global camera_offset
    target_x = -player_pos.x + SCREEN_WIDTH // 2
    target_y = -player_pos.y + SCREEN_HEIGHT // 2
    
    # Плавное движение камеры
    camera_offset.x += (target_x - camera_offset.x) * 0.1
    camera_offset.y += (target_y - camera_offset.y) * 0.1

def apply_camera(rect):
    """Применяет смещение камеры к прямоугольнику"""
    return pygame.Rect(
        rect.x + camera_offset.x,
        rect.y + camera_offset.y,
        rect.width,
        rect.height
    )

class Laser:
    def __init__(self, x, y, target_x, target_y):
        self.pos = pygame.Vector2(x, y)
        direction = pygame.Vector2(target_x, target_y) - self.pos
        if direction.length() > 0:
            self.velocity = direction.normalize() * 15
        else:
            self.velocity = pygame.Vector2(15, 0)
        self.rect = pygame.Rect(0, 0, 10, 4)
        self.distance_traveled = 0
        self.max_distance = 1000

    def update(self):
        self.pos += self.velocity
        self.rect.center = self.pos
        self.distance_traveled += self.velocity.length()

    def draw(self, surface):
        adjusted_rect = apply_camera(self.rect)
        pygame.draw.rect(surface, COLOR_LASER, adjusted_rect)

class Gear:
    def __init__(self, x, y):
        self.rect = pygame.Rect(x - 10, y - 10, 20, 20)

    def draw(self, surface):
        center_x = self.rect.centerx + camera_offset.x
        center_y = self.rect.centery + camera_offset.y
        pygame.draw.circle(surface, COLOR_GEAR, (int(center_x), int(center_y)), 10)

class Enemy:
    def __init__(self, x, y):
        self.rect = pygame.Rect(x, y, 40, 40)
        self.speed = 2

    def update(self, player_rect):
        if self.rect.x > player_rect.x:
            self.rect.x -= self.speed
        elif self.rect.x < player_rect.x:
            self.rect.x += self.speed

    def draw(self, surface):
        adjusted_rect = apply_camera(self.rect)
        pygame.draw.rect(surface, COLOR_ENEMY, adjusted_rect)

class Player:
    def __init__(self, platform_rect):
        self.rect = pygame.Rect(0, 0, 40, 40)
        self.rect.midbottom = platform_rect.midtop
        self.vel_y = 0
        self.speed = 5
        self.jump_power = -15
        self.gravity = 0.8
        self.on_ground = True
        self.platform_y = platform_rect.top

    def handle_input(self, lasers):
        keys = pygame.key.get_pressed()
        if keys[pygame.K_a]:
            self.rect.x -= self.speed
        if keys[pygame.K_d]:
            self.rect.x += self.speed
        if keys[pygame.K_w] and self.on_ground:
            self.vel_y = self.jump_power
            self.on_ground = False

    def apply_gravity(self):
        self.vel_y += self.gravity
        self.rect.y += self.vel_y
        if self.rect.bottom >= self.platform_y:
            self.rect.bottom = self.platform_y
            self.vel_y = 0
            self.on_ground = True

    def draw(self, surface):
        adjusted_rect = apply_camera(self.rect)
        pygame.draw.rect(surface, COLOR_PLAYER, adjusted_rect)

def main():
    # Создание объектов
    platform = pygame.Rect(0, SCREEN_HEIGHT - 50, SCREEN_WIDTH, 50)
    player = Player(platform)
    lasers = []
    # Создаем несколько врагов в разных позициях
    enemies = [
        Enemy(SCREEN_WIDTH + 100, platform.top - 40),
        Enemy(SCREEN_WIDTH + 300, platform.top - 40),
        Enemy(SCREEN_WIDTH + 500, platform.top - 40),
        Enemy(SCREEN_WIDTH + 700, platform.top - 40),
        Enemy(SCREEN_WIDTH + 900, platform.top - 40)
    ]
    gears = []
    score = 0

    running = True
    while running:
        screen.fill(COLOR_BG)
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1: # ЛКМ
                    mx, my = pygame.mouse.get_pos()
                    # Корректируем позицию мыши с учетом камеры
                    corrected_mx = mx - camera_offset.x
                    corrected_my = my - camera_offset.y
                    lasers.append(Laser(player.rect.centerx, player.rect.centery, corrected_mx, corrected_my))

        # Обновление камеры
        update_camera(pygame.Vector2(player.rect.centerx, player.rect.centery))

        # Логика игрока
        player.handle_input(lasers)
        player.apply_gravity()

        # Логика лазеров
        for laser in lasers[:]:
            laser.update()
            if laser.distance_traveled > laser.max_distance:
                lasers.remove(laser)
                continue
            
            # Проверка попадания во врага
            hit = False
            for enemy in enemies[:]:
                if laser.rect.colliderect(enemy.rect):
                    gears.append(Gear(enemy.rect.centerx, enemy.rect.centery))
                    enemies.remove(enemy)
                    score += 1  # Увеличиваем счет при уничтожении врага
                    hit = True
                    break
            if hit:
                lasers.remove(laser)

        # Логика врагов
        for enemy in enemies:
            enemy.update(player.rect)

        # Логика шестеренок
        for gear in gears[:]:
            if player.rect.colliderect(gear.rect):
                score += 1
                gears.remove(gear)

        # Отрисовка
        pygame.draw.rect(screen, COLOR_PLATFORM, apply_camera(platform))
        player.draw(screen)
        for laser in lasers: 
            laser.draw(screen)
        for enemy in enemies: 
            enemy.draw(screen)
        for gear in gears: 
            gear.draw(screen)

        # Интерфейс
        score_text = font.render(f"{score:03}", True, COLOR_TEXT)
        screen.blit(score_text, (20, 20))

        pygame.display.flip()
        clock.tick(FPS)

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()