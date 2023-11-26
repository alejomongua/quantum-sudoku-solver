from qiskit.opflow import Z, I, PauliSumOp
from qiskit import QuantumCircuit, Aer, execute
from qiskit.quantum_info import Pauli
from qiskit.opflow import Z, I, PauliSumOp, Plus, SummedOp
from qiskit.utils import algorithm_globals
import numpy as np

# Establece una semilla para la reproducibilidad
algorithm_globals.random_seed = 12345

# Definimos el número de qubits necesarios
n = 4  # Tamaño del Sudoku (4x4)
qubits_por_celda = 2  # Necesitamos 2 qubits para codificar los números del 1 al 4

# Total de qubits requeridos
total_qubits = n * n * qubits_por_celda

# Creamos un circuito cuántico vacío con el número correcto de qubits
qc = QuantumCircuit(total_qubits)

# Coeficiente de penalización
alpha = 1000

# Hamiltoniano como una lista de términos de Pauli
hamiltonian_terms = []


def qubit_idx(row, col, num):
    """Función para obtener el índice del qubit en el circuito"""
    return (row * 4 + col) * 2 + num


# Función auxiliar para agregar términos al Hamiltoniano
def add_hamiltonian_term(pauli_string, coefficient):
    hamiltonian_terms.append((Pauli(pauli_string), coefficient))

# Function to create a Z operator that acts on a specific qubit


def single_qubit_z(qubit_index, total_qubits):
    # Crear un operador Z que actúe solo en el qubit deseado y como identidad en los demás
    return PauliSumOp(Z ^ (I ^ (total_qubits - qubit_index - 1)).tensor(I ^ qubit_index))


def one_number_per_cell():
    ops = []
    for row in range(4):
        for col in range(4):
            z0 = single_qubit_z(qubit_idx(row, col, 0), total_qubits)
            z1 = single_qubit_z(qubit_idx(row, col, 1), total_qubits)
            identidad = I ^ total_qubits
            # Asegurar que todos los operadores actúen sobre el mismo número de qubits
            cell_penalty = alpha * ((z0 + z1 - identidad) ** 2)
            ops.append(cell_penalty)
    return sum(ops)

# Función para la restricción de números únicos por fila


def unique_number_per_row():
    ops = []
    for row in range(4):
        for num in range(2):  # Dos qubits por número (1-4)
            for col1 in range(4):
                for col2 in range(col1 + 1, 4):
                    z1 = Z ^ I ^ (total_qubits - qubit_idx(row, col1, num) - 1)
                    z2 = Z ^ I ^ (total_qubits - qubit_idx(row, col2, num) - 1)
                    ops.append(alpha * (z1 * z2))
    return sum(ops)

# Función para la restricción de números únicos por columna


def unique_number_per_column():
    ops = []
    for col in range(4):
        for num in range(2):  # Dos qubits por número (1-4)
            for row1 in range(4):
                for row2 in range(row1 + 1, 4):
                    z1 = Z ^ I ^ (total_qubits - qubit_idx(row1, col, num) - 1)
                    z2 = Z ^ I ^ (total_qubits - qubit_idx(row2, col, num) - 1)
                    ops.append(alpha * (z1 * z2))
    return sum(ops)

# Función para la restricción de números únicos por subcuadrícula 2x2


def unique_number_per_subgrid():
    ops = []
    # Tamaño de la subcuadrícula
    subgrid_size = 2
    # Número de subcuadrículas en una fila/columna
    num_subgrids = 2

    # Iterar sobre cada subcuadrícula
    for subgrid_row in range(num_subgrids):
        for subgrid_col in range(num_subgrids):
            # Iterar sobre cada número dentro de la subcuadrícula
            for num in range(2):  # Dos qubits por número (1-4)
                # Comparar cada par de celdas dentro de la subcuadrícula
                for i in range(subgrid_size):
                    for j in range(subgrid_size):
                        cell1 = (subgrid_row * subgrid_size + i,
                                 subgrid_col * subgrid_size + j)
                        for k in range(subgrid_size):
                            for l in range(subgrid_size):
                                if (i, j) < (k, l):  # Evitar duplicados y comparaciones con uno mismo
                                    cell2 = (subgrid_row * subgrid_size + k,
                                             subgrid_col * subgrid_size + l)
                                    z1 = Z ^ I ^ (
                                        total_qubits - qubit_idx(*cell1, num) - 1)
                                    z2 = Z ^ I ^ (
                                        total_qubits - qubit_idx(*cell2, num) - 1)
                                    ops.append(alpha * (z1 * z2))
    return sum(ops)


# Construimos el Hamiltoniano completo con todas las restricciones
H = one_number_per_cell()  # + unique_number_per_row() + \
#     unique_number_per_column() + unique_number_per_subgrid()

# Convertimos el Hamiltoniano a PauliSumOp
H = PauliSumOp(H)
print(H)
