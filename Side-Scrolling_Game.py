import pygame
import sys

# Screen dimensions and constants
SCREEN_WIDTH, SCREEN_HEIGHT = 900, 480
FPS = 60
GRAVITY = 0.9

pygame.init()
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Animal Hero Side Scroller")
clock = pygame.time.Clock()

def draw_text(surface, text, size, x, y, color=(255,255,255)):
    font = pygame.font.SysFont("arial", size)
    text_surface = font.render(text, True, color)
    surface.blit(text_surface, (x, y))

# Projectile class
class Projectile(pygame.sprite.Sprite):
    def __init__(self, x, y, speed=14, damage=25, direction=1):
        super().__init__()
        self.image = pygame.Surface((10, 4))
        self.image.fill((255, 255, 0))
        self.rect = self.image.get_rect(center=(x, y))
        self.speed = speed * direction
        self.damage = damage

    def update(self):
        self.rect.x += self.speed
        if self.rect.right < -50 or self.rect.left > SCREEN_WIDTH + 50:
            self.kill()

# Player class
class Player(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        self.image = pygame.Surface((40, 60))
        self.image.fill((0, 128, 255))  # Blue animal hero
        self.rect = self.image.get_rect(topleft=(x, y))
        self.speed = 6
        self.vel_y = 0
        self.jump_power = 17
        self.on_ground = False
        self.health = 100
        self.lives = 3
        self.projectiles = pygame.sprite.Group()
        self.shoot_cooldown = 0
        self.facing_right = True

    def handle_input(self, platforms):
        keys = pygame.key.get_pressed()
        dx = 0
        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            dx = -self.speed
            self.facing_right = False
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            dx = self.speed
            self.facing_right = True

        self.rect.x += dx
        self.collide(dx, 0, platforms)

        self.vel_y += GRAVITY
        if self.vel_y > 20:
            self.vel_y = 20
        self.rect.y += self.vel_y
        self.on_ground = False
        self.collide(0, self.vel_y, platforms)

        if self.shoot_cooldown > 0:
            self.shoot_cooldown -= 1

        if keys[pygame.K_f] and self.shoot_cooldown == 0:
            self.shoot()
            self.shoot_cooldown = 20

        self.projectiles.update()

    def jump(self):
        if self.on_ground:
            self.vel_y = -self.jump_power
            self.on_ground = False

    def collide(self, dx, dy, platforms):
        for platform in platforms:
            if self.rect.colliderect(platform.rect):
                if dx > 0:
                    self.rect.right = platform.rect.left
                if dx < 0:
                    self.rect.left = platform.rect.right
                if dy > 0:
                    self.rect.bottom = platform.rect.top
                    self.vel_y = 0
                    self.on_ground = True
                if dy < 0:
                    self.rect.top = platform.rect.bottom
                    self.vel_y = 0

    def shoot(self):
        proj_x = self.rect.centerx + (self.rect.width // 2 if self.facing_right else -self.rect.width // 2)
        proj = Projectile(proj_x, self.rect.centery, direction=1 if self.facing_right else -1)
        self.projectiles.add(proj)

    def draw(self, surface, camera_x):
        surface.blit(self.image, (self.rect.x - camera_x, self.rect.y))
        self.projectiles.draw(surface)

# Enemy class
class Enemy(pygame.sprite.Sprite):
    def __init__(self, x, y, patrol_distance):
        super().__init__()
        self.image = pygame.Surface((40, 60))
        self.image.fill((200, 0, 0))  # Red human enemy
        self.rect = self.image.get_rect(topleft=(x, y))
        self.health = 50
        self.speed = 2
        self.patrol_distance = patrol_distance
        self.start_x = x
        self.direction = 1

    def update(self, platforms):
        self.rect.x += self.speed * self.direction
        if self.rect.x < self.start_x or self.rect.x > self.start_x + self.patrol_distance:
            self.direction *= -1
        for platform in platforms:
            if self.rect.colliderect(platform.rect):
                self.direction *= -1

    def draw(self, surface, camera_x):
        surface.blit(self.image, (self.rect.x - camera_x, self.rect.y))

# Collectible class
class Collectible(pygame.sprite.Sprite):
    def __init__(self, x, y, kind):
        super().__init__()
        self.kind = kind  # 'health' or 'life'
        self.image = pygame.Surface((30, 30))
        if kind == 'health':
            self.image.fill((0, 255, 0))
        else:
            self.image.fill((0, 0, 255))
        self.rect = self.image.get_rect(center=(x, y))

    def draw(self, surface, camera_x):
        surface.blit(self.image, (self.rect.x - camera_x, self.rect.y))

# Boss enemy class
class BossEnemy(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        self.image = pygame.Surface((80, 80))
        self.image.fill((150, 0, 0))
        self.rect = self.image.get_rect(topleft=(x, y))
        self.health = 300
        self.speed = 2
        self.direction = 1
        self.projectiles = pygame.sprite.Group()
        self.shoot_cooldown = 0

    def update(self, platforms, player_rect):
        self.rect.x += self.speed * self.direction
        if self.rect.x < 1850 or self.rect.x > 1950:
            self.direction *= -1

        for platform in platforms:
            if self.rect.colliderect(platform.rect):
                self.direction *= -1

        if self.shoot_cooldown > 0:
            self.shoot_cooldown -= 1
        else:
            if abs(self.rect.centery - player_rect.centery) < 50:
                self.shoot()
                self.shoot_cooldown = 60

        self.projectiles.update()

    def shoot(self):
        proj_x = self.rect.centerx + (self.direction * self.rect.width // 2)
        proj_y = self.rect.centery
        projectile = Projectile(proj_x, proj_y, speed=10 * self.direction, damage=20, direction=self.direction)
        self.projectiles.add(projectile)

    def draw(self, surface, camera_x):
        surface.blit(self.image, (self.rect.x - camera_x, self.rect.y))
        self.projectiles.draw(surface)

# Platform class
class Platform(pygame.sprite.Sprite):
    def __init__(self, x, y, w, h):
        super().__init__()
        self.image = pygame.Surface((w, h))
        self.image.fill((100, 100, 100))
        self.rect = self.image.get_rect(topleft=(x, y))

    def draw(self, surface, camera_x):
        surface.blit(self.image, (self.rect.x - camera_x, self.rect.y))

# Level class with 3 levels + boss
class Level:
    def __init__(self, number):
        self.number = number
        self.platforms = pygame.sprite.Group()
        self.enemies = pygame.sprite.Group()
        self.collectibles = pygame.sprite.Group()
        self.boss = None
        self.finish_line = None
        self.create_level(number)

    def create_level(self, num):
        self.platforms.empty()
        self.enemies.empty()
        self.collectibles.empty()
        self.boss = None
        self.finish_line = None

        if num == 1:
            self.platforms.add(Platform(0, SCREEN_HEIGHT - 40, 2400, 40))
            self.platforms.add(Platform(200, 350, 150, 20))
            self.platforms.add(Platform(600, 300, 200, 20))
            self.platforms.add(Platform(1000, 250, 150, 20))
            self.platforms.add(Platform(1400, 300, 150, 20))
            self.platforms.add(Platform(1800, 350, 400, 20))

            self.enemies.add(Enemy(400, SCREEN_HEIGHT - 100, 150))
            self.enemies.add(Enemy(1100, SCREEN_HEIGHT - 100, 150))
            self.enemies.add(Enemy(1900, SCREEN_HEIGHT - 100, 150))

            self.collectibles.add(Collectible(250, 320, 'health'))
            self.collectibles.add(Collectible(650, 270, 'life'))
            self.collectibles.add(Collectible(1450, 270, 'health'))

            self.finish_line = pygame.Rect(2300, SCREEN_HEIGHT - 100, 50, 60)

        elif num == 2:
            self.platforms.add(Platform(0, SCREEN_HEIGHT - 40, 2600, 40))
            self.platforms.add(Platform(300, 330, 180, 20))
            self.platforms.add(Platform(700, 290, 150, 20))
            self.platforms.add(Platform(1100, 250, 200, 20))
            self.platforms.add(Platform(1550, 290, 180, 20))
            self.platforms.add(Platform(2000, 330, 600, 20))

            self.enemies.add(Enemy(800, SCREEN_HEIGHT - 100, 150))
            self.enemies.add(Enemy(1300, SCREEN_HEIGHT - 100, 150))
            self.enemies.add(Enemy(2100, SCREEN_HEIGHT - 100, 200))

            self.collectibles.add(Collectible(350, 300, 'health'))
            self.collectibles.add(Collectible(1150, 220, 'life'))
            self.collectibles.add(Collectible(1650, 260, 'health'))

            self.finish_line = pygame.Rect(2550, SCREEN_HEIGHT - 100, 50, 60)

        elif num == 3:
            self.platforms.add(Platform(0, SCREEN_HEIGHT - 40, 2800, 40))
            self.platforms.add(Platform(500, 310, 180, 20))
            self.platforms.add(Platform(950, 270, 200, 20))
            self.platforms.add(Platform(1400, 230, 250, 20))
            self.platforms.add(Platform(1900, 280, 300, 20))
            self.platforms.add(Platform(2350, 320, 600, 20))

            self.enemies.add(Enemy(700, SCREEN_HEIGHT - 100, 150))
            self.enemies.add(Enemy(1200, SCREEN_HEIGHT - 100, 150))
            self.enemies.add(Enemy(1850, SCREEN_HEIGHT - 100, 150))
            self.enemies.add(Enemy(2400, SCREEN_HEIGHT - 100, 200))

            self.collectibles.add(Collectible(550, 280, 'health'))
            self.collectibles.add(Collectible(1000, 240, 'life'))
            self.collectibles.add(Collectible(1600, 200, 'health'))
            self.collectibles.add(Collectible(2200, 260, 'life'))

            self.boss = BossEnemy(2700, SCREEN_HEIGHT - 120)

            self.finish_line = pygame.Rect(2850, SCREEN_HEIGHT - 100, 50, 60)

    def draw(self, surface, camera_x):
        for platform in self.platforms:
            platform.draw(surface, camera_x)
        for collectible in self.collectibles:
            collectible.draw(surface, camera_x)
        for enemy in self.enemies:
            enemy.draw(surface, camera_x)
        if self.boss:
            self.boss.draw(surface, camera_x)

        if self.finish_line:
            finish_rect_screen = pygame.Rect(
                self.finish_line.x - camera_x,
                self.finish_line.y,
                self.finish_line.width,
                self.finish_line.height)
            pygame.draw.rect(surface, (255, 215, 0), finish_rect_screen)

    def update(self, player_rect):
        for enemy in self.enemies:
            enemy.update(self.platforms)
        if self.boss:
            self.boss.update(self.platforms, player_rect)

# Main Game class
class Game:
    def __init__(self):
        self.screen = screen
        self.clock = clock
        self.running = True
        self.score = 0
        self.level_num = 1
        self.level = Level(self.level_num)
        self.player = Player(50, SCREEN_HEIGHT - 100)
        self.camera_x = 0
        self.game_over = False

    def run(self):
        while self.running:
            self.clock.tick(FPS)
            self.handle_events()
            if not self.game_over:
                self.update()
            self.draw()
        pygame.quit()
        sys.exit()

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.KEYDOWN:
                if not self.game_over:
                    if event.key == pygame.K_SPACE:
                        self.player.jump()
                else:
                    if event.key == pygame.K_r:
                        self.restart_game()

    def update(self):
        self.player.handle_input(self.level.platforms)
        self.level.update(self.player.rect)
        self.player.projectiles.update()

        target_x = self.player.rect.centerx - SCREEN_WIDTH // 4
        self.camera_x += (target_x - self.camera_x) * 0.1
        if self.camera_x < 0:
            self.camera_x = 0

        # Player fell off screen
        if self.player.rect.top > SCREEN_HEIGHT + 100:
            self.player.lives -= 1
            self.player.health = 100
            self.player.rect.topleft = (50, SCREEN_HEIGHT - 100)
            if self.player.lives <= 0:
                self.game_over = True

        # Projectiles hit enemies
        for proj in self.player.projectiles:
            for enemy in self.level.enemies:
                if proj.rect.colliderect(enemy.rect) and enemy.health > 0:
                    enemy.health -= proj.damage
                    proj.kill()
                    if enemy.health <= 0:
                        enemy.kill()
                        self.score += 100
            if self.level.boss and proj.rect.colliderect(self.level.boss.rect):
                self.level.boss.health -= proj.damage
                proj.kill()
                if self.level.boss.health <= 0:
                    self.level.boss = None
                    self.score += 500

        # Boss projectiles hit player
        if self.level.boss:
            for proj in self.level.boss.projectiles:
                if proj.rect.colliderect(self.player.rect):
                    self.player.health -= proj.damage
                    proj.kill()

        # Enemies collide with player
        for enemy in self.level.enemies:
            if self.player.rect.colliderect(enemy.rect):
                self.player.health -= 1
        if self.level.boss and self.player.rect.colliderect(self.level.boss.rect):
            self.player.health -= 3

        # Collectibles collide with player
        for collectible in self.level.collectibles:
            if self.player.rect.colliderect(collectible.rect):
                if collectible.kind == 'health':
                    self.player.health = min(100, self.player.health + 20)
                elif collectible.kind == 'life':
                    self.player.lives += 1
                self.score += 50
                collectible.kill()

        # Player health/lives check
        if self.player.health <= 0:
            self.player.lives -= 1
            self.player.health = 100
            if self.player.lives <= 0:
                self.game_over = True

        # Level finish detection
        if self.level.finish_line and self.player.rect.colliderect(self.level.finish_line):
            self.level_num += 1
            if self.level_num > 3:
                self.game_over = True
            else:
                self.level = Level(self.level_num)
                self.player.rect.topleft = (50, SCREEN_HEIGHT - 100)
                self.camera_x = 0

    def draw(self):
        self.screen.fill((135, 206, 235))  # Sky blue background
        self.level.draw(self.screen, int(self.camera_x))
        self.player.draw(self.screen, int(self.camera_x))

        self.draw_health_bar(self.screen, 10, 10, self.player.health, 100, (255, 0, 0))
        draw_text(self.screen, f"Lives: {self.player.lives}", 24, 10, 45)
        draw_text(self.screen, f"Score: {self.score}", 24, 10, 75)
        draw_text(self.screen, f"Level: {self.level_num}", 24, SCREEN_WIDTH - 150, 10)

        if self.level.boss:
            self.draw_health_bar(self.screen, SCREEN_WIDTH - 210, 10, self.level.boss.health, 300, (200, 0, 0))
            draw_text(self.screen, "Boss", 24, SCREEN_WIDTH - 150, 45)

        if self.game_over:
            self.draw_game_over()

        pygame.display.flip()

    def draw_health_bar(self, surf, x, y, current, max_health, color):
        ratio = current / max_health
        pygame.draw.rect(surf, (50, 50, 50), (x - 2, y - 2, 204, 24))
        pygame.draw.rect(surf, color, (x, y, int(200 * ratio), 20))

    def draw_game_over(self):
        draw_text(self.screen, "GAME OVER", 64, SCREEN_WIDTH // 2 - 150, SCREEN_HEIGHT // 2 - 50, (255, 0, 0))
        draw_text(self.screen, "Press R to Restart", 32, SCREEN_WIDTH // 2 - 110, SCREEN_HEIGHT // 2 + 30)

    def restart_game(self):
        self.score = 0
        self.level_num = 1
        self.level = Level(self.level_num)
        self.player = Player(50, SCREEN_HEIGHT - 100)
        self.camera_x = 0
        self.game_over = False

if __name__ == "__main__":
    game = Game()
    game.run()
