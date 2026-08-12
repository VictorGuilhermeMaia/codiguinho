import pygame
import sys
import time
import random
import math

# --- Configurações Iniciais ---
pygame.init()

P1_NAME = "Cobra Ártica"
P1_COLOR = pygame.Color(0, 255, 150)   # Verde Frio
P2_NAME = "Cobra Vulcânica"
P2_COLOR = pygame.Color(255, 100, 50)  # Laranja Quente (Contraste)

# Configurações Ultra Fluidas
FPS = 144
MOVE_DELAY_NORMAL = 55   # Velocidade normal (ms)
MOVE_DELAY_FROZEN = 165  # Velocidade quando congelado (Câmera lenta)

SQUARE_SIZE = 24
UI_HEIGHT = SQUARE_SIZE * 5

# Resolução Solicitada
base_width, base_height = 1336, 768

# Cores de Inverno
black = pygame.Color(5, 5, 10)
winter_bg = pygame.Color(15, 25, 45)      # Noite fria
white = pygame.Color(255, 255, 255)
red = pygame.Color(255, 50, 50)
green = pygame.Color(50, 255, 50)
gold = pygame.Color(255, 215, 0)
ice_color = pygame.Color(150, 220, 255)   # Gelo claro
frost_blue = pygame.Color(0, 150, 255)    # Congelamento

font_ui = pygame.font.SysFont('consolas', 16, bold=True)
font_go = pygame.font.SysFont('arial', 70, bold=True)
font_dmg = pygame.font.SysFont('impact', 22)
clock = pygame.time.Clock()

display_window = pygame.display.set_mode((base_width, base_height), pygame.RESIZABLE)
pygame.display.set_caption(f"Snake PvP - WINTER EDITION ({FPS} FPS)")

# Ajuste de grade perfeito
frame_size_x = base_width - (base_width % SQUARE_SIZE)
frame_size_y = base_height - (base_height % SQUARE_SIZE)
game_window = pygame.Surface((frame_size_x, frame_size_y))
fx_surface = pygame.Surface((frame_size_x, frame_size_y), pygame.SRCALPHA)

# --- Efeitos Visuais (VFX) ---
class Snowflake:
    def __init__(self):
        self.x = random.randint(0, frame_size_x)
        self.y = random.randint(UI_HEIGHT, frame_size_y)
        self.speed = random.uniform(0.5, 2.0)
        self.size = random.uniform(1.5, 3.5)
        self.wind = random.uniform(-0.5, 0.5)
        self.offset = random.uniform(0, 10)
        
    def update(self):
        self.y += self.speed
        self.x += math.sin((pygame.time.get_ticks() / 1000.0) + self.offset) * 0.5 + self.wind
        if self.y > frame_size_y:
            self.y = UI_HEIGHT
            self.x = random.randint(0, frame_size_x)
            
    def draw(self, surface):
        pygame.draw.circle(surface, pygame.Color(255, 255, 255, 150), (int(self.x), int(self.y)), int(self.size))

class BackgroundWalker:
    def __init__(self):
        self.type = random.choice(['penguin', 'snowman'])
        self.dir = random.choice([1, -1])
        self.x = -50 if self.dir == 1 else frame_size_x + 50
        self.y = random.randrange(UI_HEIGHT + SQUARE_SIZE, frame_size_y - SQUARE_SIZE*2, SQUARE_SIZE)
        self.speed = random.uniform(0.3, 0.8)
        self.bob = 0
        
    def update(self):
        self.x += self.speed * self.dir
        self.bob = math.sin(pygame.time.get_ticks() / 150.0) * 3
        
    def draw(self, surface):
        if self.type == 'snowman':
            pygame.draw.circle(surface, white, (int(self.x), int(self.y)), 12) # Corpo
            pygame.draw.circle(surface, white, (int(self.x), int(self.y - 14 + self.bob*0.3)), 9) # Cabeça
            pygame.draw.polygon(surface, pygame.Color(255, 100, 0), [(self.x + 3*self.dir, self.y - 14), (self.x + 12*self.dir, self.y - 12), (self.x + 3*self.dir, self.y - 10)]) # Cenoura
        elif self.type == 'penguin':
            pygame.draw.ellipse(surface, black, (int(self.x - 10), int(self.y - 15 + self.bob), 20, 25))
            pygame.draw.ellipse(surface, white, (int(self.x - 6), int(self.y - 10 + self.bob), 12, 18))
            pygame.draw.polygon(surface, gold, [(self.x + 8*self.dir, self.y - 5 + self.bob), (self.x + 12*self.dir, self.y - 3 + self.bob), (self.x + 8*self.dir, self.y - 1 + self.bob)]) # Bico

