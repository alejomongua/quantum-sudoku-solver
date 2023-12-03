import matplotlib.pyplot as plt
import numpy as np

from qiskit import Aer, QuantumCircuit, ClassicalRegister, QuantumRegister, execute
from qiskit.quantum_info import Statevector

from qiskit.visualization import plot_histogram
from sympy import plot


def XOR(qc, a, b, output):
    qc.cx(a, output)
    qc.cx(b, output)


def sudoku_oracle(qc, clause_list, var_qubits, clause_qubits, output_qubit):
    i = 0
    for clause in clause_list:
        XOR(qc, var_qubits[clause[0]], var_qubits[clause[1]], clause_qubits[i])
        i += 1

    qc.mcx(clause_qubits, output_qubit)

    i = 0
    for clause in clause_list:
        XOR(qc, var_qubits[clause[0]], var_qubits[clause[1]], clause_qubits[i])
        i += 1


def diffuser(nqubits):
    qc = QuantumCircuit(nqubits)
    for qubit in range(nqubits):
        qc.h(qubit)
    for qubit in range(nqubits):
        qc.x(qubit)
    qc.h(nqubits-1)
    qc.mct(list(range(nqubits-1)), nqubits-1)
    qc.h(nqubits-1)
    for qubit in range(nqubits):
        qc.x(qubit)
    for qubit in range(nqubits):
        qc.h(qubit)
    U_s = qc.to_gate()
    U_s.name = "U$_s$"
    return U_s


def main():
    clause_list = ((0, 1), (0, 2), (1, 3), (2, 3))
    var_qubits = QuantumRegister(4, name='v')
    clause_qubits = QuantumRegister(4, name='c')
    output_qubit = QuantumRegister(1, name='out')
    c_bits = ClassicalRegister(4, name='cbits')
    qc = QuantumCircuit(var_qubits, clause_qubits, output_qubit, c_bits)

    sudoku_oracle(qc, clause_list, var_qubits, clause_qubits, output_qubit)

    qc.initialize([1, -1]/np.sqrt(2), output_qubit)  # type: ignore

    qc.h(var_qubits)
    qc.barrier()

    sudoku_oracle(qc, clause_list, var_qubits, clause_qubits, output_qubit)

    qc.barrier()
    qc.append(diffuser(4), [0, 1, 2, 3])

    sudoku_oracle(qc, clause_list, var_qubits, clause_qubits, output_qubit)
    qc.barrier()

    qc.append(diffuser(4), [0, 1, 2, 3])

    qc.measure(var_qubits, c_bits)

    qc.draw(output='mpl')

    plt.show()

    backend = Aer.get_backend('qasm_simulator')
    job = execute(qc, backend, shots=1000)
    result = job.result()
    counts = result.get_counts()
    plot_histogram(counts)
    plt.show()


if __name__ == '__main__':
    main()
