import math
import os
import sys
import pickle

from qiskit import QuantumRegister, transpile, assemble, Aer
from qiskit.utils import QuantumInstance
from qiskit.circuit import Parameter, QuantumCircuit
from qiskit.circuit.library import RYGate, CXGate
from qiskit.algorithms import VQE
from qiskit.algorithms.optimizers import SPSA
from qiskit.opflow import PauliSumOp


from restrictions import create_hamiltonian

QUBITS_PER_CELL = 2
SUDOKU_ROWS = 2
SUDOKU_COLS = 2
ALPHA = 100
TOTAL_QUBITS = SUDOKU_COLS * SUDOKU_ROWS, QUBITS_PER_CELL


def create_subgrids(num_rows, num_cols, subgrid_rows=None, subgrid_cols=None):
    if subgrid_rows is None:
        subgrid_rows = int(math.sqrt(num_rows))
    if subgrid_cols is None:
        subgrid_cols = int(math.sqrt(num_cols))

    subgrids = []
    # Iterar sobre las filas y columnas del tablero en pasos del tamaño de las subgrillas
    for row in range(0, num_rows, subgrid_rows):
        for col in range(0, num_cols, subgrid_cols):
            # Crear una subgrilla
            subgrid = []
            for r in range(subgrid_rows):
                for c in range(subgrid_cols):
                    # Calcular el índice en el tablero y añadirlo a la subgrilla
                    index = (row + r) * num_cols + (col + c)
                    subgrid.append(index)
            # Añadir la subgrilla a la lista de subgrillas
            subgrids.append(tuple(subgrid))

    return subgrids


def convert_to_paulisumop(sparse_op):
    # Convertir SparsePauliOp a una lista de tuplas para PauliSumOp
    list_of_tuples = [(pauli.to_label(), coeff)
                      for pauli, coeff in zip(sparse_op.paulis, sparse_op.coeffs)]
    return PauliSumOp.from_list(list_of_tuples)


def sudoku_ansatz(rows, cols):
    num_qubits = rows * cols * QUBITS_PER_CELL
    qr = QuantumRegister(num_qubits)
    qc = QuantumCircuit(qr)
    params = [Parameter(f"θ{i}") for i in range(num_qubits)]

    # Bloque de puertas parametrizadas por fila
    for i in range(0, num_qubits, cols):
        for j in range(rows):
            qc.append(RYGate(params[i + j]), [i + j])
        for j in range(rows - 1):
            qc.append(CXGate(), [i + j, i + j + 1])

    # Bloque de puertas parametrizadas por columna
    for col in range(cols):
        for row in range(rows):
            qubit_idx = row * cols + col
            qc.append(RYGate(params[qubit_idx]), [qubit_idx])
        for row in range(cols - 1):
            qc.append(CXGate(), [(row * 4 + col), ((row + 1) * 4 + col)])

    # Entrelazamiento mejorado
    for i in range(rows):
        for j in range(cols):
            idx = i * cols + j
            qc.ry(params[idx], qr[idx])

            # Entrelazar dentro de la fila
            if j < cols - 1:
                qc.cx(qr[idx], qr[idx + 1])

            # Entrelazar dentro de la columna
            if i < rows - 1:
                qc.cx(qr[idx], qr[idx + cols])

    for subgrid in create_subgrids(rows, cols):
        for qubit_idx in subgrid:
            qc.append(RYGate(params[qubit_idx]), [qubit_idx])
        for i in range(len(subgrid) - 1):
            qc.append(CXGate(), [subgrid[i], subgrid[i+1]])

    return qc, params


def store_intermediate_result(eval_count, parameters, mean, std):
    global optimal_params
    optimal_params = parameters


if __name__ == '__main__':
    H = create_hamiltonian(ALPHA, SUDOKU_ROWS, QUBITS_PER_CELL, SUDOKU_COLS)

    H_converted = convert_to_paulisumop(H)

    backend = Aer.get_backend('qasm_simulator')

    quantum_instance = QuantumInstance(backend, shots=20000)

    optimizer = SPSA(maxiter=250)
    ansatz, params = sudoku_ansatz(SUDOKU_ROWS, SUDOKU_COLS)

    print(ansatz.draw())

    optimal_params = []
    vqe = VQE(ansatz, optimizer, quantum_instance=quantum_instance,
              callback=store_intermediate_result)

    result = vqe.compute_minimum_eigenvalue(H_converted)

    # Guardar los parámetros óptimos en un archivo
    with open('optimal_params.pkl', 'wb') as f:
        pickle.dump(optimal_params, f)

    # Preparar el estado cuántico óptimo
    optimal_circuit = ansatz.bind_parameters(optimal_params)
    # Añadir mediciones
    optimal_circuit.measure_all()

    # Realizar mediciones
    transpiled_circuit = transpile(optimal_circuit, backend)
    qobj = assemble(transpiled_circuit, backend, shots=20000)
    measurement_result = backend.run(qobj).result()
    counts = measurement_result.get_counts(optimal_circuit)

    # La configuración de qubits más probable es nuestra solución
    solution = max(counts, key=counts.get)

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
