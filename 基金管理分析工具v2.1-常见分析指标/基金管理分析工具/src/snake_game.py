import pygame
import random
import time

# 初始化pygame
pygame.init()

# 游戏常量
WIDTH, HEIGHT = 600, 400
GRID_SIZE = 20
WHITE, RED = (255, 255, 255), (255, 0, 0)
NAVY_BLUE, LIGHT_GREEN = (30, 144, 255), (199, 236, 200)

screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("贪吃蛇")

class Direction:
    LEFT, RIGHT, UP, DOWN = (-1, 0), (1, 0), (0, -1), (0, 1)

class Snake:
    def __init__(self):
        self.body = [(WIDTH//2, HEIGHT//2)]
        self.direction = Direction.RIGHT
        self.grow = False

    def move(self):
        head_x, head_y = self.body[0]
        dx, dy = self.direction
        new_head = ((head_x + dx*GRID_SIZE) % WIDTH, (head_y + dy*GRID_SIZE) % HEIGHT)
        self.body.insert(0, new_head)
        if not self.grow: self.body.pop()
        self.grow = False

class Food:
    def __init__(self):
        self.position = self.random_position()
    
    def random_position(self):
        while True:
            pos = (random.randrange(0, WIDTH, GRID_SIZE), 
                  random.randrange(0, HEIGHT, GRID_SIZE))
            if pos not in snake.body: return pos

snake = Snake()
food = Food()
score, game_over = 0, False

while True:
    screen.fill(LIGHT_GREEN)
    
    for event in pygame.event.get():
        if event.type == pygame.QUIT: pygame.quit(); exit()
        if event.type == pygame.KEYDOWN:
            if game_over:
                if event.key == pygame.K_r: snake, food, score, game_over = Snake(), Food(), 0, False
                elif event.key == pygame.K_q: pygame.quit(); exit()
            else:
                directions = {pygame.K_LEFT: Direction.LEFT, pygame.K_RIGHT: Direction.RIGHT,
                            pygame.K_UP: Direction.UP, pygame.K_DOWN: Direction.DOWN}
                if event.key in directions and snake.direction != (-directions[event.key][0], -directions[event.key][1]):
                    snake.direction = directions[event.key]

    if not game_over:
        snake.move()
        if snake.body[0] == food.position:
            snake.grow, food.position, score = True, food.random_position(), score + 1
        game_over = len(snake.body) != len(set(snake.body))

    for segment in snake.body:
        pygame.draw.rect(screen, NAVY_BLUE, (*segment, GRID_SIZE-1, GRID_SIZE-1))
    pygame.draw.rect(screen, RED, (*food.position, GRID_SIZE-1, GRID_SIZE-1))
    
    font = pygame.font.SysFont("simhei", 24)
    screen.blit(font.render(f"分数: {score}", True, WHITE), (10, 10))
    if game_over:
        screen.blit(font.render("游戏结束！按R重新开始，Q退出", True, RED), (WIDTH//2-160, HEIGHT//2-20))
    
    pygame.display.update()
    time.sleep(0.1)

pygame.quit()
