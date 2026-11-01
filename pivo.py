"""Escolha do pivô pela Mediana das Medianas."""

from typing import Callable

import trace

Selecionar = Callable[[list[int], int, int], int]  # (lista, k, profundidade) -> valor


def dividir_em_grupos(lista: list[int], tamanho: int = 5) -> list[list[int]]:
    """Divide `lista` em grupos consecutivos de até `tamanho` elementos."""
    return [lista[i:i + tamanho] for i in range(0, len(lista), tamanho)]


def mediana_do_grupo(grupo: list[int]) -> int:
    """Devolve o valor de índice (len-1)//2 da versão ordenada de `grupo`.

    Em grupo par, esse valor é a mediana inferior.
    """
    # Custo O(1) por grupo, porque o tamanho do grupo é constante.
    ordenado = grupo.copy()
    for i in range(1, len(ordenado)):
        atual = ordenado[i]
        j = i - 1
        while j >= 0 and ordenado[j] > atual:
            ordenado[j + 1] = ordenado[j]
            j -= 1
        ordenado[j + 1] = atual
    return ordenado[(len(ordenado) - 1) // 2]


def mediana_das_medianas(lista: list[int], selecionar: Selecionar,
                         profundidade: int = 0) -> int:
    """Devolve o pivô de `lista`, a mediana das medianas.
    """
    if not lista:
        raise ValueError("lista não pode ser vazia")

    grupos = dividir_em_grupos(lista)
    trace.log(profundidade, f"grupos: {len(grupos)}, tamanhos {[len(g) for g in grupos]}")

    medianas = [mediana_do_grupo(g) for g in grupos]
    trace.log(profundidade, f"medianas: {medianas}")

    pivo = selecionar(medianas, (len(medianas) - 1) // 2, profundidade + 1)
    trace.log(profundidade, f"pivô: {pivo}")
    return pivo
