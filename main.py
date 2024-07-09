import pygame as pg
import math

WIDTH = 800
HEIGHT = 600

RES = (WIDTH, HEIGHT)

PLAYER_SPEED = 0.005
PLAYER_ROT_SPEED = 0.001

mini_map = [
    [0, 0, 0, 0, 0, 0],
    [0, 2, 1, 3, 0, 0],
    [0, 4, 0, 5, 0, 0],
    [0, 6, 0, 7, 0, 0],
    [0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 2, 0],
    [0, 0, 0, 0, 0, 0],
]

PLAYER_POS = 1.5, 5
PLAYER_ANGLE = 0

FOV = math.pi / 3
HALF_FOV = FOV / 2

NUM_RAYS = WIDTH // 3
DELTA_ANGLE = FOV / NUM_RAYS

MAX_DEPTH = 30

SCREEN_DIST = WIDTH // 2 / math.tan(HALF_FOV)
SCALE = WIDTH // NUM_RAYS

COL1 = (156, 214, 228)
COL2 = (250, 235, 215)
COL3 = (127, 255, 212)
COL4 = (0, 127, 255)
COL5 = (245, 245, 220)
COL6 = (127, 255, 212)
COL7 = (255, 228, 196)

TEXTURE_SIZE = 1024
HALF_TEX_SIZE = TEXTURE_SIZE // 2


class Map:
    def __init__(self):
        self.mini_map = mini_map
        self.world_map = {}
        self.rows = len(self.mini_map)
        self.cols = len(self.mini_map[0])
        self.get_map()

    def get_map(self):
        for j, row in enumerate(self.mini_map):
            for i, value in enumerate(row):
                if value: self.world_map[(i, j)] = value

    def draw(self, surf):
        pg.draw.rect(surf, COL1, (0, 0, len(mini_map[0]) * 25, len(mini_map) * 25), 100)

        for x in range(0, len(mini_map[0]) + 1):
            pg.draw.line(screen, 'black', (x * 25, 0), (x * 25, len(mini_map) * 25), 1)

        for y in range(0, len(mini_map) + 1):
            pg.draw.line(screen, 'black', (0, y * 25), (len(mini_map[0]) * 25, y * 25), 1)

        [pg.draw.rect(surf, COL2, (pos[0] * 25, pos[1] * 25, 25, 25), 5)
         for pos in self.world_map]


class Player:
    def __init__(self):
        self.x, self.y = PLAYER_POS
        self.angle = PLAYER_ANGLE

    def movement(self, dt):
        sin_a = math.sin(self.angle)
        cos_a = math.cos(self.angle)
        dx, dy = 0, 0
        speed = PLAYER_SPEED * dt
        speed_sin = speed * sin_a
        speed_cos = speed * cos_a

        keys = pg.key.get_pressed()
        if keys[pg.K_w]:
            dx += speed_cos
            dy += speed_sin
        if keys[pg.K_s]:
            dx += -speed_cos
            dy += -speed_sin
        if keys[pg.K_a]:
            dx += speed_sin
            dy += -speed_cos
        if keys[pg.K_d]:
            dx += -speed_sin
            dy += speed_cos

        self.x += dx
        self.y += dy

        if keys[pg.K_LEFT]: self.angle -= PLAYER_ROT_SPEED * dt
        if keys[pg.K_RIGHT]: self.angle += PLAYER_ROT_SPEED * dt

        self.angle %= math.tau

    def draw(self, surf):
        pg.draw.circle(surf, (0, 0, 0), (self.x * 25, self.y * 25), 10)
        pg.draw.circle(surf, COL3, (self.x * 25, self.y * 25), 5)

    @property
    def pos(self): return self.x, self.y
    @property
    def map_pos(self): return int(self.x), int(self.y)


