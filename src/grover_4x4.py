import matplotlib.pyplot as plt
import numpy as np

from qiskit import Aer, QuantumCircuit, ClassicalRegister, QuantumRegister, execute
from qiskit.quantum_info import Statevector

from qiskit.visualization import plot_histogram
from sympy import plot


def XOR(qc, a, b, output):
    qc.cx(a, output)
    qc.cx(b, output)


def apply_xor_for_number(qc, row_qubits, clause_qubits, number, clause_idx_start, auxiliary_qubits):
    """
    Aplica puertas XOR para verificar la presencia de un número específico en los qubits de una fila.

    Args:
        qc (QuantumCircuit): El circuito cuántico donde se aplican las puertas.
        row_qubits (QuantumRegister): Los qubits que representan una fila específica.
        clause_qubits (QuantumRegister): Los qubits de cláusula para la verificación.
        number (int): El número (0 a 3) a verificar en la fila.
        clause_idx_start (int): El índice inicial del qubit de cláusula a utilizar.
        auxiliary_qubits (QuantumRegister): Los qubits auxiliares para la verificación.
    """
    # Conversión del número a su representación binaria
    num_bin = format(number, '02b')

    # Aplicar XOR y mcx para cada celda en la fila
    for i in range(4):  # 4 celdas en una fila
        cell_qubits = row_qubits[2*i:2*i+2]
        for j in range(2):
            if num_bin[j] == '0':
                qc.x(cell_qubits[j])

        # Aplicar puertas XOR con los qubits de cláusula
        qc.mcx(cell_qubits, clause_qubits[clause_idx_start + i])

        # Revertir las puertas X si fueron aplicadas
        for j in range(2):
            if num_bin[j] == '0':
                qc.x(cell_qubits[j])

    # Verificar si exactamente uno de los qubits de cláusula está activado
    # Para simplificar, consideraremos que solo necesitamos verificar si hay una activación entre los qubits de cláusula
    # Aquí podría ir una lógica más compleja para sumar y verificar los qubits de cláusula
    # Por ejemplo, podríamos usar puertas adicionales para realizar esta operación
    qc.mcx(
        clause_qubits[clause_idx_start:clause_idx_start + 4], auxiliary_qubits[0])

    # Restablecer qubits de cláusula
    for i in range(4):
        qc.reset(clause_qubits[clause_idx_start + i])

    # Restablecer qubits auxiliares
    qc.reset(auxiliary_qubits[0])


def check_rows(qc, var_qubits, clause_qubits, auxiliary_qubits, output_qubit):
    """
    Verifica que cada número aparezca exactamente una vez en cada fila.

    Args:
        qc (QuantumCircuit): El circuito cuántico en el que se aplica la verificación.
        var_qubits (QuantumRegister): Los qubits que representan las celdas del sudoku.
        clause_qubits (QuantumRegister): Los qubits utilizados para las cláusulas de verificación.
        auxiliary_qubits (QuantumRegister): Los qubits auxiliares para la verificación.
        output_qubit (QuantumRegister): El qubit de salida que indica si se cumplen las condiciones.
    """
    for i in range(4):  # Hay 4 filas en un sudoku de 4x4
        # Selecciona los 8 qubits que representan una fila
        row_qubits = var_qubits[2*i*4:2*(i+1)*4]

        for num in range(4):  # Cada número del 0 al 3
            clause_idx_start = i * 4 + num * 16  # Índice para los qubits de cláusula
            apply_xor_for_number(qc, row_qubits, clause_qubits,
                                 num, clause_idx_start, auxiliary_qubits)

        # Lógica para marcar el qubit de salida si se cumplen todas las condiciones de la fila
        # Suponiendo que tenemos un qubit de cláusula adicional para cada fila
        qc.mcx(clause_qubits[i*16:(i+1)*16], output_qubit)

    # Restablecer qubits de cláusula si es necesario
    for i in range(64):  # Número total de qubits de cláusula utilizados
        qc.reset(clause_qubits[i])


