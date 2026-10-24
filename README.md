# qkd_qrng: BB84 e QRNG simulados em Qiskit

Mini-projeto complementar ao `wfc_bench`, voltado a redes e criptografia quânticas.

| Arquivo | Conteúdo |
|---|---|
| `bb84.py` | Protocolo BB84 com canal despolarizante e ataque intercepta-reenvia; mede QBER e taxa de chave assintótica (1 − 2h(QBER)) |
| `qrng.py` | Gerador quântico de números aleatórios (Hadamard + medição) com erro de leitura assimétrico, extrator de von Neumann e testes inspirados no NIST SP 800-22 |
| `results/` | `bb84.csv`, `qrng.csv` |

```bash
pip install qiskit qiskit-aer numpy scipy
python bb84.py   # ~1 min
python qrng.py   # ~10 s
```

## Resultados (semente 2026)

**BB84, 20 000 qubits enviados (~10 000 após sifting)**

| p (despolarizante) | QBER sem Eva | taxa de chave | QBER com Eva |
|---|---|---|---|
| 0 | 0,000 | 1,00 | 0,250 |
| 0,05 | 0,026 | 0,65 | 0,267 |
| 0,10 | 0,051 | 0,42 | 0,270 |
| 0,20 | 0,101 | 0,06 | 0,303 |

- Sem Eva, QBER ≈ p/2, como a teoria prevê para o canal despolarizante; a chave some perto de QBER ≈ 11%.
- O ataque intercepta-reenvia produz QBER ≈ 25% mesmo num canal perfeito, então é sempre detectado.

**QRNG, 200 000 bits**

- No caso ideal, os bits passam nos testes monobit, runs e qui-quadrado.
- Com erro de leitura assimétrico (2%/5% ou 5%/15%), o viés aparece (fração de uns 0,48 e 0,45) e os três testes reprovam (p ≈ 0).
- Depois do extrator de von Neumann, os testes voltam a passar, com cerca de 25% dos bits aproveitados.

## Relação com o wfc_bench

É a mesma metodologia: circuito em Qiskit, modelo de ruído, muitas amostras e uma métrica estatística contra o valor teórico. O QWFC é amostragem quântica com restrições; um QRNG é amostragem quântica sem restrições.
