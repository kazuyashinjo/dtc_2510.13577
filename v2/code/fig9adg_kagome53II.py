"""
Floquet circuit construction for a kicked Ising model on the Kagome53-II lattice
implemented on IBM Quantum devices.

The layer definitions are written as:
    [physical_qubit, ancilla_qubit]

Physical qubits are connected through shared ancilla qubits.
Before running, set:
    export IBM_QUANTUM_TOKEN="..."
Optionally:
    export IBM_QUANTUM_INSTANCE="hub/group/project"
"""

import json
import os
from math import pi

from qiskit import QuantumCircuit
from qiskit.transpiler.preset_passmanagers import generate_preset_pass_manager
from qiskit_ibm_runtime import Batch, QiskitRuntimeService, SamplerV2


def add_rzz_mph_gates_withAncilla(qc: QuantumCircuit, layer1: list, layer2: list):
    for bond in layer1:
        qc.cx(bond[0], bond[1])

    for bond in layer2:
        qc.sdg(bond[0])
        qc.sdg(bond[1])
        qc.cz(bond[0], bond[1])

    for bond in layer1:
        qc.cx(bond[0], bond[1])


qubits = 127
thetaJ = -0.5 * pi

backend_name = "ibm_kyiv"
num_steps = 41
n_shots = 2 ** 14
h_x_list = [0.99999, 0.975, 0.95, 0.9]

# [physical qubit, ancilla qubit]
zz_layer_r1 = [
    [21, 20], [15, 22], [25, 24], [16, 26], [29, 28], [17, 30],
    [40, 41], [44, 45], [48, 49],
    [59, 58], [53, 60], [63, 62], [54, 64], [55, 68],
    [76, 77], [80, 79], [82, 83], [73, 85],
    [97, 96], [99, 100], [92, 102], [105, 104], [93, 106],
]
zz_layer_r2 = [
    [33, 20], [23, 22], [34, 24], [27, 26], [35, 28], [31, 30],
    [42, 41], [46, 45], [50, 49],
    [71, 58], [61, 60], [72, 62], [65, 64], [67, 68],
    [78, 77], [91, 79], [84, 83], [86, 85],
    [109, 96], [101, 100], [103, 102], [111, 104], [107, 106],
]
zz_layer_b1 = [
    [19, 20], [23, 24], [25, 26], [17, 30],
    [33, 39], [40, 41], [42, 43], [35, 47], [48, 49],
    [57, 58], [59, 60], [54, 64], [65, 66], [67, 68],
    [78, 79], [72, 81], [84, 83], [86, 87],
    [95, 96], [91, 98], [99, 100], [101, 102], [93, 106],
]
zz_layer_b2 = [
    [21, 20], [34, 24], [27, 26], [29, 30],
    [38, 39], [53, 41], [44, 43], [46, 47], [55, 49],
    [71, 58], [61, 60], [63, 64], [73, 66], [69, 68],
    [80, 79], [82, 81], [92, 83], [88, 87],
    [109, 96], [97, 98], [110, 100], [103, 102], [105, 106],
]
zz_layer_g1 = [
    [19, 20], [15, 22], [23, 24], [27, 28],
    [38, 39], [42, 41], [34, 43], [46, 45], [35, 47],
    [57, 58], [61, 62], [65, 66], [55, 68],
    [71, 77], [72, 81], [82, 83], [73, 85], [86, 87],
    [95, 96], [91, 98], [101, 100], [103, 104], [105, 106],
]
zz_layer_g2 = [
    [33, 20], [21, 22], [25, 24], [29, 28],
    [40, 39], [53, 41], [44, 43], [54, 45], [48, 47],
    [59, 58], [63, 62], [67, 66], [69, 68],
    [78, 77], [80, 81], [92, 83], [84, 85], [93, 87],
    [97, 96], [99, 98], [110, 100], [111, 104], [107, 106],
]
zz_layer_y1 = [
    [21, 22], [16, 26], [27, 28], [29, 30],
    [33, 39], [34, 43], [44, 45], [46, 47], [50, 49],
    [53, 60], [61, 62], [63, 64], [67, 66],
    [71, 77], [78, 79], [80, 81], [84, 85], [88, 87],
    [97, 98], [92, 102], [103, 104],
]
zz_layer_y2 = [
    [23, 22], [25, 26], [35, 28], [31, 30],
    [40, 39], [42, 43], [54, 45], [48, 47], [55, 49],
    [59, 60], [72, 62], [65, 64], [73, 66],
    [76, 77], [91, 79], [82, 81], [86, 85], [93, 87],
    [99, 98], [101, 102], [105, 104],
]

