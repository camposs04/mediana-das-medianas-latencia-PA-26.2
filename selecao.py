"""Seleção do k-ésimo menor elemento (BFPRT)."""

import trace
from pivo import mediana_das_medianas


def particionar(lista: list[int], pivo: int,
                profundidade: int = 0) -> tuple[list[int], list[int], list[int]]:
    """Separa `lista` em menores, iguais e maiores que `pivo`, em uma passada.

    A parte `iguais` absorve os valores repetidos. Como o pivô cai nela, as
    outras duas partes são sempre menores que `lista` e a recursão termina.
    """
    menores, iguais, maiores = [], [], []
    for valor in lista:
        if valor < pivo:
            menores.append(valor)
        elif valor > pivo:
            maiores.append(valor)
        else:
            iguais.append(valor)

    trace.log(profundidade, f"partição: menores={len(menores)}, "
                            f"iguais={len(iguais)}, maiores={len(maiores)}")
    return menores, iguais, maiores


def selecionar(lista: list[int], k: int, profundidade: int = 0) -> int:
    """Devolve o k-ésimo menor elemento de `lista`, 0-indexado.

    Stub: ordena a lista inteira, sem usar `mediana_das_medianas`.
    """
    return sorted(lista)[k]
