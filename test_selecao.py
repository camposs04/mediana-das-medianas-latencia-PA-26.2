"""Testes de particionar e selecionar (issues #5 e #6)."""

import contextlib
import io
import random
import unittest

import pivo
import selecao
import trace
from selecao import particionar, selecionar


def capturar_trace(funcao, *args):
    saida = io.StringIO()
    trace.ativar(True)
    try:
        with contextlib.redirect_stdout(saida):
            resultado = funcao(*args)
    finally:
        trace.ativar(False)
    return resultado, saida.getvalue()


class ListaContada(list):
    """Lista que conta quantas vezes foi percorrida do início."""

    def __init__(self, *args):
        super().__init__(*args)
        self.passadas = 0

    def __iter__(self):
        self.passadas += 1
        return super().__iter__()


class TestParticionar(unittest.TestCase):
    def test_separa_em_tres_partes_na_ordem_de_entrada(self):
        self.assertEqual(
            particionar([5, 1, 5, 9, 3], 5),
            ([1, 3], [5, 5], [9]),
        )

    def test_soma_dos_tamanhos_preserva_a_lista(self):
        gerador = random.Random(1)
        lista = [gerador.randint(0, 20) for _ in range(500)]
        menores, iguais, maiores = particionar(lista, 10)
        self.assertEqual(len(menores) + len(iguais) + len(maiores), len(lista))
        self.assertEqual(sorted(menores + iguais + maiores), sorted(lista))

    def test_todos_iguais_ficam_em_iguais(self):
        self.assertEqual(particionar([7] * 6, 7), ([], [7] * 6, []))

    def test_faz_uma_unica_passada(self):
        # Critério da #5: três compreensões de lista fariam 3 passadas.
        lista = ListaContada([3, 1, 2])
        particionar(lista, 2)
        self.assertEqual(lista.passadas, 1)

    def test_nao_altera_a_entrada(self):
        lista = [3, 1, 2]
        particionar(lista, 2)
        self.assertEqual(lista, [3, 1, 2])

    def test_trace_registra_os_tamanhos_das_tres_partes(self):
        _, saida = capturar_trace(particionar, [1, 2, 2, 3, 4], 2)
        self.assertRegex(saida, r"menores\D*1\b")
        self.assertRegex(saida, r"iguais\D*2\b")
        self.assertRegex(saida, r"maiores\D*2\b")

    def test_sem_trace_nao_imprime(self):
        saida = io.StringIO()
        with contextlib.redirect_stdout(saida):
            particionar([1, 2, 3], 2)
        self.assertEqual(saida.getvalue(), "")


class TestSelecionarContrato(unittest.TestCase):
    def test_caso_base_com_cinco_elementos(self):
        self.assertEqual(selecionar([5, 1, 4, 2, 3], 2), 3)

    def test_um_elemento(self):
        self.assertEqual(selecionar([42], 0), 42)

    def test_caso_base_nao_escolhe_pivo(self):
        original = selecao.mediana_das_medianas
        chamadas = []
        selecao.mediana_das_medianas = lambda *a: chamadas.append(a) or original(*a)
        try:
            selecionar([5, 1, 4, 2, 3], 0)
        finally:
            selecao.mediana_das_medianas = original
        self.assertEqual(chamadas, [])

    def test_lista_vazia_da_erro(self):
        with self.assertRaisesRegex(ValueError, "vazia"):
            selecionar([], 0)

    def test_k_negativo_da_erro(self):
        # Sem a checagem, sorted(l)[-1] devolveria o maior valor.
        with self.assertRaisesRegex(ValueError, "k"):
            selecionar([1, 2, 3], -1)

    def test_k_igual_a_n_da_erro(self):
        with self.assertRaisesRegex(ValueError, "k"):
            selecionar([1, 2, 3], 3)

    def test_nao_altera_a_entrada(self):
        lista = [9, 3, 7, 1, 8, 2, 6, 4, 5, 0, 11, 10]
        copia = lista.copy()
        selecionar(lista, 6)
        self.assertEqual(lista, copia)