initial_flip_list = []

physq_list = [
    15, 16, 17,
    19, 21, 23, 25, 27, 29, 31, 33, 34, 35,
    38, 40, 42, 44, 46, 48, 50,
    53, 54, 55,
    57, 59, 61, 63, 65, 67, 69, 71, 72, 73,
    76, 78, 80, 82, 84, 86, 88,
    91, 92, 93,
    95, 97, 99, 101, 103, 105, 107, 109, 110, 111,
]


def get_backend():
    token = os.environ.get("IBM_QUANTUM_TOKEN")
    if not token:
        raise RuntimeError("Set IBM_QUANTUM_TOKEN before running this script.")

    instance = os.environ.get("IBM_QUANTUM_INSTANCE")
    if instance:
        QiskitRuntimeService.save_account(
            channel="ibm_quantum",
            token=token,
            instance=instance,
            overwrite=True,
        )
    else:
        QiskitRuntimeService.save_account(
            channel="ibm_quantum",
            token=token,
            overwrite=True,
        )

    service = QiskitRuntimeService()
    return service.backend(backend_name)


def check_layers():
    all_layers = [
        zz_layer_r1, zz_layer_r2,
        zz_layer_b1, zz_layer_b2,
        zz_layer_g1, zz_layer_g2,
        zz_layer_y1, zz_layer_y2,
    ]
    used_physq = sorted({bond[0] for layer in all_layers for bond in layer})
    if used_physq != sorted(physq_list):
        raise ValueError(
            "physq_list does not match the physical qubits used in the layer definitions."
        )


def main():
    check_layers()

    backend_p = get_backend()
    pm = generate_preset_pass_manager(optimization_level=0, target=backend_p.target)

    print(backend_name)

    with Batch(backend=backend_p):
        for h_x in h_x_list:
            h_x *= pi

            trotter_layer = QuantumCircuit(qubits)
            for j in physq_list:
                trotter_layer.rx(h_x, j)

            add_rzz_mph_gates_withAncilla(trotter_layer, zz_layer_r1, zz_layer_r2)
            add_rzz_mph_gates_withAncilla(trotter_layer, zz_layer_b1, zz_layer_b2)
            add_rzz_mph_gates_withAncilla(trotter_layer, zz_layer_g1, zz_layer_g2)
            add_rzz_mph_gates_withAncilla(trotter_layer, zz_layer_y1, zz_layer_y2)

            print("Hx =", h_x)
            print("thetaJ =", thetaJ)
            print("initial flip at", initial_flip_list)

            trotter_circuit_list = []
            for i in range(num_steps):
                trotter_circuit = QuantumCircuit(qubits)

                for j in initial_flip_list:
                    trotter_circuit.x(j)

                for _ in range(i):
                    trotter_circuit = trotter_circuit.compose(trotter_layer)

                trotter_circuit.measure_all()
                trotter_circuit = pm.run(trotter_circuit)
                trotter_circuit_list.append(trotter_circuit)
                print(f"Trotter circuit with {i} Trotter steps")

            print("Gate counts:")
            gate_counts = trotter_circuit_list[-1].count_ops()
            for gate_name, count in gate_counts.items():
                print(f"{gate_name}: {count}")

            jobs = []
            sampler = SamplerV2()
            sampler.options.default_shots = n_shots

            for trotter_circuit in trotter_circuit_list:
                job = sampler.run([trotter_circuit])
                print("job id:", job.job_id())
                jobs.append(job)

            data = {
                "backend": backend_name,
                "shots": n_shots,
                "trotter_steps": num_steps,
                "gate_counts": [(gate_name, count) for gate_name, count in gate_counts.items()],
                "job_id": [job.job_id() for job in jobs],
            }

            file_path = (
                "thetaJ"
                + str(round(thetaJ / pi, 3))
                + "_thetaX"
                + str(round(h_x / pi, 3))
                + ".json"
            )
            with open(file_path, "w", encoding="utf-8") as fp:
                fp.write(json.dumps(data, indent=4))


if __name__ == "__main__":
    main()
