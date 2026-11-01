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
    """Devolve o k-ésimo menor elemento de `lista`, 0-indexado, em O(n).

    A recursão segue um só lado da partição. O pivô da mediana das medianas
    deixa no máximo cerca de 7n/10 elementos nesse lado, o que dá a recorrência
    T(n) <= T(n/5) + T(7n/10) + O(n).
    """
    n = len(lista)
    if n == 0:
        raise ValueError("lista não pode ser vazia")
    if not 0 <= k < n:
        raise ValueError(f"k deve estar em [0, {n - 1}], recebido {k}")

    trace.log(profundidade, f"selecionar: k={k}, n={n}")

    if n <= 5:
        # Custo O(1), porque n é limitado por uma constante.
        resultado = sorted(lista)[k]
        trace.log(profundidade, f"caso base: {resultado}")
        return resultado

    pivo = mediana_das_medianas(lista, selecionar, profundidade)
    menores, iguais, maiores = particionar(lista, pivo, profundidade)
    m, i = len(menores), len(iguais)

    if k < m:
        trace.log(profundidade, "lado: menores")
        return selecionar(menores, k, profundidade + 1)
    if k < m + i:
        trace.log(profundidade, f"lado: iguais, resultado {pivo}")
        return pivo
    trace.log(profundidade, "lado: maiores")
    return selecionar(maiores, k - m - i, profundidade + 1)