class TestSelecionarUsaOPivo(unittest.TestCase):
    def test_lista_grande_passa_pela_mediana_das_medianas(self):
        # Acima de 5 elementos, o pivô tem de vir de pivo.py.
        original = selecao.mediana_das_medianas
        chamadas = []

        def espiao(lista, selecionar_fn, profundidade=0):
            chamadas.append(len(lista))
            return original(lista, selecionar_fn, profundidade)

        selecao.mediana_das_medianas = espiao
        try:
            selecionar(list(range(100)), 50)
        finally:
            selecao.mediana_das_medianas = original
        self.assertIn(100, chamadas)

    def test_recursao_vai_a_um_lado_so(self):
        # Em cada nível, só um lado da partição é visitado.
        lista = list(range(125))
        random.Random(3).shuffle(lista)
        pivos_por_tamanho = []
        original = selecao.particionar

        def espiao(entrada, pivo_escolhido, *resto):
            partes = original(entrada, pivo_escolhido, *resto)
            pivos_por_tamanho.append((len(entrada), partes))
            return partes

        selecao.particionar = espiao
        try:
            selecionar(lista, 10)
        finally:
            selecao.particionar = original
        # Um lado só implica soma geométrica, e não n log n.
        self.assertTrue(pivos_por_tamanho, "nenhuma partição foi feita")
        self.assertLess(sum(t for t, _ in pivos_por_tamanho), 10 * len(lista))

    def test_trace_mostra_k_n_e_lado(self):
        _, saida = capturar_trace(selecionar, list(range(30)), 2)
        self.assertIn("k=2", saida)
        self.assertIn("n=30", saida)
        self.assertRegex(saida, r"lado: (menores|iguais|maiores)")

    def test_trace_indenta_a_recursao(self):
        _, saida = capturar_trace(selecionar, list(range(30)), 2)
        self.assertTrue(any(l.startswith("  ") for l in saida.splitlines()))


class TestSelecionarContraOraculo(unittest.TestCase):
    def conferir_todos_os_k(self, lista):
        ordenada = sorted(lista)
        for k in range(len(lista)):
            self.assertEqual(selecionar(lista, k), ordenada[k], f"k={k}")

    def test_todos_os_tamanhos_ate_60(self):
        gerador = random.Random(7)
        for n in range(1, 61):
            self.conferir_todos_os_k([gerador.randint(0, 50) for _ in range(n)])

    def test_cem_elementos(self):
        gerador = random.Random(11)
        self.conferir_todos_os_k([gerador.randint(0, 10**6) for _ in range(100)])

    def test_padroes_ruins_para_quickselect(self):
        n = 200
        casos = {
            "crescente": list(range(n)),
            "decrescente": list(range(n, 0, -1)),
            "todos iguais": [5] * n,
            "dois valores": [i % 2 for i in range(n)],
            "tres valores": [i % 3 for i in range(n)],
            "montanha": list(range(n // 2)) + list(range(n // 2, 0, -1)),
            "cauda longa": [1] * 180 + [1000] * 20,
        }
        for nome, lista in casos.items():
            with self.subTest(nome):
                self.conferir_todos_os_k(lista)

    def test_negativos(self):
        self.conferir_todos_os_k([-5, 3, -1, 0, 7, -9, 2, 2, -5, 8, 1])


class TestGarantiasDoAlgoritmo(unittest.TestCase):
    def fatias(self, lista, k=None):
        """Coleta (n, maior lado) de toda partição feita por uma seleção."""
        registros = []
        original = selecao.particionar

        def espiao(entrada, pivo_escolhido, *resto):
            partes = original(entrada, pivo_escolhido, *resto)
            registros.append((len(entrada), max(len(partes[0]), len(partes[2]))))
            return partes

        selecao.particionar = espiao
        try:
            selecionar(lista, len(lista) // 2 if k is None else k)
        finally:
            selecao.particionar = original
        return registros

    def test_maior_lado_respeita_7n_sobre_10(self):
        # Limite clássico: cada lado tem no máximo 7n/10 + 6 elementos.
        gerador = random.Random(13)
        for n in [10, 50, 137, 1000, 5000]:
            for lista in (
                [gerador.randint(0, 10**9) for _ in range(n)],
                [gerador.randint(0, 3) for _ in range(n)],
                list(range(n)),
            ):
                registros = self.fatias(lista)
                self.assertTrue(registros, "nenhuma partição foi feita")
                for tamanho, maior in registros:
                    self.assertLessEqual(maior, 0.7 * tamanho + 6)

    def test_trabalho_cresce_linearmente(self):
        # A soma dos tamanhos particionados por n fica estável ao crescer n.
        def razao(n):
            lista = list(range(n))
            random.Random(n).shuffle(lista)
            return sum(t for t, _ in self.fatias(lista)) / n

        self.assertLess(razao(64000) / razao(4000), 1.25)

    def test_profundidade_nao_estoura_a_pilha(self):
        self.assertEqual(selecionar(list(range(200000)), 100000), 100000)


class TestPivoIntegrado(unittest.TestCase):
    def test_grupos_padrao_tem_cinco_elementos(self):
        # Grupos de 3 viram O(n log n) sem quebrar nenhuma resposta.
        grupos = pivo.dividir_em_grupos(list(range(12)))
        self.assertEqual([len(g) for g in grupos], [5, 5, 2])

    def test_mediana_das_medianas_com_selecionar_real_coincide_com_sorted(self):
        gerador = random.Random(17)
        lista = [gerador.randint(0, 999) for _ in range(25)]
        real = pivo.mediana_das_medianas(lista, selecionar)
        conferencia = pivo.mediana_das_medianas(lista, lambda l, k, p=0: sorted(l)[k])
        self.assertEqual(real, conferencia)


if __name__ == "__main__":
    unittest.main()
