"""Seleção do k-ésimo menor elemento (BFPRT)."""

from pivo import mediana_das_medianas


def particionar(lista: list[int], pivo: int) -> tuple[list[int], list[int], list[int]]:
    """Separa `lista` em menores, iguais e maiores que `pivo`."""
    return (
        [x for x in lista if x < pivo],
        [x for x in lista if x == pivo],
        [x for x in lista if x > pivo],
    )


def selecionar(lista: list[int], k: int, profundidade: int = 0) -> int:
    """Devolve o k-ésimo menor elemento de `lista`, 0-indexado.

    Stub: ordena a lista inteira, sem usar `mediana_das_medianas`.
    """
    return sorted(lista)[k]
