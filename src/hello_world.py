import os
import sys

from matplotlib import pyplot as plt
from qiskit.visualization import plot_histogram
from qiskit.providers.ibmq import least_busy
from qiskit import QuantumCircuit, execute, IBMQ

if __name__ == '__main__':
    # Agregar el directorio padre al path para poder importar el archivo config.py
    parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    sys.path.append(parent_dir)

    from config import api_key

    # Cargar la cuenta de IBM Q
    IBMQ.save_account(api_key, overwrite=True)
    IBMQ.load_account()

    # Crear un circuito cuántico simple
    qc = QuantumCircuit(2, 2)
    qc.h(0)
    qc.cx(0, 1)
    qc.measure([0, 1], [0, 1])

    # Obtener el backend menos ocupado
    provider = IBMQ.get_provider(hub='ibm-q')
    # ejemplo de backend, elige uno disponible
    backend = least_busy(provider.backends(filters=lambda x: x.configuration().n_qubits >= 2
                                           and not x.configuration().simulator
                                           and x.status().operational == True))

    job = execute(qc, backend)
    result = job.result()

    # Imprimir los resultados
    counts = result.get_counts(qc)
    print("\nTotal counts are:", counts)

    plot_histogram(counts)
    plt.show()
