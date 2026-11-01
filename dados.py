"""Obtenção de latências e conversão de percentil em posição."""

from math import ceil


def gerar_latencias(n: int, seed: int | None = None) -> list[int]:
    """Gera `n` latências aleatórias, reproduzíveis por `seed`.

    Stub: devolve uma lista fixa pequena, ignorando os parâmetros.
    """
    return [42, 7, 19, 88, 23]


def ler_latencias(caminho: str) -> list[int]:
    """Lê as latências do arquivo em `caminho`.

    Stub: devolve uma lista fixa pequena, sem abrir o arquivo.
    """
    return [42, 7, 19, 88, 23]


def k_do_percentil(p: float, n: int) -> int:
    """Devolve a posição do percentil `p` em `n` valores.

    Nearest-rank, 0-indexado: ceil(p/100 * n) - 1, limitado a [0, n-1].
    A multiplicação vem antes da divisão para evitar erro de ponto flutuante.
    """
    return max(0, min(n - 1, ceil(p * n / 100) - 1))
