"""Obtenção de latências e conversão de percentil em posição."""

import math
import random


def gerar_latencias(n: int, seed: int | None = None) -> list[int]:
    """Gera `n` latências aleatórias em ms, reproduzíveis por `seed`.

    Cerca de 90% dos valores ficam entre 20 e 120 ms e 10% entre 300 e 900 ms,
    o que forma a cauda longa.
    """
    if n < 1:
        raise ValueError(f"n deve ser pelo menos 1, recebido {n}")

    gerador = random.Random(seed)
    latencias = []
    for _ in range(n):
        if gerador.random() < 0.9:
            latencias.append(gerador.randint(20, 120))
        else:
            latencias.append(gerador.randint(300, 900))
    return latencias


def ler_latencias(caminho: str) -> list[int]:
    """Lê as latências do arquivo em `caminho`, com um número por linha.

    Linhas vazias ou só com espaços são ignoradas, mas contam na numeração.
    """
    latencias = []
    with open(caminho, encoding="utf-8") as arquivo:
        for numero, linha in enumerate(arquivo, start=1):
            conteudo = linha.strip()
            if not conteudo:
                continue
            try:
                latencias.append(int(conteudo))
            except ValueError:
                raise ValueError(
                    f"linha {numero}: valor inválido {conteudo!r}"
                ) from None
    return latencias


def k_do_percentil(p: float, n: int) -> int:
    """Devolve a posição do percentil `p` em `n` valores.

    Nearest-rank, 0-indexado: ceil(p * n / 100) - 1, limitado a [0, n-1].
    """
    if not 0 < p <= 100:
        raise ValueError(f"p deve estar em (0, 100], recebido {p}")
    if n < 1:
        raise ValueError(f"n deve ser pelo menos 1, recebido {n}")

    # A multiplicação vem antes da divisão para evitar erro de ponto flutuante.
    return max(0, min(n - 1, math.ceil(p * n / 100) - 1))
