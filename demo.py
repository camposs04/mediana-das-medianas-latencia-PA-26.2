"""Animação da Mediana das Medianas no terminal, só com a biblioteca padrão.

A animação não tem uma cópia do algoritmo: ela chama `selecao.selecionar` e
observa as funções reais enquanto rodam. Cada etapa vira um `Quadro`, e a tela
mostra um quadro por vez, com as peças deslizando de uma cena para a outra.
"""

import argparse
import locale
import math
import os
import sys
import textwrap
import time
from dataclasses import dataclass, field
from typing import NamedTuple

import main as cli
import pivo
import selecao

try:
    import curses
except ImportError:  # O Python do Windows não traz o curses.
    curses = None

MAX_N = 60
ARQUIVO_PADRAO = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                              "exemplos", "latencias.txt")
INTERVALO_PADRAO = 3.0
DURACAO_MOVIMENTO = 0.45
ESPERA_TECLA_MS = 33

MARGEM = 2
TOPO_PALCO = 5  # Título, linha vazia, duas de legenda e outra vazia.
LINHAS_FIXAS = TOPO_PALCO + 2  # Mais a linha vazia e o rodapé.
LARGURA_ROTULO = 13
NOMES_FAIXAS = ("menores", "iguais", "maiores")


class Elemento(int):
    """Inteiro com identidade, para a tela seguir cada peça mesmo com repetidos.

    Para `selecao.py` ele é um int comum: compara e imprime do mesmo jeito.
    """

    def __new__(cls, valor: int, ident: int) -> "Elemento":
        elemento = super().__new__(cls, valor)
        elemento.ident = ident
        return elemento


@dataclass(frozen=True)
class Quadro:
    """Uma tela da animação. `blocos` guarda os ids das peças de cada parte."""

    titulo: str
    legenda: str
    cena: str  # "lista", "grupos" ou "particao".
    blocos: tuple[tuple[int, ...], ...]
    marcas: dict[int, str] = field(default_factory=dict)
    alvo: int | None = None  # Posição do alvo, na cena "lista".
    destaque: int | None = None  # Faixa escolhida, na cena "particao".


@dataclass
class Chamada:
    """Estado de uma chamada de `selecionar` em andamento."""

    k: int
    lista: list[Elemento]
    abertura: str
    particao: tuple | None = None
    lado_anunciado: bool = False

    @property
    def titulo(self) -> str:
        return f"selecionar(k={self.k}, n={len(self.lista)})"


def _ids(lista: list[Elemento]) -> tuple[int, ...]:
    return tuple(elemento.ident for elemento in lista)


def _marcar(lista: list[Elemento], marca: str) -> dict[int, str]:
    return {elemento.ident: marca for elemento in lista}


def _contar(n: int, singular: str, plural: str) -> str:
    return f"{n} {singular if n == 1 else plural}"