def ray_cast(p: Player, ma: Map, surf):
    ray_cast_result = []
    ox, oy = p.pos
    x_map, y_map = p.map_pos

    ray_angle = p.angle - HALF_FOV + 0.0001
    for ray in range(NUM_RAYS):
        sin_a = math.sin(ray_angle)
        cos_a = math.cos(ray_angle)

        color = 'white'

        # Horizontal
        y_hor, dy = (y_map + 1, 1) if sin_a > 0 else (y_map - 1e-6, -1)

        depth_hor = (y_hor - oy) / sin_a
        x_hor = ox + depth_hor * cos_a

        delta_depth = dy / sin_a
        dx = delta_depth * cos_a

        wall_type_h = 0
        for i in range(MAX_DEPTH):
            tile_hor = int(x_hor), int(y_hor)
            if tile_hor in ma.world_map:
                wall_type_h = ma.world_map[tile_hor]
                break
            x_hor += dx
            y_hor += dy
            depth_hor += delta_depth

        # Vertical
        x_vert, dx = (x_map + 1, 1) if cos_a > 0 else (x_map - 1e-6, -1)

        depth_vert = (x_vert - ox) / cos_a
        y_vert = oy + depth_vert * sin_a

        delta_depth = dx / cos_a
        dy = delta_depth * sin_a

        wall_type_v = 0
        for i in range(MAX_DEPTH):
            tile_vert = int(x_vert), int(y_vert)
            if tile_vert in ma.world_map:
                wall_type_v = ma.world_map[tile_vert]
                break
            x_vert += dx
            y_vert += dy
            depth_vert += delta_depth

        if depth_vert < depth_hor:
            depth = depth_vert
            tile_type = wall_type_v
            y_vert %= 1
            offset = y_vert if cos_a > 0 else (1 - y_vert)
        else:
            depth = depth_hor
            tile_type = wall_type_h
            x_hor %= 1
            offset = (1 - x_hor) if sin_a > 0 else x_hor

        depth *= math.cos(p.angle - ray_angle)

        proj_height = SCREEN_DIST / (depth + 0.001)

        if depth < MAX_DEPTH - 5:
            if tile_type == 1:
                col = COL2
                pg.draw.rect(surf, (col[0] / (1 + depth ** 5 * 0.001), col[1] / (1 + depth ** 5 * 0.001),
                                    col[2] / (1 + depth ** 5 * 0.001)), (ray * SCALE,
                                                                         HEIGHT // 2 - proj_height // 2,
                                                                         SCALE, proj_height))

            else:
                wall_column = walls_textures[tile_type].subsurface(
                    offset * (TEXTURE_SIZE - SCALE), 0, SCALE, TEXTURE_SIZE
                )
                wall_column = pg.transform.scale(wall_column, (SCALE, proj_height))
                wall_pos = (ray * SCALE, HEIGHT // 2 - proj_height // 2)

                surf.blit(wall_column, wall_pos)

        ray_angle += DELTA_ANGLE
    return ray_cast_result


screen = pg.display.set_mode(RES)
walls_textures = {
    2: pg.transform.scale(pg.image.load('textures/Wall1.png').convert_alpha(), (TEXTURE_SIZE, TEXTURE_SIZE)),
    3: pg.transform.scale(pg.image.load('textures/Wall2.jpg').convert_alpha(), (TEXTURE_SIZE, TEXTURE_SIZE)),
    4: pg.transform.scale(pg.image.load('textures/Wall3.png').convert_alpha(), (TEXTURE_SIZE, TEXTURE_SIZE)),
    5: pg.transform.scale(pg.image.load('textures/Wall4.jpg').convert_alpha(), (TEXTURE_SIZE, TEXTURE_SIZE)),
    6: pg.transform.scale(pg.image.load('textures/Wall5.png').convert_alpha(), (TEXTURE_SIZE, TEXTURE_SIZE)),
    7: pg.transform.scale(pg.image.load('textures/Wall6.jpg').convert_alpha(), (TEXTURE_SIZE, TEXTURE_SIZE)),
}
clock = pg.time.Clock()
m = Map()
player = Player()
dt = 1

m.get_map()

while True:
    for event in pg.event.get():
        if event.type == pg.QUIT:
            pg.quit()
            exit()

    player.movement(dt)

    pg.display.flip()
    dt = clock.tick()
    pg.display.set_caption(f'Raycaster {clock.get_fps()}')

    screen.fill((0, 0, 0))
    ray_cast(player, m, screen)
    m.draw(screen)
    player.draw(screen)
