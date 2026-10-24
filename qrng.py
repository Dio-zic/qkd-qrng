"""QRNG em Qiskit: Hadamard + medição, com viés de leitura e extração de von Neumann.

Gera bits ideais e com erro de leitura assimétrico (0->1 com prob. r01, 1->0 com r10),
aplica o extrator de von Neumann e roda testes estatísticos simples inspirados no
NIST SP 800-22 (monobit, runs) e um qui-quadrado sobre bytes.
"""
import argparse
import csv
import math
import os
import numpy as np
from scipy import stats
from scipy.special import erfc
from qiskit import QuantumCircuit
from qiskit_aer import AerSimulator
from qiskit_aer.noise import NoiseModel, ReadoutError


def gerar(n_bits, r01=0.0, r10=0.0, seed=None, largura=16):
    """largura qubits em paralelo, memory=True para manter a ordem dos bits."""
    qc = QuantumCircuit(largura, largura)
    qc.h(range(largura))
    qc.measure(range(largura), range(largura))
    nm = None
    if r01 or r10:
        nm = NoiseModel()
        nm.add_all_qubit_readout_error(ReadoutError([[1 - r01, r01], [r10, 1 - r10]]))
    sim = AerSimulator(noise_model=nm)
    shots = math.ceil(n_bits / largura)
    mem = sim.run(qc, shots=shots, memory=True, seed_simulator=seed).result().get_memory()
    return np.array([int(c) for s in mem for c in s], dtype=np.uint8)[:n_bits]


def von_neumann(bits):
    pares = bits[: len(bits) // 2 * 2].reshape(-1, 2)
    ok = pares[:, 0] != pares[:, 1]
    return pares[ok, 0]


def monobit(bits):
    s = np.sum(2 * bits.astype(int) - 1)
    return erfc(abs(s) / math.sqrt(len(bits)) / math.sqrt(2))


def runs(bits):
    n = len(bits)
    pi = bits.mean()
    if abs(pi - 0.5) >= 2 / math.sqrt(n):
        return 0.0
    v = 1 + np.count_nonzero(bits[1:] != bits[:-1])
    return erfc(abs(v - 2 * n * pi * (1 - pi)) / (2 * math.sqrt(2 * n) * pi * (1 - pi)))


def qui2_bytes(bits):
    b = np.packbits(bits[: len(bits) // 8 * 8])
    obs = np.bincount(b, minlength=256)
    return stats.chisquare(obs).pvalue


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=200000)
    ap.add_argument("--seed", type=int, default=2026)
    args = ap.parse_args()
    os.makedirs("results", exist_ok=True)
    linhas = []
    for nome, r01, r10 in [("ideal", 0, 0), ("leitura 2%/5%", 0.02, 0.05), ("leitura 5%/15%", 0.05, 0.15)]:
        bruto = gerar(args.n, r01, r10, args.seed)
        for etapa, bits in (("bruto", bruto), ("von Neumann", von_neumann(bruto))):
            l = dict(cenario=nome, etapa=etapa, n=len(bits), frac_uns=round(float(bits.mean()), 4),
                     p_monobit=round(float(monobit(bits)), 4), p_runs=round(float(runs(bits)), 4),
                     p_qui2_bytes=round(float(qui2_bytes(bits)), 4))
            linhas.append(l)
            print(l)
    with open("results/qrng.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=linhas[0].keys())
        w.writeheader()
        w.writerows(linhas)


if __name__ == "__main__":
    main()
