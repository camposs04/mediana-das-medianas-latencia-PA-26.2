"""Testes da animação no terminal. A tela roda de verdade em um pseudo-terminal."""

import collections
import contextlib
import io
import os
import random
import re
import select
import struct
import subprocess
import sys
import time
import unittest
from unittest.mock import patch

import demo
import selecao
import trace

RAIZ = os.path.dirname(os.path.abspath(__file__))
EXEMPLO = [47, 82, 35, 118, 64, 412, 29, 91, 56, 73, 105, 38, 67, 22, 850, 99,
           44, 78, 113, 31, 58, 86, 327, 52, 70]
LISTAS = {
    "exemplo": EXEMPLO,
    "unitaria": [5],
    "caso base": [9, 1, 8, 2, 7],
    "seis": [9, 1, 8, 2, 7, 3],
    "iguais": [7] * 30,
    "repetidos": [40, 60, 80] * 19,
    "crescente": list(range(100, 160)),
    "negativos": [-5, 3, -1, 0, 7, -9, 2, 2, -5, 8, 1, 4],
}


def ids_do_quadro(quadro):
    return [ident for bloco in quadro.blocos for ident in bloco]


class TestElemento(unittest.TestCase):
    def test_compara_e_imprime_como_inteiro(self):
        elemento = demo.Elemento(7, ident=3)
        self.assertEqual(elemento, 7)
        self.assertLess(elemento, 8)
        self.assertEqual(f"{elemento}", "7")
        self.assertEqual(elemento.ident, 3)

    def test_valores_iguais_mantem_identidades_diferentes(self):
        a, b = demo.Elemento(7, 0), demo.Elemento(7, 1)
        self.assertEqual(sorted([a, b])[0].ident, 0)
        self.assertEqual(sorted([b, a])[0].ident, 1)


