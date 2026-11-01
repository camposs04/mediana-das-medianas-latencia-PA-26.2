"""Escolha do pivô pela Mediana das Medianas."""

from typing import Callable

Selecionar = Callable[[list[int], int, int], int]  # (lista, k, profundidade) -> valor


def dividir_em_grupos(lista: list[int], tamanho: int = 5) -> list[list[int]]:
    """Divide `lista` em grupos consecutivos de até `tamanho` elementos."""
    return [lista[i:i + tamanho] for i in range(0, len(lista), tamanho)]


def mediana_do_grupo(grupo: list[int]) -> int:
    """Devolve o índice (len-1)//2 da versão ordenada de `grupo`."""
    return sorted(grupo)[(len(grupo) - 1) // 2]


def mediana_das_medianas(lista: list[int], selecionar: Selecionar,
                         profundidade: int = 0) -> int:
    """Devolve o pivô de `lista`.

    Pivô = selecionar(medianas, (len(medianas)-1)//2, profundidade+1).
    Não importa selecao.py: a função de seleção chega por parâmetro.

    Stub: devolve o elemento central da lista ordenada, sem usar `selecionar`.
    """
    return sorted(lista)[len(lista) // 2]