def gerar_quadros(valores: list[int], k: int, rotulo: str) -> list[Quadro]:
    """Roda a seleção real sobre `valores` e devolve os quadros da animação."""
    elementos = [Elemento(valor, i) for i, valor in enumerate(valores)]
    selecionar_real = selecao.selecionar
    particionar_real = selecao.particionar
    pivo_real = selecao.mediana_das_medianas

    quadros: list[Quadro] = []
    pilha: list[Chamada] = []
    abertura = ""

    def emitir(cena: str, legenda: str, blocos: list[list[Elemento]],
               **extras) -> None:
        quadros.append(Quadro(pilha[-1].titulo, legenda.strip(), cena,
                              tuple(_ids(b) for b in blocos), **extras))

    def anunciar_lado(chamada: Chamada, faixa: int, k_novo: int | None) -> None:
        """Mostra a faixa que a seleção real acabou de escolher."""
        chamada.lado_anunciado = True
        partes = chamada.particao
        marcas: dict[int, str] = {}
        for i, parte in enumerate(partes):
            marca = "apagada" if i != faixa else ("menor", "pivo", "maior")[i]
            marcas |= _marcar(parte, marca)
        escolhida = partes[faixa]
        if faixa == 1:
            legenda = (f"k={chamada.k} cai em iguais: o resultado é o próprio "
                       f"pivô, {escolhida[0]}.")
        else:
            fora = len(chamada.lista) - len(escolhida)
            legenda = (f"k={chamada.k} cai nos {NOMES_FAIXAS[faixa]}: "
                       f"{_contar(fora, 'valor sai', 'valores saem')} do problema.")
        emitir("particao", legenda, list(partes), marcas=marcas, destaque=faixa)
        if faixa != 1:
            nonlocal abertura
            abertura = f"Seguimos com k={k_novo} nos {len(escolhida)} {NOMES_FAIXAS[faixa]}."

    def selecionar_visivel(lista: list[Elemento], k_atual: int,
                           profundidade: int = 0) -> int:
        nonlocal abertura
        if pilha and pilha[-1].particao is not None:
            # A seleção real passa adiante o próprio objeto da partição.
            faixa = 0 if lista is pilha[-1].particao[0] else 2
            anunciar_lado(pilha[-1], faixa, k_atual)

        chamada = Chamada(k_atual, lista, abertura)
        abertura = ""
        pilha.append(chamada)
        resultado = selecionar_real(lista, k_atual, profundidade)

        if len(lista) <= 5:
            ordenada = sorted(lista)
            emitir("lista",
                   f"{chamada.abertura} Com n ≤ 5 basta ordenar: "
                   f"o índice {k_atual} vale {resultado}.",
                   [ordenada], marcas={ordenada[k_atual].ident: "alvo"},
                   alvo=k_atual)
        elif not chamada.lado_anunciado:
            anunciar_lado(chamada, 1, None)
        pilha.pop()
        return resultado

    def pivo_visivel(lista: list[Elemento], selecionar_fn, profundidade: int = 0) -> int:
        nonlocal abertura
        grupos = pivo.dividir_em_grupos(lista)
        medianas = [pivo.mediana_do_grupo(grupo) for grupo in grupos]
        emitir("grupos",
               f"{pilha[-1].abertura} Dividimos em "
               f"{_contar(len(grupos), 'grupo', 'grupos')} de até 5.",
               grupos)
        emitir("grupos",
               "Ordenamos cada grupo. A linha do meio traz as medianas.",
               [sorted(grupo) for grupo in grupos],
               marcas=_marcar(medianas, "mediana"))
        abertura = f"Para achar o pivô, repetimos tudo nas {len(grupos)} medianas."
        return pivo_real(lista, selecionar_fn, profundidade)

    def particionar_visivel(lista: list[Elemento], pivo_escolhido: int,
                            profundidade: int = 0) -> tuple:
        partes = particionar_real(lista, pivo_escolhido, profundidade)
        menores, iguais, maiores = partes
        pilha[-1].particao = partes
        emitir("particao",
               f"Pivô {pivo_escolhido}: {_contar(len(menores), 'menor', 'menores')}, "
               f"{_contar(len(iguais), 'igual', 'iguais')} e "
               f"{_contar(len(maiores), 'maior', 'maiores')}.",
               list(partes),
               marcas={**_marcar(menores, "menor"), **_marcar(iguais, "pivo"),
                       **_marcar(maiores, "maior")})
        return partes

    n = len(elementos)
    quadros.append(Quadro(f"selecionar(k={k}, n={n})",
                          f"Queremos o {k + 1}º menor de {n} valores, "
                          "sem ordenar a lista.",
                          "lista", (_ids(elementos),)))

    selecao.selecionar = selecionar_visivel
    selecao.particionar = particionar_visivel
    selecao.mediana_das_medianas = pivo_visivel
    try:
        resultado = selecionar_visivel(elementos, k)
    finally:
        selecao.selecionar = selecionar_real
        selecao.particionar = particionar_real
        selecao.mediana_das_medianas = pivo_real

    ordenada = sorted(elementos)
    conferencia = ordenada[k]
    fecho = (f"Ordenando tudo, o índice {k} também vale {conferencia}."
             if resultado == conferencia else f"Mas sorted traz {conferencia}.")
    quadros.append(Quadro("Resultado", f"{rotulo} = {resultado} ms. {fecho}", "lista",
                          (_ids(ordenada),), marcas={conferencia.ident: "alvo"},
                          alvo=k))
    return quadros


class Nota(NamedTuple):
    """Texto fixo do palco, fora das peças."""

    x: int
    y: int
    texto: str
    estilo: str = "normal"


class Cena(NamedTuple):
    """Onde cada peça e cada nota ficam em um quadro."""

    pos: dict[int, tuple[int, int]]
    notas: list[Nota]


def largura_peca(valores: list[int]) -> int:
    """Largura de uma peça: o maior número, com um espaço de cada lado."""
    return max(len(str(valor)) for valor in valores) + 2


