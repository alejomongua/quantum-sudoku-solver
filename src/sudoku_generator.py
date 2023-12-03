import random
import math


def initialize_board(n):
    return [[0 for _ in range(n)] for _ in range(n)]


def fill_diagonal_boxes(board, n):
    for i in range(0, n, int(n**0.5)):
        fill_box(board, i, i)


def find_empty(board):
    for i in range(len(board)):
        for j in range(len(board[0])):
            if board[i][j] == 0:
                return (i, j)  # fila, columna
    return None


def fill_box(board, row, col):
    n = len(board)
    num = 1
    for i in range(int(n**0.5)):
        for j in range(int(n**0.5)):
            while not check_validity(board, row + i, col + j, num):
                num = random.randint(1, n)
            board[row + i][col + j] = num
            num += 1


def check_validity(board, row, col, num):
    n = len(board)
    for x in range(n):
        if board[row][x] == num or board[x][col] == num:
            return False

    start_row = row - row % int(n**0.5)
    start_col = col - col % int(n**0.5)
    for i in range(int(n**0.5)):
        for j in range(int(n**0.5)):
            if board[i + start_row][j + start_col] == num:
                return False

    return True


def remove_numbers_from_board(board, n, num_to_remove):
    count = num_to_remove
    while count != 0:
        i = random.randint(0, n-1)
        j = random.randint(0, n-1)
        if board[i][j] != 0:
            count -= 1
            board[i][j] = 0


def fill_rest_of_board(board, n):
    for i in range(n):
        for j in range(n):
            if board[i][j] == 0:
                for num in range(1, n + 1):
                    if check_validity(board, i, j, num):
                        board[i][j] = num
                        if fill_rest_of_board(board, n) or not find_empty(board):
                            return True
                        board[i][j] = 0
                return False
    return True


def is_perfect_square(n):
    return n == math.isqrt(n) ** 2


def permute_numbers(board):
    # Para que no queden todos los sudoku exactamente iguales
    # se intercambian los números de posición, esto es, todos los 1 se cambian por 4, los 2 por 7, etc.
    n = len(board)
    # Primero determine que número va a intercambiar por cual
    intercambio = {}
    for i in range(1, n+1):
        propuesta = random.randint(1, n)
        while propuesta in intercambio.values():
            propuesta = random.randint(1, n)

        intercambio[i] = propuesta

    # Luego intercambie los números
    for i in range(n):
        for j in range(n):
            board[i][j] = intercambio[board[i][j]]


def generate_sudoku(n, num_to_remove):
    if not is_perfect_square(n):
        raise ValueError(
            "El tamaño del tablero debe ser un cuadrado perfecto.")

    board = initialize_board(n)
    fill_diagonal_boxes(board, n)
    fill_rest_of_board(board, n)
    remove_numbers_from_board(board, n, num_to_remove)
    permute_numbers(board)
    return board
