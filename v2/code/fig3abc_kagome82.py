"""
Floquet circuit construction for a kicked Ising model on the Kagome82 lattice
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


qubits = 156
thetaJ = -0.5 * pi

backend_name = "ibm_marrakesh"
num_steps = 5
n_shots = 2 ** 12
h_x_list = [0.99999, 0.95, 0.9, 0.85, 0.8, 0.7]

# [physical qubit, ancilla qubit]
zz_layer_r1 = [
    [6, 7], [10, 11],
    [16, 23], [17, 27], [18, 31], [19, 35],
    [24, 25], [28, 29], [32, 33],
    [42, 43], [46, 47], [50, 51],
    [56, 63], [57, 67], [58, 71], [59, 75],
    [64, 65], [68, 69], [72, 73],
    [82, 83], [86, 87], [90, 91],
    [96, 103], [97, 107], [98, 111], [99, 115],
    [104, 105], [108, 109], [112, 113],
    [122, 123], [126, 127], [130, 131],
    [137, 147], [138, 151], [139, 155],
]
zz_layer_r2 = [
    [8, 7], [12, 11],
    [22, 23], [26, 27], [30, 31], [34, 35],
    [37, 25], [38, 29], [39, 33],
    [44, 43], [48, 47], [52, 51],
    [62, 63], [66, 67], [70, 71], [74, 75],
    [77, 65], [78, 69], [79, 73],
    [84, 83], [88, 87], [92, 91],
    [102, 103], [106, 107], [110, 111], [114, 115],
    [117, 105], [118, 109], [119, 113],
    [124, 123], [128, 127], [132, 131],
    [146, 147], [150, 151], [154, 155],
]
zz_layer_b1 = [
    [4, 5], [8, 9], [12, 13],
    [16, 23], [17, 27], [18, 31],
    [22, 21], [26, 25], [30, 29], [34, 33],
    [44, 45], [48, 49], [52, 53],
    [56, 63], [57, 67], [58, 71],
    [62, 61], [66, 65], [70, 69], [74, 73],
    [84, 85], [88, 89], [92, 93],
    [96, 103], [97, 107], [98, 111],
    [102, 101], [106, 105], [110, 109], [114, 113],
    [124, 125], [128, 129], [132, 133],
    [136, 143], [137, 147], [138, 151],
]
zz_layer_b2 = [
    [6, 5], [10, 9], [14, 13],
    [24, 23], [28, 27], [32, 31],
    [36, 21], [37, 25], [38, 29], [39, 33],
    [46, 45], [50, 49], [54, 53],
    [64, 63], [68, 67], [72, 71],
    [76, 61], [77, 65], [78, 69], [79, 73],
    [86, 85], [90, 89], [94, 93],
    [104, 103], [108, 107], [112, 111],
    [116, 101], [117, 105], [118, 109], [119, 113],
    [126, 125], [130, 129], [134, 133],
    [144, 143], [148, 147], [152, 151],
]
zz_layer_g1 = [
    [4, 3], [8, 7], [12, 11],
    [22, 23], [26, 27], [30, 31],
    [36, 41], [37, 45], [38, 49], [39, 53],
    [44, 43], [48, 47], [52, 51],
    [62, 63], [66, 67], [70, 71],
    [76, 81], [77, 85], [78, 89], [79, 93],
    [84, 83], [88, 87], [92, 91],
    [102, 103], [106, 107], [110, 111],
    [116, 121], [117, 125], [118, 129], [119, 133],
    [124, 123], [128, 127], [132, 131],
    [146, 147], [150, 151],
]
zz_layer_g2 = [
    [16, 3], [17, 7], [18, 11],
    [24, 23], [28, 27], [32, 31],
    [42, 41], [46, 45], [50, 49], [54, 53],
    [56, 43], [57, 47], [58, 51],
    [64, 63], [68, 67], [72, 71],
    [82, 81], [86, 85], [90, 89], [94, 93],
    [96, 83], [97, 87], [98, 91],
    [104, 103], [108, 107], [112, 111],
    [122, 121], [126, 125], [130, 129], [134, 133],
    [136, 123], [137, 127], [138, 131],
    [148, 147], [152, 151],
]
zz_layer_y1 = [
    [6, 7], [10, 11], [14, 15],
    [24, 25], [28, 29], [32, 33],
    [37, 45], [38, 49], [39, 53],
    [42, 43], [46, 47], [50, 51], [54, 55],
    [64, 65], [68, 69], [72, 73],
    [77, 85], [78, 89], [79, 93],
    [82, 83], [86, 87], [90, 91], [94, 95],
    [104, 105], [108, 109], [112, 113],
    [117, 125], [118, 129], [119, 133],
    [122, 123], [126, 127], [130, 131], [134, 135],
    [144, 145], [148, 149], [152, 153],
]
zz_layer_y2 = [
    [17, 7], [18, 11], [19, 15],
    [26, 25], [30, 29], [34, 33],
    [44, 45], [48, 49], [52, 53],
    [56, 43], [57, 47], [58, 51], [59, 55],
    [66, 65], [70, 69], [74, 73],
    [84, 85], [88, 89], [92, 93],
    [96, 83], [97, 87], [98, 91], [99, 95],
    [106, 105], [110, 109], [114, 113],
    [124, 125], [128, 129], [132, 133],
    [136, 123], [137, 127], [138, 131], [139, 135],
    [146, 145], [150, 149], [154, 153],
]

initial_flip_list = []

physq_list = [
    4, 6, 8, 10, 12, 14,
    16, 17, 18, 19,
    22, 24, 26, 28, 30, 32, 34,
    36, 37, 38, 39,
    42, 44, 46, 48, 50, 52, 54,
    56, 57, 58, 59,
    62, 64, 66, 68, 70, 72, 74,
    76, 77, 78, 79,
    82, 84, 86, 88, 90, 92, 94,
    96, 97, 98, 99,
    102, 104, 106, 108, 110, 112, 114,
    116, 117, 118, 119,
    122, 124, 126, 128, 130, 132, 134,
    136, 137, 138, 139,
    144, 146, 148, 150, 152, 154,
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
            gate_counts = trotter_circuit_list[1].count_ops()
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
