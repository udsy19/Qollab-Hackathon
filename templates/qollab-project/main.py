"""FILL: project name — one line on what it does. On Qollab: press Run on Qollab, pick a simulator, press Run."""
from qiskit import QuantumCircuit, transpile

try:
    backend  # Qollab pre-creates this from the Select QPU dialog; never replace it on Qollab
except NameError:  # off Qollab (local dev only): Qiskit's built-in simulator
    from qiskit.providers.basic_provider import BasicSimulator
    backend = BasicSimulator()


def build_circuit() -> QuantumCircuit:
    qc = QuantumCircuit(2)
    qc.h(0)
    qc.cx(0, 1)
    qc.measure_all()
    return qc


# Qollab calls main() itself and turns its parameters into a Run settings form. The signature must stay on ONE
# line at column 0 with every parameter annotated int/float/str/bool, or main() is silently never called.
# Never call main() from this file: on an IonQ backend a second call would be a second job and fail the run.
def main(shots: int = 1024):
    circuit = transpile(build_circuit(), backend)
    # ONE backend.run per run: IonQ backends accept exactly one job per run. Batch circuits into this call.
    counts = backend.run(circuit, shots=shots).result().get_counts()
    print(counts)