def _centralizar(total: int, disponivel: int) -> int:
    return max(0, (disponivel - total) // 2)


def _dispor_lista(quadro: Quadro, largura: int, altura: int, peca: int) -> Cena | None:
    ids = quadro.blocos[0]
    por_fila = (largura - 2 * MARGEM + 1) // (peca + 1)
    if por_fila < 1:
        return None
    filas = math.ceil(len(ids) / por_fila)
    if 2 * filas > altura:  # Cada fila reserva uma linha para a marca do alvo.
        return None

    topo = _centralizar(2 * filas, altura)
    pos, notas = {}, []
    for i, ident in enumerate(ids):
        fila, coluna = divmod(i, por_fila)
        na_fila = min(por_fila, len(ids) - fila * por_fila)
        inicio = _centralizar(na_fila * (peca + 1) - 1, largura)
        pos[ident] = (inicio + coluna * (peca + 1), topo + 2 * fila)
        if i == quadro.alvo:
            texto = f"k={i}"
            x = pos[ident][0] + (peca - len(texto)) // 2
            notas.append(Nota(max(0, min(x, largura - len(texto))),
                              pos[ident][1] + 1, texto, "forte"))
    return Cena(pos, notas)


def _dispor_grupos(quadro: Quadro, largura: int, altura: int, peca: int) -> Cena | None:
    por_fila = (largura - 2 * MARGEM + 2) // (peca + 2)
    if por_fila < 1:
        return None
    filas = math.ceil(len(quadro.blocos) / por_fila)
    total = 6 * filas - 1  # Cinco linhas por fila de grupos, e uma entre elas.
    if total > altura:
        return None

    topo = _centralizar(total, altura)
    pos = {}
    for g, grupo in enumerate(quadro.blocos):
        fila, coluna = divmod(g, por_fila)
        na_fila = min(por_fila, len(quadro.blocos) - fila * por_fila)
        inicio = _centralizar(na_fila * (peca + 2) - 2, largura)
        # Alinha a mediana de todo grupo na linha central.
        desvio = 2 - (len(grupo) - 1) // 2
        for i, ident in enumerate(grupo):
            pos[ident] = (inicio + coluna * (peca + 2), topo + 6 * fila + i + desvio)
    return Cena(pos, [])


def _dispor_particao(quadro: Quadro, largura: int, altura: int, peca: int) -> Cena | None:
    por_fila = (largura - 2 * MARGEM - LARGURA_ROTULO + 1) // (peca + 1)
    if por_fila < 1:
        return None
    alturas = [max(1, math.ceil(len(faixa) / por_fila)) for faixa in quadro.blocos]
    total = sum(alturas) + 2
    if total > altura:
        return None

    pos, notas = {}, []
    y = _centralizar(total, altura)
    for f, faixa in enumerate(quadro.blocos):
        estilo = "normal"
        if quadro.destaque is not None:
            estilo = "forte" if f == quadro.destaque else "apagada"
        notas.append(Nota(MARGEM, y, f"{NOMES_FAIXAS[f]}: {len(faixa)}", estilo))
        for i, ident in enumerate(faixa):
            fila, coluna = divmod(i, por_fila)
            pos[ident] = (MARGEM + LARGURA_ROTULO + coluna * (peca + 1), y + fila)
        y += alturas[f] + 1
    return Cena(pos, notas)


def dispor(quadro: Quadro, largura: int, altura: int, peca: int) -> Cena | None:
    """Calcula a cena no palco dado, ou devolve None se ela não couber."""
    funcoes = {"lista": _dispor_lista, "grupos": _dispor_grupos,
               "particao": _dispor_particao}
    return funcoes[quadro.cena](quadro, largura, altura, peca)


def interpolar(origem: tuple[int, int], destino: tuple[int, int],
               progresso: float) -> tuple[int, int]:
    """Posição de uma peça em movimento, com `progresso` entre 0 e 1."""
    suave = 1 - (1 - progresso) ** 3  # Sai rápido e desacelera até parar.
    return (round(origem[0] + (destino[0] - origem[0]) * suave),
            round(origem[1] + (destino[1] - origem[1]) * suave))


def criar_estilos() -> dict[str, int]:
    """Monta os atributos de cada marca, conforme as cores do terminal."""
    apagada = curses.A_DIM
    if not curses.has_colors():
        return {"normal": curses.A_REVERSE, "mediana": curses.A_REVERSE | curses.A_BOLD,
                "menor": curses.A_REVERSE, "maior": curses.A_REVERSE,
                "pivo": curses.A_BOLD | curses.A_UNDERLINE,
                "alvo": curses.A_BOLD | curses.A_UNDERLINE, "apagada": apagada}

    if curses.COLORS >= 256:
        pares = {"normal": (16, 252), "mediana": (16, 221), "menor": (16, 117),
                 "maior": (16, 209), "pivo": (231, 161), "alvo": (16, 84)}
    else:
        pares = {"normal": (curses.COLOR_BLACK, curses.COLOR_WHITE),
                 "mediana": (curses.COLOR_BLACK, curses.COLOR_YELLOW),
                 "menor": (curses.COLOR_BLACK, curses.COLOR_CYAN),
                 "maior": (curses.COLOR_BLACK, curses.COLOR_RED),
                 "pivo": (curses.COLOR_WHITE, curses.COLOR_MAGENTA),
                 "alvo": (curses.COLOR_BLACK, curses.COLOR_GREEN)}

    estilos = {"apagada": apagada}
    for numero, (nome, (frente, fundo)) in enumerate(pares.items(), start=1):
        curses.init_pair(numero, frente, fundo)
        estilos[nome] = curses.color_pair(numero)
    return estilos


class Tela:
    """Desenha os quadros e responde ao teclado."""

    def __init__(self, tela, quadros: list[Quadro], valores: list[int],
                 intervalo: float) -> None:
        self.tela = tela
        self.quadros = quadros
        self.valores = valores
        self.intervalo = intervalo
        self.peca = largura_peca(valores)
        self.estilos = criar_estilos()
        self.indice = 0
        self.tocando = False
        self.proxima_troca = 0.0
        self.inicio_movimento = 0.0
        self.origem: dict[int, tuple[int, int]] = {}
        self.cena = self.medir()
        self.sujo = True
        self.animando = False

    def medir(self) -> Cena | None:
        altura, largura = self.tela.getmaxyx()
        return dispor(self.quadros[self.indice], largura, altura - LINHAS_FIXAS, self.peca)

    def progresso(self, agora: float) -> float:
        return min(1.0, (agora - self.inicio_movimento) / DURACAO_MOVIMENTO)

    def posicoes(self, agora: float) -> dict[int, tuple[int, int]]:
        if self.cena is None:
            return {}
        fracao = self.progresso(agora)
        return {ident: interpolar(self.origem.get(ident, destino), destino, fracao)
                for ident, destino in self.cena.pos.items()}

    def ir_para(self, indice: int, agora: float) -> None:
        self.origem = self.posicoes(agora)
        self.indice = max(0, min(len(self.quadros) - 1, indice))
        self.cena = self.medir()
        self.inicio_movimento = agora
        self.proxima_troca = agora + DURACAO_MOVIMENTO + self.intervalo
        self.sujo = True

    def alternar_reproducao(self, agora: float) -> None:
        self.tocando = not self.tocando
        self.sujo = True
        if self.tocando:
            no_fim = self.indice == len(self.quadros) - 1
            self.ir_para(0 if no_fim else self.indice + 1, agora)

    def escrever(self, y: int, x: int, texto: str, atributo: int = 0) -> None:
        altura, largura = self.tela.getmaxyx()
        if not (0 <= y < altura and 0 <= x < largura):
            return
        try:
            self.tela.addnstr(y, x, texto, largura - x, atributo)
        except curses.error:  # Escrever na última célula da tela sempre falha.
            pass

    def desenhar(self, agora: float) -> None:
        self.tela.erase()
        altura, largura = self.tela.getmaxyx()
        if self.cena is None:
            self.escrever(0, 0, "Aumente o terminal", curses.A_BOLD)
            self.tela.refresh()
            return

        quadro = self.quadros[self.indice]
        contador = f"{self.indice + 1}/{len(self.quadros)}"
        self.escrever(0, MARGEM, quadro.titulo, curses.A_BOLD)
        self.escrever(0, largura - MARGEM - len(contador), contador, curses.A_DIM)
        linhas = textwrap.wrap(quadro.legenda, largura - 2 * MARGEM)
        for i, linha in enumerate(linhas[:2]):
            self.escrever(2 + i, MARGEM, linha)

        atributos = {"normal": 0, "forte": curses.A_BOLD, "apagada": curses.A_DIM}
        for nota in self.cena.notas:
            self.escrever(TOPO_PALCO + nota.y, nota.x, nota.texto, atributos[nota.estilo])

        for ident, (x, y) in self.posicoes(agora).items():
            texto = f"{self.valores[ident]:^{self.peca}}"
            estilo = self.estilos[quadro.marcas.get(ident, "normal")]
            self.escrever(TOPO_PALCO + y, x, texto, estilo)

        acao = "pausa" if self.tocando else "reproduz"
        rodape = f"espaço {acao}   ←/→ passo   r início   q sai"
        self.escrever(altura - 1, MARGEM, rodape, curses.A_DIM)
        self.tela.refresh()

    def rodar(self) -> None:
        self.tela.timeout(ESPERA_TECLA_MS)
        while True:
            agora = time.monotonic()
            if self.sujo or self.animando:
                # Decide antes de desenhar: o quadro com progresso 1 ainda sai.
                self.animando = self.progresso(agora) < 1
                self.desenhar(agora)
                self.sujo = False

            tecla = self.tela.getch()
            agora = time.monotonic()
            if tecla in (ord("q"), ord("Q")):
                return
            if tecla == ord(" "):
                self.alternar_reproducao(agora)
            elif tecla == curses.KEY_RIGHT:
                self.tocando = False
                self.ir_para(self.indice + 1, agora)
            elif tecla == curses.KEY_LEFT:
                self.tocando = False
                self.ir_para(self.indice - 1, agora)
            elif tecla in (ord("r"), ord("R")):
                self.tocando = False
                self.ir_para(0, agora)
            elif tecla == curses.KEY_RESIZE:
                self.origem = {}
                self.cena = self.medir()
                self.sujo = True
            elif self.tocando and agora >= self.proxima_troca:
                if self.indice == len(self.quadros) - 1:
                    self.tocando = False
                    self.sujo = True
                else:
                    self.ir_para(self.indice + 1, agora)


def criar_parser() -> argparse.ArgumentParser:
    """Monta o parser dos argumentos da animação."""
    parser = argparse.ArgumentParser(
        description="Anima a Mediana das Medianas no terminal, um passo por vez."
    )
    fonte = parser.add_mutually_exclusive_group()
    fonte.add_argument("--arquivo",
                       help="arquivo com uma latência por linha "
                            "(padrão: exemplos/latencias.txt)")
    fonte.add_argument("--n", type=cli.inteiro,
                       help=f"quantidade de latências geradas, até {MAX_N}")
    parser.add_argument("--seed", type=cli.inteiro, help="semente da geração")
    consulta = parser.add_mutually_exclusive_group()
    consulta.add_argument("--percentil", type=cli.numero, default=90.0,
                          help="percentil em (0, 100] (padrão: 90)")
    consulta.add_argument("--k", type=cli.inteiro,
                          help="pede o k-ésimo menor, com k a partir de 1")
    parser.add_argument("--intervalo", type=cli.numero, default=INTERVALO_PADRAO,
                        help="segundos em cada passo ao reproduzir "
                             f"(padrão: {INTERVALO_PADRAO:g})")
    return parser


def main() -> None:
    """Valida os argumentos e abre a animação."""
    parser = criar_parser()
    args = parser.parse_args()
    if not args.intervalo > 0:
        parser.error("--intervalo deve ser maior que zero")
    if args.arquivo is None and args.n is None:
        args.arquivo = ARQUIVO_PADRAO
    args.percentis = None if args.k is not None else [args.percentil]

    valores, consultas = cli.preparar(parser, args)
    if len(valores) > MAX_N:
        parser.error(f"a animação cabe na tela com até {MAX_N} valores, "
                     f"recebidos {len(valores)}")
    if curses is None:
        parser.error("o curses não está disponível neste Python "
                     "(no Windows: pip install windows-curses)")
    if not (sys.stdin.isatty() and sys.stdout.isatty()):
        parser.error("a animação precisa rodar em um terminal interativo")

    rotulo, k = consultas[0]
    quadros = gerar_quadros(valores, k, rotulo)

    def abrir(tela) -> None:
        try:
            curses.curs_set(0)
        except curses.error:  # Alguns terminais não escondem o cursor.
            pass
        curses.use_default_colors()
        Tela(tela, quadros, valores, args.intervalo).rodar()

    try:
        locale.setlocale(locale.LC_ALL, "")
    except locale.Error:
        pass
    try:
        curses.wrapper(abrir)
    except KeyboardInterrupt:
        pass
    except curses.error as erro:
        parser.error(f"o terminal não suporta a animação: {erro}")


if __name__ == "__main__":
    main()
