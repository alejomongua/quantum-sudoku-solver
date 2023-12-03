import math
from qiskit.quantum_info import SparsePauliOp, Pauli


def qubit_idx(row, col, num, cols, qubits_per_cell):
    return (row * cols + col) * qubits_per_cell + num


def single_qubit_z(qubit_index, total_qubits):
    pauli_str = ['I'] * total_qubits
    pauli_str[qubit_index] = 'Z'
    return SparsePauliOp(Pauli(''.join(pauli_str)))


def one_number_per_cell(alpha, rows, cols, qubits_per_cell):
    total_qubits = rows * cols * qubits_per_cell
    ops = []
    for row in range(rows):
        for col in range(cols):
            z0 = single_qubit_z(
                qubit_idx(row, col, 0, cols, qubits_per_cell), total_qubits)
            z1 = single_qubit_z(
                qubit_idx(row, col, 1, cols, qubits_per_cell), total_qubits)
            identidad = SparsePauliOp(Pauli('I' * total_qubits))
            cell_penalty = (z0 + z1 - identidad) ** 2
            ops.append(alpha * cell_penalty)
    return sum(ops)


def unique_number_per_row(alpha, rows, cols, qubits_per_cell):
    total_qubits = rows * cols * qubits_per_cell
    ops = []
    for row in range(rows):
        for num in range(qubits_per_cell):
            for col1 in range(cols):
                for col2 in range(col1 + 1, cols):
                    z1 = single_qubit_z(
                        qubit_idx(row, col1, num, cols, qubits_per_cell), total_qubits)
                    z2 = single_qubit_z(
                        qubit_idx(row, col2, num, cols, qubits_per_cell), total_qubits)
                    combined_op = z1.compose(z2)
                    ops.append(alpha * combined_op)
    return sum(ops)


def unique_number_per_column(alpha, rows, cols, qubits_per_cell):
    total_qubits = rows * cols * qubits_per_cell
    ops = []
    for col in range(cols):
        for num in range(qubits_per_cell):
            for row1 in range(rows):
                for row2 in range(row1 + 1, rows):
                    z1 = single_qubit_z(
                        qubit_idx(row1, col, num, cols, qubits_per_cell), total_qubits)
                    z2 = single_qubit_z(
                        qubit_idx(row2, col, num, cols, qubits_per_cell), total_qubits)
                    combined_op = z1.compose(z2)
                    ops.append(alpha * combined_op)
    return sum(ops)


def unique_number_per_subgrid(alpha, rows, cols, qubits_per_cell):
    total_qubits = rows * cols * qubits_per_cell
    ops = []
    # Ajustar según la lógica del Sudoku más pequeño
    subgrid_size = math.isqrt(rows)
    for subgrid_row in range(rows // subgrid_size):
        for subgrid_col in range(cols // subgrid_size):
            for num in range(qubits_per_cell):
                for i in range(subgrid_size):
                    for j in range(subgrid_size):
                        cell1 = (subgrid_row * subgrid_size + i,
                                 subgrid_col * subgrid_size + j)
                        for k in range(subgrid_size):
                            for l in range(subgrid_size):
                                if (i, j) < (k, l):
                                    cell2 = (subgrid_row * subgrid_size + k,
                                             subgrid_col * subgrid_size + l)
                                    z1 = single_qubit_z(
                                        qubit_idx(*cell1, num, cols, qubits_per_cell), total_qubits)
                                    z2 = single_qubit_z(
                                        qubit_idx(*cell2, num, cols, qubits_per_cell), total_qubits)
                                    combined_op = z1.compose(z2)
                                    ops.append(alpha * combined_op)
    return sum(ops)


def create_hamiltonian(alpha, rows, qubits_per_cell, cols=None):
    if cols is None:
        cols = rows
    H = one_number_per_cell(alpha, rows, cols, qubits_per_cell) \
        + unique_number_per_row(alpha, rows, cols, qubits_per_cell) \
        + unique_number_per_column(alpha, rows, cols, qubits_per_cell) \
        + unique_number_per_subgrid(alpha, rows, cols, qubits_per_cell)
    return H


if __name__ == '__main__':
    import sys

    if len(sys.argv) > 1:
        print(f'Usage: python {sys.argv[0]} <rows> [<cols>] [<alpha>]')
        sys.exit(1)

    rows = int(sys.argv[1])
    cols = None
    if len(sys.argv) > 2:
        cols = int(sys.argv[2])

    alpha = 1000
    if len(sys.argv) > 3:
        alpha = int(sys.argv[3])

    qubits_per_cell = 4

    H = one_number_per_cell(alpha, rows, cols, qubits_per_cell) \
        + unique_number_per_row(alpha, rows, cols, qubits_per_cell) \
        + unique_number_per_column(alpha, rows, cols, qubits_per_cell) \
        + unique_number_per_subgrid(alpha, rows, cols, qubits_per_cell)
    print(H)
