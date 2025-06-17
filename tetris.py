import pygame
import random
import os

pygame.init()
pygame.mixer.init()  # Inicializa el mixer de sonidos

# Constantes
BLOCK_SIZE = 30  # Tamaño de cada bloque en píxeles
GRID_WIDTH = 10  # Ancho del tablero en bloques
GRID_HEIGHT = 20  # Alto del tablero en bloques
SCREEN_WIDTH = BLOCK_SIZE * (GRID_WIDTH + 8)  # Espacio extra para la siguiente pieza y puntaje
SCREEN_HEIGHT = BLOCK_SIZE * GRID_HEIGHT

# Colores
BLACK = (0, 0, 0)         # Fondo
WHITE = (255, 255, 255)   # Texto
CYAN = (0, 255, 255)      # Pieza I
BLUE = (0, 0, 255)        # Pieza J
ORANGE = (255, 165, 0)    # Pieza L
YELLOW = (255, 255, 0)    # Pieza O
GREEN = (0, 255, 0)       # Pieza S
PURPLE = (128, 0, 128)    # Pieza T
RED = (255, 0, 0)         # Pieza Z
GRAY = (128, 128, 128)    # Líneas de la cuadrícula

# Formas de las figuras (matrices)
SHAPES = [
    [[1, 1, 1, 1]],           # I
    [[1, 0, 0],
     [1, 1, 1]],             # J
    [[0, 0, 1],
     [1, 1, 1]],             # L
    [[1, 1],
     [1, 1]],                # O
    [[0, 1, 1],
     [1, 1, 0]],             # S
    [[0, 1, 0],
     [1, 1, 1]],             # T
    [[1, 1, 0],
     [0, 1, 1]]              # Z
]

COLORS = [CYAN, BLUE, ORANGE, YELLOW, GREEN, PURPLE, RED]

# Directorio base para cargar recursos (imágenes, sonidos, etc.)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

class Tetromino:
    def __init__(self):
        # Selecciona aleatoriamente la forma
        self.shape_idx = random.randint(0, len(SHAPES) - 1)
        # Se hace una copia de la forma para evitar modificar la original
        self.shape = [row[:] for row in SHAPES[self.shape_idx]]
        self.color = COLORS[self.shape_idx]
        self.x = GRID_WIDTH // 2 - len(self.shape[0]) // 2
        self.y = 0

    def rotate(self):
        # Rotación: trasponer y luego invertir el orden de las filas
        self.shape = [[self.shape[y][x] for y in range(len(self.shape) - 1, -1, -1)]
                      for x in range(len(self.shape[0]))]