class Particle:
    def __init__(self, x, y, color, speed_mult=1.0):
        self.x, self.y, self.color = x, y, color
        self.vx = random.uniform(-3, 3) * speed_mult
        self.vy = random.uniform(-3, 3) * speed_mult
        self.life = 255
        self.size = random.uniform(3, 7)
    def update(self):
        self.x += self.vx
        self.y += self.vy
        self.life -= 4
        self.size = max(0, self.size - 0.05)
    def draw(self, surface):
        if self.life > 0 and self.size > 0:
            c = (*self.color[:3], max(0, int(self.life)))
            pygame.draw.circle(surface, c, (int(self.x), int(self.y)), int(self.size))

class FloatingText:
    def __init__(self, x, y, text, color):
        self.x, self.y, self.text, self.color = x, y, text, color
        self.life, self.vy = 255, -0.8
    def update(self):
        self.y += self.vy
        self.life -= 3
    def draw(self, surface):
        if self.life > 0:
            txt = font_dmg.render(self.text, True, self.color)
            txt.set_alpha(max(0, int(self.life)))
            surface.blit(txt, (self.x, self.y))

# --- Mecânicas ---
class Projectile:
    def __init__(self, x, y, direction, color, owner):
        self.x, self.y = x + SQUARE_SIZE//2, y + SQUARE_SIZE//2
        self.color, self.owner = color, owner
        self.speed = 6
        self.vx = self.speed if direction == "RIGHT" else (-self.speed if direction == "LEFT" else 0)
        self.vy = self.speed if direction == "DOWN" else (-self.speed if direction == "UP" else 0)
        self.rect = pygame.Rect(0, 0, SQUARE_SIZE//2, SQUARE_SIZE//2)
        self.bounces = 0
        
    def update(self):
        self.x += self.vx
        self.y += self.vy
        self.rect.center = (self.x, self.y)

class Player:
    def __init__(self, name, base_color, start_pos, start_dir):
        self.name, self.base_color = name, base_color
        self.head_pos = list(start_pos)
        self.direction, self.next_dir = start_dir, start_dir
        self.input_locked = False
        
        offset = -SQUARE_SIZE if start_dir == "RIGHT" else SQUARE_SIZE
        self.body = [list(start_pos), [start_pos[0]+offset, start_pos[1]], [start_pos[0]+offset*2, start_pos[1]]]
        self.hp, self.energy = 100, 0
        
        self.last_move_time = 0
        self.last_attack_time = 0
        self.invulnerable_until = 0
        self.frozen_until = 0 # Tempo de lentidão (Gelo)

    def get_rects(self):
        return [pygame.Rect(b[0], b[1], SQUARE_SIZE, SQUARE_SIZE) for b in self.body]

    def take_damage(self, amount, current_time):
        if current_time > self.invulnerable_until:
            global screen_shake, hit_stop
            screen_shake = min(screen_shake + 15, 30)
            hit_stop = 8
            
            self.hp = max(0, self.hp - amount)
            self.invulnerable_until = current_time + 1000
            self.energy = min(100, self.energy + 20)
            
            create_particles(self.head_pos[0]+SQUARE_SIZE//2, self.head_pos[1]+SQUARE_SIZE//2, red, 20)
            floating_texts.append(FloatingText(self.head_pos[0], self.head_pos[1]-20, f"-{amount}", red))
            return True
        return False

# --- Globais ---
players, projectiles, particles, floating_texts = [], [], [], []
snowflakes, background_walkers = [], []
crystals, ice_blocks, ice_bombs = [], [], []
screen_shake, hit_stop = 0, 0
game_over_state = False

def get_safe_pos():
    cols = frame_size_x // SQUARE_SIZE
    rows_start = UI_HEIGHT // SQUARE_SIZE
    rows_end = frame_size_y // SQUARE_SIZE
    
    for _ in range(100):
        cx = random.randrange(1, cols - 1) * SQUARE_SIZE
        cy = random.randrange(rows_start + 1, rows_end - 1) * SQUARE_SIZE
        test_rect = pygame.Rect(cx, cy, SQUARE_SIZE, SQUARE_SIZE)
        
        safe = True
        for p in players:
            if any(test_rect.colliderect(r) for r in p.get_rects()): safe = False
        if any(test_rect.colliderect(pygame.Rect(a[0], a[1], SQUARE_SIZE, SQUARE_SIZE)) for a in ice_blocks): safe = False
        if any(test_rect.colliderect(pygame.Rect(c[0], c[1], SQUARE_SIZE, SQUARE_SIZE)) for c in crystals): safe = False
        if any(test_rect.colliderect(pygame.Rect(b['pos'][0], b['pos'][1], SQUARE_SIZE, SQUARE_SIZE)) for b in ice_bombs): safe = False
        
        if safe: return [cx, cy]
    return [0, UI_HEIGHT]

def generate_arena():
    global ice_blocks
    ice_blocks = []
    # Blocos de gelo simétricos
    for i in range(8):
        x = random.randrange(4, (frame_size_x // SQUARE_SIZE) // 2) * SQUARE_SIZE
        y = random.randrange((UI_HEIGHT // SQUARE_SIZE) + 2, (frame_size_y // SQUARE_SIZE) - 2) * SQUARE_SIZE
        ice_blocks.extend([[x, y], [x, y+SQUARE_SIZE], [x+SQUARE_SIZE, y]])
        opp_x = frame_size_x - x - (SQUARE_SIZE*2)
        ice_blocks.extend([[opp_x, y], [opp_x, y+SQUARE_SIZE], [opp_x-SQUARE_SIZE, y]])

def create_particles(x, y, color, count=15, speed=1.5):
    for _ in range(count): particles.append(Particle(x, y, color, speed))

def trigger_explosion(x, y, current_time, is_ult=False):
    global screen_shake, hit_stop, ice_blocks
    screen_shake = 35 if is_ult else 20
    hit_stop = 12 if is_ult else 6 
    
    radius = SQUARE_SIZE * 5 if is_ult else SQUARE_SIZE * 3
    dmg = 40 if is_ult else 20
    expl_color = frost_blue
    
    create_particles(x, y, expl_color, 80 if is_ult else 40, 4.0 if is_ult else 2.5)
    create_particles(x, y, white, 30, 2.0)
    floating_texts.append(FloatingText(x, y-30, "FROST NOVA!" if is_ult else "CONGELOU!", expl_color))

    # Congela e dá dano em quem estiver na área
    for p in players:
        for block in p.body:
            if math.hypot(block[0] - x, block[1] - y) <= radius:
                p.take_damage(dmg, current_time)
                p.frozen_until = current_time + (4000 if is_ult else 3000) # Fica lento!
                floating_texts.append(FloatingText(p.head_pos[0], p.head_pos[1]-40, "LENTO!", frost_blue))
                break
                
    if is_ult:
        # Destrói paredes de gelo na área
        ice_blocks = [obs for obs in ice_blocks if math.hypot(obs[0] - x, obs[1] - y) > radius]

def init_vars():
    global players, crystals, projectiles, particles, floating_texts, snowflakes, background_walkers, ice_bombs, game_over_state
    p1 = Player(P1_NAME, P1_COLOR, [SQUARE_SIZE * 5, frame_size_y // 2], "RIGHT")
    p2 = Player(P2_NAME, P2_COLOR, [frame_size_x - (SQUARE_SIZE * 5), frame_size_y // 2], "LEFT")
    players = [p1, p2]
    
    generate_arena()
    crystals = [get_safe_pos() for _ in range(6)]
    projectiles, particles, floating_texts, ice_bombs = [], [], [], []
    snowflakes = [Snowflake() for _ in range(150)]
    background_walkers = [BackgroundWalker() for _ in range(3)]
    game_over_state = False

init_vars()

# --- LOOP PRINCIPAL ---
running = True
while running:
    current_time = pygame.time.get_ticks()
    fx_surface.fill((0, 0, 0, 0)) 
    
    for event in pygame.event.get():
        if event.type == pygame.QUIT: running = False
        elif event.type == pygame.VIDEORESIZE:
            frame_size_x = event.w - (event.w % SQUARE_SIZE)
            frame_size_y = max(event.h, UI_HEIGHT + SQUARE_SIZE*10)
            frame_size_y = frame_size_y - (frame_size_y % SQUARE_SIZE)
            
            display_window = pygame.display.set_mode((frame_size_x, frame_size_y), pygame.RESIZABLE)
            game_window = pygame.Surface((frame_size_x, frame_size_y))
            fx_surface = pygame.Surface((frame_size_x, frame_size_y), pygame.SRCALPHA)
            generate_arena()
            
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE: running = False
            if game_over_state and event.key == pygame.K_r: init_vars()
            elif not game_over_state:
                p1, p2 = players[0], players[1]
                
                # Input P1
                if not p1.input_locked:
                    if event.key == pygame.K_w and p1.direction != "DOWN": p1.next_dir = "UP"; p1.input_locked = True
                    elif event.key == pygame.K_s and p1.direction != "UP": p1.next_dir = "DOWN"; p1.input_locked = True
                    elif event.key == pygame.K_a and p1.direction != "RIGHT": p1.next_dir = "LEFT"; p1.input_locked = True
                    elif event.key == pygame.K_d and p1.direction != "LEFT": p1.next_dir = "RIGHT"; p1.input_locked = True
                
                if event.key == pygame.K_SPACE: 
                    if current_time - p1.last_attack_time > 300:
                        projectiles.append(Projectile(p1.head_pos[0], p1.head_pos[1], p1.direction, p1.base_color, p1))
                        p1.last_attack_time = current_time
                elif event.key == pygame.K_q and p1.energy >= 100:
                    p1.energy = 0
                    trigger_explosion(p1.head_pos[0], p1.head_pos[1], current_time, is_ult=True)
                        
                # Input P2
                if not p2.input_locked:
                    if event.key == pygame.K_UP and p2.direction != "DOWN": p2.next_dir = "UP"; p2.input_locked = True
                    elif event.key == pygame.K_DOWN and p2.direction != "UP": p2.next_dir = "DOWN"; p2.input_locked = True
                    elif event.key == pygame.K_LEFT and p2.direction != "RIGHT": p2.next_dir = "LEFT"; p2.input_locked = True
                    elif event.key == pygame.K_RIGHT and p2.direction != "LEFT": p2.next_dir = "RIGHT"; p2.input_locked = True
                
                if event.key == pygame.K_RETURN or event.key == pygame.K_KP_ENTER:
                    if current_time - p2.last_attack_time > 300:
                        projectiles.append(Projectile(p2.head_pos[0], p2.head_pos[1], p2.direction, p2.base_color, p2))
                        p2.last_attack_time = current_time
                elif event.key == pygame.K_RCTRL and p2.energy >= 100:
                    p2.energy = 0
                    trigger_explosion(p2.head_pos[0], p2.head_pos[1], current_time, is_ult=True)

    if not game_over_state:
        if hit_stop > 0:
            hit_stop -= 1
        else:
            # Animações de Fundo (Neve e Pinguins)
            for s in snowflakes: s.update()
            for w in background_walkers: 
                w.update()
                # Reposiciona se sair muito da tela
                if (w.dir == 1 and w.x > frame_size_x + 100) or (w.dir == -1 and w.x < -100):
                    w.dir = random.choice([1, -1])
                    w.x = -50 if w.dir == 1 else frame_size_x + 50
                    w.y = random.randrange(UI_HEIGHT + SQUARE_SIZE, frame_size_y - SQUARE_SIZE*2, SQUARE_SIZE)
                    
            for pt in particles[:]:
                pt.update(); 
                if pt.life <= 0: particles.remove(pt)
            for ft in floating_texts[:]:
                ft.update(); 
                if ft.life <= 0: floating_texts.remove(ft)

            # Spawn de Bombas de Gelo
            if random.random() < 0.005 and len(ice_bombs) < 3:
                ice_bombs.append({'pos': get_safe_pos(), 'explode_time': current_time + 3500})

            # Projéteis
            for proj in projectiles[:]:
                proj.update()
                create_particles(proj.x, proj.y, proj.color, 1) 
                
                destroyed, bounced = False, False
                
                if proj.x < 0 or proj.x > frame_size_x or proj.y < UI_HEIGHT or proj.y > frame_size_y:
                    bounced = True
                    if proj.x < 0: proj.x += SQUARE_SIZE
                    elif proj.x > frame_size_x: proj.x -= SQUARE_SIZE
                    if proj.y < UI_HEIGHT: proj.y += SQUARE_SIZE
                    elif proj.y > frame_size_y: proj.y -= SQUARE_SIZE

                if not bounced and not destroyed:
                    for ib in ice_bombs[:]:
                        if pygame.Rect(ib['pos'][0], ib['pos'][1], SQUARE_SIZE, SQUARE_SIZE).colliderect(proj.rect):
                            trigger_explosion(ib['pos'][0], ib['pos'][1], current_time)
                            ice_bombs.remove(ib)
                            destroyed = True
                            break

                if not bounced and not destroyed:
                    for ast in ice_blocks:
                        if proj.rect.colliderect(pygame.Rect(ast[0], ast[1], SQUARE_SIZE, SQUARE_SIZE)):
                            create_particles(proj.x, proj.y, ice_color, 10)
                            bounced = True
                            break
                            
                if bounced:
                    if proj.bounces < 1:
                        proj.vx *= -1; proj.vy *= -1 # Simples ricochete reverso
                        proj.bounces += 1
                    else: destroyed = True

                if not destroyed:
                    for p in players:
                        if p != proj.owner:
                            for i, rect in enumerate(p.get_rects()):
                                if proj.rect.colliderect(rect):
                                    if p.take_damage(20, current_time):
                                        proj.owner.energy = min(100, proj.owner.energy + 20)
                                        if i > 0:
                                            p.body = p.body[:i]
                                            floating_texts.append(FloatingText(proj.x, proj.y, "CORTADO!", white))
                                    destroyed = True
                                    break
                            if destroyed: break

                if destroyed and proj in projectiles: projectiles.remove(proj)

            # Timers das Bombas
            for ib in ice_bombs[:]:
                if current_time >= ib['explode_time']:
                    trigger_explosion(ib['pos'][0], ib['pos'][1], current_time)
                    ice_bombs.remove(ib)

            # Movimento Independente das Cobras (Assíncrono)
            for p in players:
                # Se estiver congelado, o delay de movimento é muito maior (Câmera lenta)
                current_delay = MOVE_DELAY_FROZEN if current_time < p.frozen_until else MOVE_DELAY_NORMAL
                
                if current_time - p.last_move_time > current_delay:
                    p.direction = p.next_dir
                    p.input_locked = False 
                    
                    if p.direction == "UP": p.head_pos[1] -= SQUARE_SIZE
                    elif p.direction == "DOWN": p.head_pos[1] += SQUARE_SIZE
                    elif p.direction == "LEFT": p.head_pos[0] -= SQUARE_SIZE
                    elif p.direction == "RIGHT": p.head_pos[0] += SQUARE_SIZE
                    
                    p.head_pos[0] = p.head_pos[0] % frame_size_x
                    playable_h = frame_size_y - UI_HEIGHT
                    p.head_pos[1] = UI_HEIGHT + ((p.head_pos[1] - UI_HEIGHT) % playable_h)

                    p.body.insert(0, list(p.head_pos))
                    
                    # Coleta de Itens
                    head_rect = pygame.Rect(p.head_pos[0], p.head_pos[1], SQUARE_SIZE, SQUARE_SIZE)
                    ate = False
                    for i, c in enumerate(crystals):
                        if head_rect.colliderect(pygame.Rect(c[0], c[1], SQUARE_SIZE, SQUARE_SIZE)):
                            p.hp = min(100, p.hp + 15)
                            p.energy = min(100, p.energy + 10)
                            crystals[i] = get_safe_pos()
                            create_particles(c[0]+SQUARE_SIZE//2, c[1]+SQUARE_SIZE//2, green, 15)
                            ate = True
                            break
                    if not ate: p.body.pop()
                    
                    p.last_move_time = current_time

            # Colisões Físicas entre Corpos
            p1, p2 = players[0], players[1]
            p1_head, p2_head = pygame.Rect(p1.head_pos[0], p1.head_pos[1], SQUARE_SIZE, SQUARE_SIZE), pygame.Rect(p2.head_pos[0], p2.head_pos[1], SQUARE_SIZE, SQUARE_SIZE)
            
            for block in p1.get_rects()[1:]:
                if p1_head.colliderect(block): p1.take_damage(15, current_time)
            for block in p2.get_rects()[1:]:
                if p2_head.colliderect(block): p2.take_damage(15, current_time)
            for block in p2.get_rects():
                if p1_head.colliderect(block): p1.take_damage(15, current_time)
            for block in p1.get_rects():
                if p2_head.colliderect(block): p2.take_damage(15, current_time)
            for ast in ice_blocks:
                ast_rect = pygame.Rect(ast[0], ast[1], SQUARE_SIZE, SQUARE_SIZE)
                if p1_head.colliderect(ast_rect): p1.take_damage(10, current_time)
                if p2_head.colliderect(ast_rect): p2.take_damage(10, current_time)

            if p1.hp <= 0 or p2.hp <= 0: game_over_state = True

    # 3. RENDERIZAÇÃO
    game_window.fill(winter_bg)
    
    for s in snowflakes: s.draw(game_window)
    for w in background_walkers: w.draw(game_window)

    # Blocos de Gelo (Paredes)
    for ast in ice_blocks:
        rect = pygame.Rect(ast[0], ast[1], SQUARE_SIZE, SQUARE_SIZE)
        pygame.draw.rect(game_window, ice_color, rect, border_radius=4)
        pygame.draw.rect(game_window, white, rect, 2, border_radius=4) # Brilho do gelo
        pygame.draw.line(game_window, white, (ast[0]+4, ast[1]+4), (ast[0]+12, ast[1]+12), 2) # Reflexo

    # Bombas de Gelo
    for ib in ice_bombs:
        time_left = ib['explode_time'] - current_time
        blink = (current_time // max(40, int(time_left / 12))) % 2 == 0
        c = white if blink else frost_blue
        pygame.draw.circle(game_window, c, (ib['pos'][0]+SQUARE_SIZE//2, ib['pos'][1]+SQUARE_SIZE//2), SQUARE_SIZE//2)
        pygame.draw.circle(game_window, white, (ib['pos'][0]+SQUARE_SIZE//2, ib['pos'][1]+SQUARE_SIZE//2), SQUARE_SIZE//2, 2)
        # Símbolo floco de neve na bomba
        pygame.draw.line(game_window, black, (ib['pos'][0]+SQUARE_SIZE//2, ib['pos'][1]+4), (ib['pos'][0]+SQUARE_SIZE//2, ib['pos'][1]+SQUARE_SIZE-4))
        pygame.draw.line(game_window, black, (ib['pos'][0]+4, ib['pos'][1]+SQUARE_SIZE//2), (ib['pos'][0]+SQUARE_SIZE-4, ib['pos'][1]+SQUARE_SIZE//2))

    # Cristais Mágicos (Cura)
    for c in crystals:
        cx, cy = c[0] + SQUARE_SIZE//2, c[1] + SQUARE_SIZE//2
        pulse = math.sin(current_time / 150) * 3
        points = [(cx, cy - SQUARE_SIZE//2 - pulse), (cx + SQUARE_SIZE//2 + pulse, cy),
                  (cx, cy + SQUARE_SIZE//2 + pulse), (cx - SQUARE_SIZE//2 - pulse, cy)]
        pygame.draw.polygon(game_window, green, points)
        pygame.draw.polygon(game_window, white, points, 1)

    # Naves / Cobras
    for p in players:
        if current_time < p.invulnerable_until and (current_time // 50) % 2 == 0: continue
        
        is_frozen = current_time < p.frozen_until
        
        for i, block in enumerate(p.body):
            rect = pygame.Rect(block[0], block[1], SQUARE_SIZE, SQUARE_SIZE)
            
            # Se congelado, a cobra fica com tons de azul e gelo
            body_color = frost_blue if is_frozen else p.base_color
            head_color = white if is_frozen else white
            
            pygame.draw.rect(game_window, head_color if i==0 else body_color, rect, border_radius=4)
            pygame.draw.rect(game_window, black, rect, 2) 
            
            if i == 0:
                ox1, oy1, ox2, oy2 = 0, 0, 0, 0
                if p.direction == "UP": ox1, oy1, ox2, oy2 = 5, 5, 15, 5
                elif p.direction == "DOWN": ox1, oy1, ox2, oy2 = 5, 15, 15, 15
                elif p.direction == "LEFT": ox1, oy1, ox2, oy2 = 5, 5, 5, 15
                elif p.direction == "RIGHT": ox1, oy1, ox2, oy2 = 15, 5, 15, 15
                if ox1: 
                    pygame.draw.circle(game_window, black, (block[0]+ox1, block[1]+oy1), 3)
                    pygame.draw.circle(game_window, black, (block[0]+ox2, block[1]+oy2), 3)

    for proj in projectiles:
        pygame.draw.circle(game_window, white, (int(proj.x), int(proj.y)), SQUARE_SIZE//4)
        pygame.draw.circle(game_window, proj.color, (int(proj.x), int(proj.y)), SQUARE_SIZE//3, 2)
        
    for pt in particles: pt.draw(fx_surface)
    game_window.blit(fx_surface, (0,0)) 
    for ft in floating_texts: ft.draw(game_window)

    # UI 
    pygame.draw.rect(game_window, black, (0, 0, frame_size_x, UI_HEIGHT))
    pygame.draw.line(game_window, ice_color, (0, UI_HEIGHT), (frame_size_x, UI_HEIGHT), 3)
    
    bw = frame_size_x // 3
    for i, p in enumerate(players):
        x_base = 20 if i == 0 else frame_size_x - bw - 20
        pygame.draw.rect(game_window, pygame.Color(50, 0, 0), (x_base, UI_HEIGHT - 65, bw, 20))
        pygame.draw.rect(game_window, p.base_color, (x_base, UI_HEIGHT - 65, bw * (p.hp/100), 20))
        
        pygame.draw.rect(game_window, pygame.Color(50, 50, 0), (x_base, UI_HEIGHT - 35, bw, 15))
        ult_color = white if p.energy >= 100 and (current_time//100)%2==0 else gold
        pygame.draw.rect(game_window, ult_color, (x_base, UI_HEIGHT - 35, bw * (p.energy/100), 15))
        
        status = ""
        if current_time < p.frozen_until: status = "CONGELADO! "
        if p.energy >= 100: status += f"ULT PRONTO {'[Q]' if i==0 else '[CTRL]'}"
        
        txt = font_ui.render(f"{p.name} | HP: {p.hp} | {status}", True, white)
        game_window.blit(txt, (x_base, UI_HEIGHT - 95))

    if game_over_state:
        s = pygame.Surface((frame_size_x, frame_size_y), pygame.SRCALPHA)
        s.fill((0, 0, 0, 180))
        game_window.blit(s, (0,0))
        p1, p2 = players[0], players[1]
        win_txt = "EMPATE!" if p1.hp<=0 and p2.hp<=0 else f"{p1.name if p2.hp<=0 else p2.name} VENCEU!"
        t1 = font_go.render(win_txt, True, ice_color)
        t2 = font_ui.render("Pressione 'R' para Revanche!", True, white)
        game_window.blit(t1, (frame_size_x//2 - t1.get_width()//2, frame_size_y//2 - 50))
        game_window.blit(t2, (frame_size_x//2 - t2.get_width()//2, frame_size_y//2 + 30))

    shake_x = random.randint(-int(screen_shake), int(screen_shake)) if screen_shake > 0 else 0
    shake_y = random.randint(-int(screen_shake), int(screen_shake)) if screen_shake > 0 else 0
    display_window.fill(black)
    display_window.blit(game_window, (shake_x, shake_y))
    if screen_shake > 0: screen_shake -= 0.75 

    pygame.display.flip()
    clock.tick(FPS)

pygame.quit()
sys.exit()

