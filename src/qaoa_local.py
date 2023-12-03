from qiskit import Aer
from qiskit.utils import QuantumInstance
from qiskit.algorithms import QAOA
from qiskit.algorithms.optimizers import COBYLA
from qiskit.opflow import PauliSumOp


from restrictions import create_hamiltonian

QUBITS_PER_CELL = 4
SUDOKU_ROWS = 2
SUDOKU_COLS = 2
ALPHA = 100
TOTAL_QUBITS = SUDOKU_COLS * SUDOKU_ROWS, QUBITS_PER_CELL


def convert_to_paulisumop(sparse_op):
    # Convertir SparsePauliOp a una lista de tuplas para PauliSumOp
    list_of_tuples = [(pauli.to_label(), coeff)
                      for pauli, coeff in zip(sparse_op.paulis, sparse_op.coeffs)]
    return PauliSumOp.from_list(list_of_tuples)


def store_intermediate_result(eval_count, parameters, mean, std):
    global optimal_params
    optimal_params = parameters


if __name__ == '__main__':
    H = create_hamiltonian(ALPHA, SUDOKU_ROWS, QUBITS_PER_CELL, SUDOKU_COLS)

    H_converted = convert_to_paulisumop(H)

    backend = Aer.get_backend('qasm_simulator')

    quantum_instance = QuantumInstance(backend, shots=20000)

    optimizer = COBYLA(maxiter=500)

    optimal_params = []
    qaoa = QAOA(optimizer, quantum_instance=quantum_instance,
                callback=store_intermediate_result)

    result = qaoa.compute_minimum_eigenvalue(H_converted)

    counts = result.eigenstate

    # La configuración de qubits más probable es nuestra solución
    solution = max(counts, key=counts.get)  # type: ignore

    print(solution)

    # Decodificar la solución en formato de Sudoku
    sudoku_solution = []

    for i in range(SUDOKU_ROWS):
        row = []
        for j in range(SUDOKU_COLS):
            idx = i * SUDOKU_COLS + j
            number = solution[idx * QUBITS_PER_CELL:idx *
                              QUBITS_PER_CELL + QUBITS_PER_CELL]
            number = int(number, 2)
            row.append(number)
        sudoku_solution.append(row)

    # Imprimir la solución
    for row in sudoku_solution:
        print(row)