def check_columns(qc, var_qubits, clause_qubits, auxiliary_qubits, output_qubit):
    """
    Verifica que cada número aparezca exactamente una vez en cada columna.

    Args:
        qc (QuantumCircuit): El circuito cuántico en el que se aplica la verificación.
        var_qubits (QuantumRegister): Los qubits que representan las celdas del sudoku.
        clause_qubits (QuantumRegister): Los qubits utilizados para las cláusulas de verificación.
        auxiliary_qubits (QuantumRegister): Los qubits auxiliares para la verificación.
        output_qubit (QuantumRegister): El qubit de salida que indica si se cumplen las condiciones.
    """
    for i in range(4):  # Hay 4 columnas en un sudoku de 4x4
        # Seleccionar los qubits que representan una columna
        column_qubits = [var_qubits[2*j + i*2]
                         for j in range(4)] + [var_qubits[2*j + 1 + i*2] for j in range(4)]

        for num in range(4):  # Cada número del 0 al 3
            # Índice para los qubits de cláusula (asumiendo 256 para columnas)
            clause_idx_start = 256 + i * 4 + num * 16
            apply_xor_for_number(
                qc, column_qubits, clause_qubits, num, clause_idx_start, auxiliary_qubits)

        # Lógica para marcar el qubit de salida si se cumplen todas las condiciones de la columna
        qc.mcx(clause_qubits[256 + i*16:256 + (i+1)*16], output_qubit)

    # Restablecer qubits de cláusula si es necesario
    for i in range(256, 512):  # Número total de qubits de cláusula utilizados para columnas
        qc.reset(clause_qubits[i])


def check_blocks(qc, var_qubits, clause_qubits, auxiliary_qubits, output_qubit):
    """
    Verifica que cada número aparezca exactamente una vez en cada bloque de 2x2.

    Args:
        qc (QuantumCircuit): El circuito cuántico en el que se aplica la verificación.
        var_qubits (QuantumRegister): Los qubits que representan las celdas del sudoku.
        clause_qubits (QuantumRegister): Los qubits utilizados para las cláusulas de verificación.
        auxiliary_qubits (QuantumRegister): Los qubits auxiliares para la verificación.
        output_qubit (QuantumRegister): El qubit de salida que indica si se cumplen las condiciones.
    """
    for i in range(2):  # Dos filas de bloques
        for j in range(2):  # Dos columnas de bloques
            # Seleccionar los qubits que representan un bloque de 2x2
            block_qubits = [var_qubits[2*row + col + 4*i + 8*j]
                            for row in range(2) for col in range(2)]

            for num in range(4):  # Cada número del 0 al 3
                # Índice para los qubits de cláusula (asumiendo 512 para bloques)
                clause_idx_start = 512 + (i*2 + j) * 4 + num * 16
                apply_xor_for_number(
                    qc, block_qubits, clause_qubits, num, clause_idx_start, auxiliary_qubits)

            # Lógica para marcar el qubit de salida si se cumplen todas las condiciones del bloque
            qc.mcx(clause_qubits[512 + (i*2 + j) *
                   16:512 + (i*2 + j + 1)*16], output_qubit)

    # Restablecer qubits de cláusula si es necesario
    for i in range(512, 768):  # Número total de qubits de cláusula utilizados para bloques
        qc.reset(clause_qubits[i])


def sudoku_oracle(qc, auxiliary_qubits, var_qubits, clause_qubits, output_qubit):
    # Implementar verificaciones de filas, columnas y bloques
    check_rows(qc, var_qubits, clause_qubits, auxiliary_qubits, output_qubit)
    check_columns(qc, var_qubits, clause_qubits,
                  auxiliary_qubits, output_qubit)
    check_blocks(qc, var_qubits, clause_qubits, auxiliary_qubits, output_qubit)

    return qc


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
    # 16 celdas * 2 qubits por celda
    var_qubits = QuantumRegister(32, name='v')
    clause_qubits = QuantumRegister(768, name='c')  # 768 qubits para cláusulas
    output_qubit = QuantumRegister(1, name='out')  # 1 qubit de salida
    auxiliary_qubits = QuantumRegister(8, name='aux')  # 8 qubits auxiliares
    c_bits = ClassicalRegister(32, name='cbits')

    qc = QuantumCircuit(var_qubits, clause_qubits,
                        auxiliary_qubits, output_qubit)

    sudoku_oracle(qc, auxiliary_qubits, var_qubits,
                  clause_qubits, output_qubit)

    qc.initialize([1, -1]/np.sqrt(2), output_qubit)  # type: ignore

    qc.h(var_qubits)
    qc.barrier()

    sudoku_oracle(qc, auxiliary_qubits, var_qubits,
                  clause_qubits, output_qubit)

    qc.barrier()
    qc.append(diffuser(4), [0, 1, 2, 3])

    sudoku_oracle(qc, auxiliary_qubits, var_qubits,
                  clause_qubits, output_qubit)
    qc.barrier()

    qc.append(diffuser(4), [0, 1, 2, 3])

    qc.measure(var_qubits, c_bits)

    qc.draw(output='mpl')

    plt.show()

    # Este circuito no es posible ejecutarlo con la tecnología actual
    # ya que el número de qubits es demasiado grande, por eso no se
    # incluye la ejecución del circuito.


if __name__ == '__main__':
    main()
