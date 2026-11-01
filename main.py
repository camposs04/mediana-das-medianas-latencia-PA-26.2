"""Ponto de entrada da demonstração de percentis de latência."""

import argparse
import os
import sys

import dados
import trace
from selecao import selecionar

N_PADRAO = 1000
PERCENTIS_PADRAO = [50.0, 90.0, 99.0]
LIMITE_IMPRESSAO = 30


def inteiro(texto: str) -> int:
    """Converte um argumento em int, com mensagem de erro em português."""
    try:
        return int(texto)
    except ValueError:
        raise argparse.ArgumentTypeError(
            f"esperava um inteiro, recebido {texto!r}"
        ) from None


def numero(texto: str) -> float:
    """Converte um argumento em float, com mensagem de erro em português."""
    try:
        return float(texto)
    except ValueError:
        raise argparse.ArgumentTypeError(
            f"esperava um número, recebido {texto!r}"
        ) from None


def criar_parser() -> argparse.ArgumentParser:
    """Monta o parser dos argumentos da linha de comando."""
    parser = argparse.ArgumentParser(
        description="Calcula percentis de latência em O(n) com a Mediana das "
                    "Medianas, sem ordenar a lista."
    )
    fonte = parser.add_mutually_exclusive_group()
    fonte.add_argument("--n", type=inteiro,
                       help=f"quantidade de latências geradas (padrão: {N_PADRAO})")
    fonte.add_argument("--arquivo", help="arquivo com uma latência por linha")
    parser.add_argument("--seed", type=inteiro,
                        help="semente da geração, ignorada com --arquivo")
    parser.add_argument("--percentis", type=numero, nargs="+", metavar="P",
                        help="percentis em (0, 100] (padrão: 50 90 99)")
    parser.add_argument("--k", type=inteiro,
                        help="pede o k-ésimo menor, com k a partir de 1")
    parser.add_argument("--trace", action="store_true",
                        help="mostra a recursão passo a passo")
    return parser


def obter_latencias(args: argparse.Namespace) -> list[int]:
    """Lê as latências do arquivo pedido ou gera uma lista aleatória."""
    if args.arquivo is None:
        n = N_PADRAO if args.n is None else args.n
        return dados.gerar_latencias(n, args.seed)

    latencias = dados.ler_latencias(args.arquivo)
    if not latencias:
        raise ValueError(f"{args.arquivo}: arquivo vazio, sem latências")
    return latencias


def montar_consultas(args: argparse.Namespace, n: int) -> list[tuple[str, int]]:
    """Devolve os pares (rótulo, k 0-indexado) que a execução deve calcular."""
    consultas = []
    if args.k is not None:
        if not 1 <= args.k <= n:
            raise ValueError(f"--k deve estar entre 1 e {n}, recebido {args.k}")
        consultas.append((f"k={args.k}", args.k - 1))

    percentis = args.percentis
    if percentis is None:
        percentis = PERCENTIS_PADRAO if args.k is None else []
    for p in percentis:
        rotulo = "p" + str(p).removesuffix(".0")
        consultas.append((rotulo, dados.k_do_percentil(p, n)))
    return consultas


def preparar(parser: argparse.ArgumentParser,
             args: argparse.Namespace) -> tuple[list[int], list[tuple[str, int]]]:
    """Devolve a entrada e as consultas, ou encerra com uma mensagem de erro."""
    try:
        latencias = obter_latencias(args)
        return latencias, montar_consultas(args, len(latencias))
    except OSError as erro:
        parser.error(f"não foi possível ler {args.arquivo}: {erro.strerror}")
    except UnicodeDecodeError:
        parser.error(f"{args.arquivo} não é um arquivo de texto UTF-8")
    except ValueError as erro:
        parser.error(str(erro))


def main() -> None:
    """Executa a demonstração."""
    parser = criar_parser()
    args = parser.parse_args()
    latencias, consultas = preparar(parser, args)

    trace.ativar(args.trace)

    origem = args.arquivo or f"geradas, seed {args.seed}"
    print(f"Entrada: n={len(latencias)} ({origem})")
    if len(latencias) <= LIMITE_IMPRESSAO:
        print(latencias)
    print()

    ordenada = sorted(latencias)
    for rotulo, k in consultas:
        if args.trace:
            print(f"--- {rotulo}: selecionar(k={k}) ---")
        valor = selecionar(latencias, k)
        print(f"{rotulo}: {valor} ms | sorted: {ordenada[k]} ms")


if __name__ == "__main__":
    try:
        main()
        sys.stdout.flush()
    except BrokenPipeError:
        # O leitor fechou o pipe, como em `main.py | head -1`. Apontar stdout
        # para devnull evita um segundo erro no flush do encerramento.
        os.dup2(os.open(os.devnull, os.O_WRONLY), sys.stdout.fileno())
        sys.exit(1)
