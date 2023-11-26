import math
import os
import sys
import pickle

from qiskit import IBMQ, transpile, assemble
from qiskit.utils import QuantumInstance
from qiskit.circuit import Parameter, QuantumCircuit
from qiskit.circuit.library import RYGate, CXGate
from qiskit.algorithms import VQE
from qiskit.algorithms.optimizers import SPSA
from qiskit.opflow import PauliSumOp


from restrictions import QUBITS_PER_NUMBER, create_hamiltonian

SUDOKU_ROWS = 4
SUDOKU_COLS = 4
ALPHA = 1000
TOTAL_QUBITS = SUDOKU_COLS * SUDOKU_ROWS * QUBITS_PER_NUMBER


def convert_to_paulisumop(sparse_op):
    # Convertir SparsePauliOp a una lista de tuplas para PauliSumOp
    list_of_tuples = [(pauli.to_label(), coeff)
                      for pauli, coeff in zip(sparse_op.paulis, sparse_op.coeffs)]
    return PauliSumOp.from_list(list_of_tuples)


def sudoku_ansatz(sudoku_rows, sudoku_cols):
    num_qubits = sudoku_rows * sudoku_cols
    qc = QuantumCircuit(num_qubits)
    params = [Parameter(f"θ{i}") for i in range(num_qubits)]

    # Bloque de puertas parametrizadas por fila
    for row in range(sudoku_rows):
        row_start = row * sudoku_cols
        for col in range(sudoku_cols):
            qc.append(RYGate(params[row_start + col]), [row_start + col])
        for col in range(sudoku_cols - 1):
            qc.append(CXGate(), [row_start + col, row_start + col + 1])

    # Bloque de puertas parametrizadas por columna
    for col in range(sudoku_cols):
        for row in range(sudoku_rows):
            qubit_idx = row * sudoku_cols + col
            qc.append(RYGate(params[qubit_idx]), [qubit_idx])
        for row in range(sudoku_rows - 1):
            qc.append(CXGate(), [(row * sudoku_cols + col),
                      ((row + 1) * sudoku_cols + col)])

    # Bloques para subcuadrículas
    subgrid_size = int(math.sqrt(sudoku_cols))
    for subgrid_row in range(0, sudoku_rows, subgrid_size):
        for subgrid_col in range(0, sudoku_cols, subgrid_size):
            subgrid_qubits = []
            for i in range(subgrid_size):
                for j in range(subgrid_size):
                    qubit_idx = (subgrid_row + i) * \
                        sudoku_cols + (subgrid_col + j)
                    subgrid_qubits.append(qubit_idx)
                    qc.append(RYGate(params[qubit_idx]), [qubit_idx])
            for i in range(len(subgrid_qubits) - 1):
                qc.append(CXGate(), [subgrid_qubits[i], subgrid_qubits[i+1]])

    return qc, params


def store_intermediate_result(eval_count, parameters, mean, std):
    global optimal_params
    optimal_params = parameters


if __name__ == '__main__':
    # Agregar el directorio padre al path para poder importar el archivo config.py
    parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    sys.path.append(parent_dir)

    from config import api_key

    H = create_hamiltonian(ALPHA, SUDOKU_ROWS, SUDOKU_COLS)

    H_converted = convert_to_paulisumop(H)

    # Cargar la cuenta de IBM Q
    IBMQ.save_account(api_key, overwrite=True)
    IBMQ.load_account()

    provider = IBMQ.get_provider(hub='ibm-q')
    backend = provider.get_backend('ibmq_qasm_simulator')

    quantum_instance = QuantumInstance(backend, shots=20000)

    optimizer = SPSA(maxiter=250)
    ansatz, params = sudoku_ansatz(SUDOKU_ROWS, SUDOKU_COLS)

    optimal_params = []
    vqe = VQE(ansatz, optimizer, quantum_instance=quantum_instance,
              callback=store_intermediate_result)

    result = vqe.compute_minimum_eigenvalue(H_converted)

    # Guardar los parámetros óptimos en un archivo
    with open('optimal_params.pkl', 'wb') as f:
        pickle.dump(optimal_params, f)

    # Guardar los resultados en un archivo
    with open('result.pkl', 'wb') as f:
        pickle.dump(result, f)

    # Guardar params en un archivo
    with open('params.pkl', 'wb') as f:
        pickle.dump(params, f)

    # Preparar el estado cuántico óptimo
    optimal_circuit = ansatz.bind_parameters(optimal_params)

    # Realizar mediciones
    transpiled_circuit = transpile(optimal_circuit, backend)
    qobj = assemble(transpiled_circuit, backend)
    measurement_result = backend.run(qobj).result()
    counts = measurement_result.get_counts(optimal_circuit)

    # La configuración de qubits más probable es nuestra solución
    solution = max(counts, key=counts.get)

    # Decodificar la solución en formato de Sudoku
    sudoku_solution = []
    for i in range(SUDOKU_COLS * SUDOKU_ROWS):
        bits = solution[i * QUBITS_PER_NUMBER: (i + 1) * QUBITS_PER_NUMBER]
        # Convertir de binario a decimal y ajustar el rango 1-4
        number = int(bits, 2) + 1
        sudoku_solution.append(number)

    # Reorganizar la solución en formato de matriz SUDOKU_ROWS x SUDOKU_COLS
    sudoku_matrix = [sudoku_solution[i:i + SUDOKU_COLS]
                     for i in range(0, len(sudoku_solution), SUDOKU_ROWS)]

    # Imprimir la solución del Sudoku
    for row in sudoku_matrix:
        print(" ".join(map(str, row)))

    print(result)
