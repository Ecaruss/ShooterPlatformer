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
    def __init__(self, platforms, start_platform):
        self.rect = pygame.Rect(0, 0, 40, 40)
        # Начинаем на самой нижней платформе
        self.start_pos = start_platform.midtop[0] - 20, start_platform.midtop[1] - 40
        self.rect.midbottom = start_platform.midtop
        self.vel_y = 0
        self.speed = 2.5  # Уменьшена скорость в 2 раза
        self.jump_power = -15
        self.gravity = 0.8
        self.on_ground = True
        self.platforms = platforms  # Список всех платформ
        self.main_platform = start_platform  # Основная платформа

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
        # Сохраняем начальное значение on_ground перед перемещением
        was_on_ground = self.on_ground
        self.on_ground = False
        
        # Применяем гравитацию
        self.vel_y += self.gravity
        self.rect.y += self.vel_y

        # Проверяем столкновения по оси Y (сверху или снизу)
        for platform in self.platforms:
            if self.rect.colliderect(platform):
                # Если двигаемся вниз (падаем) и сталкиваемся сверху платформы
                if self.vel_y > 0 and self.rect.bottom >= platform.top and self.rect.top < platform.top:
                    # Проверяем, что игрок действительно находится над платформой по горизонтали
                    if self.rect.right > platform.left and self.rect.left < platform.right:
                        self.rect.bottom = platform.top
                        self.vel_y = 0
                        self.on_ground = True
                # Если двигаемся вверх (прыгаем) и сталкиваемся снизу платформы
                elif self.vel_y < 0 and self.rect.top <= platform.bottom and self.rect.bottom > platform.bottom:
                    # Проверяем, что игрок действительно находится под платформой по горизонтали
                    if self.rect.right > platform.left and self.rect.left < platform.right:
                        self.rect.top = platform.bottom
                        self.vel_y = 0

        # Сохраняем позицию до горизонтального движения
        original_x = self.rect.x
        
        # Применяем горизонтальное движение с проверкой коллизий
        keys = pygame.key.get_pressed()
        horizontal_move = 0
        if keys[pygame.K_a]:
            horizontal_move = -self.speed
        elif keys[pygame.K_d]:
            horizontal_move = self.speed
        
        # Применяем горизонтальное движение
        self.rect.x += horizontal_move
        
        # Проверяем столкновения по оси X
        for platform in self.platforms:
            if self.rect.colliderect(platform):
                # Если двигаемся вправо и сталкиваемся с левой стороны платформы
                if horizontal_move > 0 and self.rect.right > platform.left and self.rect.left < platform.left:
                    self.rect.right = platform.left
                # Если двигаемся влево и сталкиваемся с правой стороны платформы
                elif horizontal_move < 0 and self.rect.left < platform.right and self.rect.right > platform.right:
                    self.rect.left = platform.right

        # После горизонтального движения проверяем, остаемся ли мы на платформе
        if was_on_ground and self.on_ground:
            # Проверяем, не сошли ли мы с платформы
            standing_on_platform = False
            for platform in self.platforms:
                if (self.rect.bottom == platform.top and 
                    self.rect.right > platform.left and 
                    self.rect.left < platform.right):
                    standing_on_platform = True
                    break
            if not standing_on_platform:
                self.on_ground = False

    def reset_if_fallen(self):
        """Возвращает игрока в начальную позицию, если он упал ниже основной платформы"""
        if self.rect.top > self.main_platform.bottom:
            self.rect.topleft = self.start_pos
            self.vel_y = 0
            self.on_ground = False  # Установим на false, чтобы игрок не считался находящимся на земле сразу после телепортации

    def draw(self, surface):
        adjusted_rect = apply_camera(self.rect)
        pygame.draw.rect(surface, COLOR_PLAYER, adjusted_rect)

def create_level():
    """Создает уровень с основной платформой и дополнительными платформами"""
    # Основная платформа (пол) - уровень 0
    main_platform_width = SCREEN_WIDTH * 6  # Расширена в 6 раз
    main_platform_height = 50 * 10         # Расширена в 10 раз
    main_platform = pygame.Rect(-main_platform_width//2, SCREEN_HEIGHT - 50, main_platform_width, main_platform_height)
    
    # Высокие бортики по краям основной платформы
    wall_height = 600  # Увеличенная высота бортиков
    left_wall = pygame.Rect(main_platform.left, main_platform.top - wall_height, 20, wall_height)
    right_wall = pygame.Rect(main_platform.right - 20, main_platform.top - wall_height, 20, wall_height)
    
    # Дополнительные платформы
    platforms = [main_platform, left_wall, right_wall]
    
    # Параметры для уровней платформ
    level_heights = [120, 240, 360]  # Высоты уровней 1, 2 и 3
    platform_thickness = 15
    gap_size = 100  # Размер пропусков в платформах
    
    for level_idx, height in enumerate(level_heights):
        # Платформа уровня (расширенная до границ)
        level_platform = pygame.Rect(
            main_platform.left, 
            SCREEN_HEIGHT - 50 - height, 
            main_platform_width, 
            platform_thickness
        )
        
        # Добавляем пропуски в платформе в зависимости от уровня
        # Уровень 1: пропуск посередине
        # Уровень 2: пропуск слева
        # Уровень 3: пропуск справа
        if level_idx == 0:  # Уровень 1 - пропуск посередине
            # Левая часть платформы
            left_part = pygame.Rect(
                level_platform.left, 
                level_platform.top, 
                (level_platform.width // 2) - (gap_size // 2), 
                platform_thickness
            )
            # Правая часть платформы
            right_part = pygame.Rect(
                level_platform.left + (level_platform.width // 2) + (gap_size // 2), 
                level_platform.top, 
                (level_platform.width // 2) - (gap_size // 2), 
                platform_thickness
            )
            platforms.extend([left_part, right_part])
            
        elif level_idx == 1:  # Уровень 2 - пропуск слева
            # Правая часть платформы
            right_part = pygame.Rect(
                level_platform.left + gap_size, 
                level_platform.top, 
                level_platform.width - gap_size, 
                platform_thickness
            )
            platforms.append(right_part)
            
        elif level_idx == 2:  # Уровень 3 - пропуск справа
            # Левая часть платформы
            left_part = pygame.Rect(
                level_platform.left, 
                level_platform.top, 
                level_platform.width - gap_size, 
                platform_thickness
            )
            platforms.append(left_part)
    
    return platforms, main_platform

def main():
    # Создание уровня
    platforms, main_platform = create_level()
    
    # Создание игрока с передачей всех платформ
    player = Player(platforms, main_platform)
    lasers = []
    # Создаем несколько врагов в разных позициях
    enemies = [
        Enemy(platforms[0].centerx + 100, platforms[0].top - 40),
        Enemy(platforms[0].centerx + 300, platforms[0].top - 40),
        Enemy(platforms[0].centerx + 500, platforms[0].top - 40),
        Enemy(SCREEN_WIDTH + 100, platforms[0].top - 40)
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

        # Проверяем, не упал ли игрок за пределы уровня
        player.reset_if_fallen()

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
        for platform in platforms:
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