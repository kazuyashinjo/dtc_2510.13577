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


qubits = 133
thetaJ = -0.5 * pi

backend_name = "ibm_torino"
num_steps = 51
n_shots = 2 ** 12
h_x_list = [0.99999, 0.975, 0.95, 0.9]

# [physical qubit, ancilla qubit]
zz_layer_r1 = [
    [22, 21], [16, 23], [26, 25], [17, 27], [30, 29], [18, 31],
    [41, 42], [45, 46], [49, 50],
    [60, 59], [54, 61], [64, 63], [55, 65], [56, 69],
    [77, 78], [81, 80], [83, 84], [74, 86],
    [98, 97], [100, 101], [93, 103], [106, 105], [94, 107],
]
zz_layer_r2 = [
    [34, 21], [24, 23], [35, 25], [28, 27], [36, 29], [32, 31],
    [43, 42], [47, 46], [51, 50],
    [72, 59], [62, 61], [73, 63], [66, 65], [68, 69],
    [79, 78], [92, 80], [85, 84], [87, 86],
    [110, 97], [102, 101], [104, 103], [112, 105], [108, 107],
]
zz_layer_b1 = [
    [20, 21], [24, 25], [26, 27], [18, 31],
    [34, 40], [41, 42], [43, 44], [36, 48], [49, 50],
    [58, 59], [60, 61], [55, 65], [66, 67], [68, 69],
    [79, 80], [73, 82], [85, 84], [87, 88],
    [96, 97], [92, 99], [100, 101], [102, 103], [94, 107],
]
zz_layer_b2 = [
    [22, 21], [35, 25], [28, 27], [30, 31],
    [39, 40], [54, 42], [45, 44], [47, 48], [56, 50],
    [72, 59], [62, 61], [64, 65], [74, 67], [70, 69],
    [81, 80], [83, 82], [93, 84], [89, 88],
    [110, 97], [98, 99], [111, 101], [104, 103], [106, 107],
]
zz_layer_g1 = [
    [20, 21], [16, 23], [24, 25], [28, 29],
    [39, 40], [43, 42], [35, 44], [47, 46], [36, 48],
    [58, 59], [62, 63], [66, 67], [56, 69],
    [72, 78], [73, 82], [83, 84], [74, 86], [87, 88],
    [96, 97], [92, 99], [102, 101], [104, 105], [106, 107],
]
zz_layer_g2 = [
    [34, 21], [22, 23], [26, 25], [30, 29],
    [41, 40], [54, 42], [45, 44], [55, 46], [49, 48],
    [60, 59], [64, 63], [68, 67], [70, 69],
    [79, 78], [81, 82], [93, 84], [85, 86], [94, 88],
    [98, 97], [100, 99], [111, 101], [112, 105], [108, 107],
]
zz_layer_y1 = [
    [22, 23], [17, 27], [28, 29], [30, 31],
    [34, 40], [35, 44], [45, 46], [47, 48], [51, 50],
    [54, 61], [62, 63], [64, 65], [68, 67],
    [72, 78], [79, 80], [81, 82], [85, 86], [89, 88],
    [98, 99], [93, 103], [104, 105],
]
zz_layer_y2 = [
    [24, 23], [26, 27], [36, 29], [32, 31],
    [41, 40], [43, 44], [55, 46], [49, 48], [56, 50],
    [60, 61], [73, 63], [66, 65], [74, 67],
    [77, 78], [92, 80], [83, 82], [87, 86], [94, 88],
    [100, 99], [102, 103], [106, 105],
]

initial_flip_list = []

physq_list = [
    16, 17, 18,
    20, 22, 24, 26, 28, 30, 32, 34, 35, 36,
    39, 41, 43, 45, 47, 49, 51,
    54, 55, 56,
    58, 60, 62, 64, 66, 68, 70, 72, 73, 74,
    77, 79, 81, 83, 85, 87, 89,
    92, 93, 94,
    96, 98, 100, 102, 104, 106, 108, 110, 111, 112,
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
