"""BB84 simulado em Qiskit: QBER sob ruído de canal e sob ataque intercepta-reenvia.

Cada qubit da Alice depende de (bit, base_A, base_B[, base_E]). Em vez de montar um
circuito por qubit, montamos um circuito por combinação e rodamos com tantos shots
quantos qubits caíram naquela combinação; o resultado é o mesmo e é muito mais rápido.

Canal: erro despolarizante de 1 qubit com probabilidade p entre Alice e Bob.
Eva (opcional): mede numa base aleatória e reenvia o estado que obteve.
Taxa de chave assintótica (Shor-Preskill): r = 1 - 2 h(QBER); chave só existe se QBER < ~11%.
"""
import argparse
import csv
import itertools
import math
import os
import numpy as np
from qiskit import QuantumCircuit
from qiskit_aer import AerSimulator
from qiskit_aer.noise import depolarizing_error

SIM = AerSimulator()


def circuito(bit, base_a, base_b, base_e=None, p=0.0):
    qc = QuantumCircuit(1, 1)
    if bit:
        qc.x(0)
    if base_a:  # base X (diagonal)
        qc.h(0)
    if base_e is not None:  # Eva mede na base dela; a medição colapsa e o estado segue (reenvio)
        if base_e:
            qc.h(0)
        qc.measure(0, 0)
        if base_e:
            qc.h(0)
    if p > 0:
        qc.append(depolarizing_error(p, 1), [0])
    if base_b:
        qc.h(0)
    qc.measure(0, 0)
    return qc


def rodar(n, p=0.0, eva=False, rng=None):
    rng = rng or np.random.default_rng()
    bits = rng.integers(0, 2, n)
    ba = rng.integers(0, 2, n)
    bb = rng.integers(0, 2, n)
    be = rng.integers(0, 2, n) if eva else np.full(n, -1)
    erros = 0
    sifted = 0
    for combo in itertools.product([0, 1], [0, 1], [0, 1], [0, 1] if eva else [-1]):
        bit, a, b, e = combo
        if a != b:  # descartado no sifting, não precisa simular
            continue
        k = int(np.sum((bits == bit) & (ba == a) & (bb == b) & (be == e)))
        if k == 0:
            continue
        qc = circuito(bit, a, b, None if e < 0 else e, p)
        counts = SIM.run(qc, shots=k, seed_simulator=int(rng.integers(1 << 31))).result().get_counts()
        erros += counts.get(str(1 - bit), 0)
        sifted += k
    return sifted, erros


def h2(x):
    return 0.0 if x <= 0 or x >= 1 else -x * math.log2(x) - (1 - x) * math.log2(1 - x)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=20000)
    ap.add_argument("--seed", type=int, default=2026)
    args = ap.parse_args()
    rng = np.random.default_rng(args.seed)
    os.makedirs("results", exist_ok=True)
    linhas = []
    for eva in (False, True):
        for p in (0.0, 0.02, 0.05, 0.1, 0.15, 0.2):
            s, e = rodar(args.n, p, eva, rng)
            qber = e / s
            linhas.append(dict(eva=int(eva), p=p, sifted=s, qber=round(qber, 4),
                               taxa_chave=round(max(0.0, 1 - 2 * h2(qber)), 4)))
            print(linhas[-1])
    with open("results/bb84.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=linhas[0].keys())
        w.writeheader()
        w.writerows(linhas)


if __name__ == "__main__":
    main()