class TetrisGame:
    def __init__(self):
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("Tetris")
        self.clock = pygame.time.Clock()
        self.grid = [[BLACK for _ in range(GRID_WIDTH)] for _ in range(GRID_HEIGHT)]
        self.current_piece = Tetromino()
        self.next_piece = Tetromino()
        self.game_over = False
        self.score = 0
        self.fall_speed = 500  # milisegundos entre caídas
        self.font = pygame.font.Font(None, 36)
        
        # Cargar sonidos (ahora con extensión mp3)
        self.sound_rotate = self.load_sound("rotate.mp3")
        self.sound_lock = self.load_sound("lock.mp3")
        self.sound_clear = self.load_sound("clear.mp3")
        self.sound_move = self.load_sound("move.mp3")  # Opcional: para movimientos laterales/abajo
        self.sound_fall = self.load_sound("fall.mp3")  # Opcional: para cada movimiento de caída

    def load_sound(self, filename):
        """Carga un sonido desde la carpeta assets/sounds."""
        sound_path = os.path.join(BASE_DIR, "assets", "sounds", filename)
        try:
            sound = pygame.mixer.Sound(sound_path)
            return sound
        except Exception as e:
            print(f"Error al cargar el sonido {filename}: {e}")
            return None

    def valid_move(self, piece, x, y):
        for i in range(len(piece.shape)):
            for j in range(len(piece.shape[i])):
                if piece.shape[i][j]:
                    new_x = x + j
                    new_y = y + i
                    # Verificar límites y colisiones
                    if new_x < 0 or new_x >= GRID_WIDTH or new_y >= GRID_HEIGHT:
                        return False
                    if new_y >= 0 and self.grid[new_y][new_x] != BLACK:
                        return False
        return True

    def lock_piece(self):
        for i in range(len(self.current_piece.shape)):
            for j in range(len(self.current_piece.shape[i])):
                if self.current_piece.shape[i][j]:
                    # Si la pieza se bloquea fuera de la parte visible, es game over
                    if self.current_piece.y + i < 0:
                        self.game_over = True
                        return
                    self.grid[self.current_piece.y + i][self.current_piece.x + j] = self.current_piece.color

        # Reproducir sonido de bloqueo de pieza
        if self.sound_lock:
            self.sound_lock.play()

        self.clear_lines()
        self.current_piece = self.next_piece
        self.next_piece = Tetromino()
        # Verificar que la nueva pieza pueda colocarse
        if not self.valid_move(self.current_piece, self.current_piece.x, self.current_piece.y):
            self.game_over = True

    def clear_lines(self):
        lines_cleared = 0
        # Recorrer la cuadrícula de abajo hacia arriba
        for i in range(len(self.grid) - 1, -1, -1):
            if all(cell != BLACK for cell in self.grid[i]):
                lines_cleared += 1
                del self.grid[i]
                self.grid.insert(0, [BLACK for _ in range(GRID_WIDTH)])
        if lines_cleared:
            self.score += 100 * (lines_cleared ** 2)
            # Reproducir sonido de limpieza de línea
            if self.sound_clear:
                self.sound_clear.play()

    def draw_grid(self):
        for i in range(GRID_HEIGHT):
            for j in range(GRID_WIDTH):
                pygame.draw.rect(self.screen, self.grid[i][j],
                                 (j * BLOCK_SIZE, i * BLOCK_SIZE, BLOCK_SIZE, BLOCK_SIZE))
                pygame.draw.rect(self.screen, GRAY,
                                 (j * BLOCK_SIZE, i * BLOCK_SIZE, BLOCK_SIZE, BLOCK_SIZE), 1)

    def draw_piece(self, piece, offset_x, offset_y):
        for i in range(len(piece.shape)):
            for j in range(len(piece.shape[i])):
                if piece.shape[i][j]:
                    pygame.draw.rect(self.screen, piece.color,
                                     ((offset_x + j) * BLOCK_SIZE, (offset_y + i) * BLOCK_SIZE, BLOCK_SIZE, BLOCK_SIZE))
                    pygame.draw.rect(self.screen, GRAY,
                                     ((offset_x + j) * BLOCK_SIZE, (offset_y + i) * BLOCK_SIZE, BLOCK_SIZE, BLOCK_SIZE), 1)

    def draw_next_piece(self):
        # Dibuja la siguiente pieza en la parte derecha de la pantalla
        next_piece_text = self.font.render("Siguiente:", True, WHITE)
        self.screen.blit(next_piece_text, (GRID_WIDTH * BLOCK_SIZE + 20, 20))
        self.draw_piece(self.next_piece, GRID_WIDTH + 2, 2)

    def draw_score(self):
        score_text = self.font.render(f"Puntaje: {self.score}", True, WHITE)
        self.screen.blit(score_text, (GRID_WIDTH * BLOCK_SIZE + 20, 150))

    def run(self):
        # Evento para la caída automática de la pieza
        fall_event = pygame.USEREVENT + 1
        pygame.time.set_timer(fall_event, self.fall_speed)

        running = True
        while running:
            self.screen.fill(BLACK)
            self.draw_grid()
            self.draw_piece(self.current_piece, self.current_piece.x, self.current_piece.y)
            self.draw_next_piece()
            self.draw_score()

            pygame.display.update()
            self.clock.tick(60)

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False

                elif event.type == fall_event:
                    # Mover la pieza hacia abajo
                    if self.valid_move(self.current_piece, self.current_piece.x, self.current_piece.y + 1):
                        self.current_piece.y += 1
                        if self.sound_fall:
                            self.sound_fall.play()
                    else:
                        self.lock_piece()

                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_LEFT:
                        if self.valid_move(self.current_piece, self.current_piece.x - 1, self.current_piece.y):
                            self.current_piece.x -= 1
                            if self.sound_move:
                                self.sound_move.play()
                    elif event.key == pygame.K_RIGHT:
                        if self.valid_move(self.current_piece, self.current_piece.x + 1, self.current_piece.y):
                            self.current_piece.x += 1
                            if self.sound_move:
                                self.sound_move.play()
                    elif event.key == pygame.K_DOWN:
                        if self.valid_move(self.current_piece, self.current_piece.x, self.current_piece.y + 1):
                            self.current_piece.y += 1
                            if self.sound_move:
                                self.sound_move.play()
                    elif event.key == pygame.K_UP:
                        # Rotar la pieza
                        original_shape = [row[:] for row in self.current_piece.shape]
                        self.current_piece.rotate()
                        # Si la rotación no es válida, se revierte
                        if not self.valid_move(self.current_piece, self.current_piece.x, self.current_piece.y):
                            self.current_piece.shape = original_shape
                        else:
                            if self.sound_rotate:
                                self.sound_rotate.play()

            if self.game_over:
                running = False

        pygame.quit()

if __name__ == "__main__":
    game = TetrisGame()
    game.run()