class TestGerarQuadros(unittest.TestCase):
    def test_todo_k_termina_no_valor_de_sorted(self):
        for nome, lista in LISTAS.items():
            ordenada = sorted(lista)
            for k in range(len(lista)):
                with self.subTest(nome, k=k):
                    ultimo = demo.gerar_quadros(lista, k, "t")[-1]
                    alvo = ultimo.blocos[0][ultimo.alvo]
                    self.assertEqual(lista[alvo], ordenada[k])
                    self.assertIn(f"t = {ordenada[k]} ms", ultimo.legenda)

    def test_listas_aleatorias(self):
        gerador = random.Random(5)
        for _ in range(200):
            lista = [gerador.randint(0, 30) for _ in range(gerador.randint(1, 60))]
            k = gerador.randrange(len(lista))
            ultimo = demo.gerar_quadros(lista, k, "t")[-1]
            self.assertEqual(lista[ultimo.blocos[0][ultimo.alvo]], sorted(lista)[k])

    def test_particoes_mostradas_sao_as_do_trace_real(self):
        for k in range(len(EXEMPLO)):
            saida = io.StringIO()
            trace.ativar(True)
            try:
                with contextlib.redirect_stdout(saida):
                    selecao.selecionar(EXEMPLO, k)
            finally:
                trace.ativar(False)
            reais = re.findall(r"menores=(\d+), iguais=(\d+), maiores=(\d+)",
                               saida.getvalue())
            mostradas = [
                tuple(str(len(bloco)) for bloco in q.blocos)
                for q in demo.gerar_quadros(EXEMPLO, k, "t")
                if q.cena == "particao" and q.destaque is None
            ]
            self.assertEqual(mostradas, reais)

    def test_exibe_o_que_o_codigo_real_devolve(self):
        # Se selecao.py mudar, a animação muda junto, porque não há cópia.
        original = selecao.particionar

        def invertida(lista, pivo, profundidade=0):
            menores, iguais, maiores = original(lista, pivo, profundidade)
            return maiores, iguais, menores

        selecao.particionar = invertida
        try:
            quadros = demo.gerar_quadros(EXEMPLO, 22, "t")
        finally:
            selecao.particionar = original
        primeira = next(q for q in quadros if q.cena == "particao")
        self.assertTrue(all(EXEMPLO[i] > 70 for i in primeira.blocos[0]))

    def test_devolve_o_modulo_como_estava(self):
        antes = (selecao.selecionar, selecao.particionar, selecao.mediana_das_medianas)
        demo.gerar_quadros(EXEMPLO, 22, "t")
        depois = (selecao.selecionar, selecao.particionar, selecao.mediana_das_medianas)
        self.assertEqual(antes, depois)

    def test_todo_quadro_tem_ids_validos_sem_repeticao(self):
        for nome, lista in LISTAS.items():
            for k in {0, len(lista) // 2, len(lista) - 1}:
                for quadro in demo.gerar_quadros(lista, k, "t"):
                    ids = ids_do_quadro(quadro)
                    with self.subTest(nome, k=k, legenda=quadro.legenda):
                        self.assertEqual(len(ids), len(set(ids)))
                        self.assertTrue(set(ids) <= set(range(len(lista))))
                        self.assertTrue(set(quadro.marcas) <= set(ids))

    def test_grupos_tem_no_maximo_cinco(self):
        for quadro in demo.gerar_quadros(EXEMPLO, 22, "t"):
            if quadro.cena == "grupos":
                self.assertLessEqual(max(map(len, quadro.blocos)), 5)

    def test_medianas_ficam_na_posicao_central_do_grupo(self):
        for nome, lista in LISTAS.items():
            for quadro in demo.gerar_quadros(lista, len(lista) // 2, "t"):
                if quadro.cena == "grupos" and quadro.marcas:
                    for bloco in quadro.blocos:
                        marca = quadro.marcas.get(bloco[(len(bloco) - 1) // 2])
                        self.assertEqual(marca, "mediana", nome)

    def test_exemplo_cabe_em_poucos_quadros(self):
        self.assertLessEqual(len(demo.gerar_quadros(EXEMPLO, 22, "p90")), 20)

    def test_legenda_e_curta(self):
        # Menos informação por tela: no máximo duas linhas em 80 colunas.
        for nome, lista in LISTAS.items():
            for k in range(0, len(lista), 3):
                for quadro in demo.gerar_quadros(lista, k, "t"):
                    self.assertLessEqual(len(quadro.legenda), 150, quadro.legenda)

    def test_lado_marca_a_faixa_escolhida(self):
        quadros = demo.gerar_quadros(EXEMPLO, 22, "t")
        lado = next(q for q in quadros if q.cena == "particao" and q.destaque is not None)
        self.assertEqual(lado.destaque, 2)
        self.assertIn("maiores", lado.legenda)

    def test_faixas_recusadas_ficam_apagadas(self):
        quadros = demo.gerar_quadros(EXEMPLO, 22, "t")
        lado = next(q for q in quadros if q.cena == "particao" and q.destaque is not None)
        for f, faixa in enumerate(lado.blocos):
            esperada = "maior" if f == lado.destaque else "apagada"
            self.assertEqual({lado.marcas[ident] for ident in faixa}, {esperada})

    def test_caso_base_aponta_o_indice_pedido(self):
        lista = [9, 1, 8, 2, 7]
        for k in range(len(lista)):
            base = demo.gerar_quadros(lista, k, "t")[1]
            self.assertEqual(base.alvo, k)
            self.assertEqual(base.marcas[base.blocos[0][k]], "alvo")

    def test_valor_igual_ao_pivo_encerra_em_iguais(self):
        quadros = demo.gerar_quadros([7] * 30, 12, "t")
        self.assertTrue(any("iguais" in q.legenda and q.destaque == 1 for q in quadros))


class TestDispor(unittest.TestCase):
    def conferir(self, lista, largura, altura):
        peca = demo.largura_peca(lista)
        for k in {0, len(lista) // 2, len(lista) - 1}:
            for quadro in demo.gerar_quadros(lista, k, "t"):
                cena = demo.dispor(quadro, largura, altura, peca)
                self.assertIsNotNone(cena, quadro.legenda)
                self.assertEqual(set(cena.pos), set(ids_do_quadro(quadro)))
                ocupadas = collections.Counter()
                for x, y in cena.pos.values():
                    self.assertGreaterEqual(x, 0)
                    self.assertGreaterEqual(y, 0)
                    self.assertLessEqual(x + peca, largura)
                    self.assertLess(y, altura)
                    ocupadas.update((x + i, y) for i in range(peca))
                self.assertEqual(max(ocupadas.values()), 1, "peças sobrepostas")
                for nota in cena.notas:
                    self.assertGreaterEqual(nota.x, 0)
                    self.assertLessEqual(nota.x + len(nota.texto), largura)
                    self.assertLess(nota.y, altura)
                    self.assertFalse(any((nota.x + i, nota.y) in ocupadas
                                         for i in range(len(nota.texto))), nota.texto)

    def test_todas_as_listas_em_80x24(self):
        for nome, lista in LISTAS.items():
            with self.subTest(nome):
                self.conferir(lista, 80, 24 - demo.LINHAS_FIXAS)

    def test_maior_lista_com_valores_longos(self):
        gerador = random.Random(9)
        lista = [gerador.randint(100, 9999) for _ in range(demo.MAX_N)]
        self.conferir(lista, 80, 24 - demo.LINHAS_FIXAS)

    def test_medianas_de_grupos_diferentes_ficam_na_mesma_linha(self):
        lista = [9, 1, 8, 2, 7, 3, 6]  # Grupos de 5 e de 2.
        quadro = next(q for q in demo.gerar_quadros(lista, 3, "t")
                      if q.cena == "grupos" and q.marcas)
        cena = demo.dispor(quadro, 80, 24 - demo.LINHAS_FIXAS, 3)
        linhas = {cena.pos[ident][1] for ident in quadro.marcas}
        self.assertEqual(len(linhas), 1)

    def test_terminal_grande(self):
        self.conferir(EXEMPLO, 200, 50)

    def test_terminal_pequeno_devolve_none(self):
        quadro = demo.gerar_quadros(EXEMPLO, 22, "t")[1]
        self.assertIsNone(demo.dispor(quadro, 12, 3, demo.largura_peca(EXEMPLO)))


class TestInterpolar(unittest.TestCase):
    def test_extremos(self):
        self.assertEqual(demo.interpolar((2, 3), (12, 9), 0), (2, 3))
        self.assertEqual(demo.interpolar((2, 3), (12, 9), 1), (12, 9))

    def test_meio_do_caminho_fica_entre_os_extremos(self):
        x, y = demo.interpolar((0, 0), (10, 10), 0.5)
        self.assertTrue(0 < x < 10 and 0 < y < 10)

    def test_desacelera_no_fim(self):
        self.assertGreater(demo.interpolar((0, 0), (100, 0), 0.5)[0], 50)


class JanelaFalsa:
    """Janela do curses em memória, com um relógio que anda a cada tecla lida."""

    def __init__(self, teclas, passo):
        self.teclas = list(teclas)
        self.passo = passo
        self.agora = 0.0
        self.escritas = []

    def getmaxyx(self):
        return 24, 80

    def erase(self):
        self.escritas = []

    def addnstr(self, y, x, texto, _limite, _atributo=0):
        self.escritas.append((y, x, texto))

    def refresh(self):
        pass

    def timeout(self, _milissegundos):
        pass

    def getch(self):
        self.agora += self.passo
        return self.teclas.pop(0)


@unittest.skipIf(demo.curses is None, "Python sem curses")
class TestLaco(unittest.TestCase):
    def rodar(self, teclas, passo):
        janela = JanelaFalsa(teclas, passo)
        quadros = demo.gerar_quadros(EXEMPLO, 22, "t")
        with patch.object(demo, "criar_estilos", lambda: collections.defaultdict(int)), \
                patch.object(demo.time, "monotonic", lambda: janela.agora):
            tela = demo.Tela(janela, quadros, EXEMPLO, 3.0)
            tela.rodar()
        return janela, tela

    def test_movimento_termina_com_as_pecas_no_destino(self):
        # Com o terminal lento, o último desenho sai no meio do movimento.
        ociosa = -1
        janela, tela = self.rodar(
            [demo.curses.KEY_RIGHT, ociosa, ociosa, ociosa, ord("q")], passo=0.3)
        destinos = {(demo.TOPO_PALCO + y, x)
                    for x, y in tela.cena.pos.values()}
        desenhadas = {(y, x) for y, x, _ in janela.escritas}
        self.assertLessEqual(destinos, desenhadas)

    def test_seta_esquerda_volta_um_quadro(self):
        direita, esquerda = demo.curses.KEY_RIGHT, demo.curses.KEY_LEFT
        _, tela = self.rodar([direita, direita, esquerda, ord("q")], passo=0.01)
        self.assertEqual(tela.indice, 1)

    def test_seta_esquerda_para_no_primeiro_quadro(self):
        _, tela = self.rodar([demo.curses.KEY_LEFT, ord("q")], passo=0.01)
        self.assertEqual(tela.indice, 0)

    def test_r_volta_ao_inicio(self):
        direita = demo.curses.KEY_RIGHT
        _, tela = self.rodar([direita, direita, ord("r"), ord("q")], passo=0.01)
        self.assertEqual(tela.indice, 0)

    def test_espaco_no_fim_recomeca(self):
        total = len(demo.gerar_quadros(EXEMPLO, 22, "t"))
        teclas = [demo.curses.KEY_RIGHT] * (total - 1) + [ord(" "), ord("q")]
        _, tela = self.rodar(teclas, passo=0.01)
        self.assertEqual(tela.indice, 0)
        self.assertTrue(tela.tocando)


class TestLinhaDeComando(unittest.TestCase):
    def rodar(self, *args):
        return subprocess.run(
            [sys.executable, "demo.py", *args], cwd=RAIZ, text=True,
            capture_output=True, stdin=subprocess.DEVNULL, timeout=30,
        )

    def assert_erro(self, r, trecho):
        self.assertEqual(r.returncode, 2, r.stdout + r.stderr)
        self.assertIn(trecho, r.stderr)
        self.assertNotIn("Traceback", r.stderr)

    def test_fora_de_um_terminal(self):
        self.assert_erro(self.rodar(), "terminal")

    def test_lista_grande_demais(self):
        self.assert_erro(self.rodar("--n", str(demo.MAX_N + 1)), str(demo.MAX_N))

    def test_k_fora_da_lista(self):
        self.assert_erro(self.rodar("--k", "26"), "entre 1 e 25")

    def test_percentil_invalido(self):
        self.assert_erro(self.rodar("--percentil", "0"), "(0, 100]")

    def test_arquivo_inexistente(self):
        self.assert_erro(self.rodar("--arquivo", "nao/existe.txt"), "nao/existe.txt")

    def test_intervalo_invalido(self):
        self.assert_erro(self.rodar("--intervalo", "0"), "maior que zero")

    def test_k_e_percentil_juntos(self):
        r = self.rodar("--k", "3", "--percentil", "90")
        self.assertEqual(r.returncode, 2)
        self.assertNotIn("Traceback", r.stderr)


@unittest.skipIf(sys.platform == "win32" or demo.curses is None,
                 "pseudo-terminal só existe em Unix")
class TestNoTerminal(unittest.TestCase):
    """Roda demo.py em um pseudo-terminal, com teclas de verdade."""

    def sessao(self, passos, colunas=100, linhas=30, args=(), limite=20):
        """`passos` é uma lista de (espera em segundos, bytes a enviar)."""
        import fcntl
        import pty
        import termios

        mestre, escravo = pty.openpty()
        fcntl.ioctl(escravo, termios.TIOCSWINSZ,
                    struct.pack("HHHH", linhas, colunas, 0, 0))
        ambiente = {**os.environ, "TERM": "xterm-256color", "LC_ALL": "C.UTF-8",
                    "PYTHONDONTWRITEBYTECODE": "1"}
        proc = subprocess.Popen(
            [sys.executable, "demo.py", *args], cwd=RAIZ, env=ambiente,
            stdin=escravo, stdout=escravo, stderr=subprocess.PIPE,
        )
        os.close(escravo)
        saida = bytearray()
        fim = time.monotonic() + limite
        pendentes = list(passos)
        proxima = time.monotonic() + (pendentes[0][0] if pendentes else 0)
        while time.monotonic() < fim:
            prontos, _, _ = select.select([mestre], [], [], 0.05)
            if prontos:
                try:
                    pedaco = os.read(mestre, 65536)
                except OSError:
                    break
                if not pedaco:
                    break
                saida += pedaco
            if pendentes and time.monotonic() >= proxima:
                os.write(mestre, pendentes.pop(0)[1])
                if pendentes:
                    proxima = time.monotonic() + pendentes[0][0]
            if proc.poll() is not None and not prontos:
                break
        proc.kill() if proc.poll() is None else None
        erros = proc.stderr.read().decode()
        proc.stderr.close()
        proc.wait()
        os.close(mestre)
        return proc.returncode, saida.decode(errors="replace"), erros

    def test_abre_e_sai_com_q(self):
        codigo, saida, erros = self.sessao([(0.5, b"q")])
        self.assertEqual((codigo, erros), (0, ""))
        self.assertIn("Queremos", saida)

    def test_seta_avanca_um_quadro(self):
        codigo, saida, erros = self.sessao(
            [(0.5, b"\x1bOC"), (0.8, b"q")])
        self.assertEqual((codigo, erros), (0, ""))
        self.assertIn("Dividimos", saida)

    def test_reproducao_avanca_sozinha(self):
        codigo, saida, erros = self.sessao(
            [(0.4, b" "), (1.2, b"q")], args=("--intervalo", "0.1"))
        self.assertEqual((codigo, erros), (0, ""))
        self.assertIn("Ordenamos", saida)

    def test_chega_ao_fim_sem_erro(self):
        passos = [(0.15, b"\x1bOC")] * 20 + [(0.4, b"q")]
        codigo, saida, erros = self.sessao(passos)
        self.assertEqual((codigo, erros), (0, ""))
        self.assertIn("327 ms", saida)

    def test_terminal_pequeno_avisa_sem_quebrar(self):
        codigo, saida, erros = self.sessao([(0.5, b"q")], colunas=20, linhas=6)
        self.assertEqual((codigo, erros), (0, ""))
        self.assertIn("umente", saida)


if __name__ == "__main__":
    unittest.main()
