"""Testes da CLI (issue #7). Rodam main.py de verdade, como subprocesso."""

import os
import re
import subprocess
import sys
import tempfile
import unittest

REPO = os.path.dirname(os.path.abspath(__file__))
ARQUIVO = "exemplos/latencias.txt"


def rodar(*args):
    return subprocess.run(
        [sys.executable, "main.py", *args],
        cwd=REPO, capture_output=True, text=True, timeout=60,
    )


def resultados(saida):
    """Extrai (rotulo, selecionar, sorted) das linhas de resultado."""
    return re.findall(r"^(p[\d.]+|k=\d+).*?: (-?\d+) ms \| sorted: (-?\d+) ms$",
                      saida, re.M)


class TestSaida(unittest.TestCase):
    def test_padrao_mostra_p50_p90_p99(self):
        r = rodar("--n", "1000", "--seed", "42")
        self.assertEqual(r.returncode, 0, r.stderr)
        linhas = resultados(r.stdout)
        self.assertEqual([l[0] for l in linhas], ["p50", "p90", "p99"])

    def test_resultado_bate_com_sorted(self):
        r = rodar("--n", "1000", "--seed", "42")
        linhas = resultados(r.stdout)
        self.assertEqual(len(linhas), 3)
        for _, calculado, conferencia in linhas:
            self.assertEqual(calculado, conferencia)

    def test_mesma_seed_gera_mesma_saida(self):
        primeira = rodar("--n", "500", "--seed", "1").stdout
        self.assertEqual(len(resultados(primeira)), 3)
        self.assertEqual(primeira, rodar("--n", "500", "--seed", "1").stdout)

    def test_arquivo_com_trace_mostra_a_recursao(self):
        r = rodar("--arquivo", ARQUIVO, "--percentis", "50", "--trace")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("lado:", r.stdout)
        self.assertIn("grupos:", r.stdout)
        self.assertIn("medianas:", r.stdout)
        self.assertEqual([l[0] for l in resultados(r.stdout)], ["p50"])

    def test_sem_trace_nao_mostra_a_recursao(self):
        r = rodar("--arquivo", ARQUIVO, "--percentis", "50")
        self.assertEqual(len(resultados(r.stdout)), 1)
        self.assertNotIn("grupos:", r.stdout)

    def test_k_e_um_indexado(self):
        r = rodar("--arquivo", ARQUIVO, "--k", "1")
        self.assertEqual(resultados(r.stdout), [("k=1", "22", "22")])

    def test_k_igual_a_n_devolve_o_maior(self):
        r = rodar("--arquivo", ARQUIVO, "--k", "25")
        self.assertEqual(resultados(r.stdout), [("k=25", "850", "850")])

    def test_k_sozinho_nao_mostra_percentis_padrao(self):
        r = rodar("--arquivo", ARQUIVO, "--k", "3")
        self.assertEqual(len(resultados(r.stdout)), 1)

    def test_percentil_fracionario_mantem_o_rotulo(self):
        r = rodar("--n", "1000", "--seed", "42", "--percentis", "99.9")
        self.assertEqual([l[0] for l in resultados(r.stdout)], ["p99.9"])

    def test_sem_fonte_usa_geracao(self):
        r = rodar()
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(len(resultados(r.stdout)), 3)


class TestImpressaoDaEntrada(unittest.TestCase):
    def test_trinta_elementos_sao_impressos(self):
        r = rodar("--n", "30", "--seed", "1")
        self.assertRegex(r.stdout, r"\[\d+(, \d+){29}\]")

    def test_trinta_e_um_so_mostra_o_tamanho(self):
        r = rodar("--n", "31", "--seed", "1")
        self.assertNotRegex(r.stdout, r"\[\d+, ")
        self.assertIn("31", r.stdout)


class TestErros(unittest.TestCase):
    def assert_erro(self, r, trecho):
        self.assertEqual(r.returncode, 2, r.stdout + r.stderr)
        self.assertIn(trecho, r.stderr)
        self.assertNotIn("Traceback", r.stderr)

    def test_arquivo_inexistente(self):
        self.assert_erro(rodar("--arquivo", "nao/existe.txt"), "nao/existe.txt")

    def test_diretorio_no_lugar_de_arquivo(self):
        self.assert_erro(rodar("--arquivo", "exemplos"), "exemplos")

    def test_arquivo_com_valor_invalido_cita_a_linha(self):
        with tempfile.NamedTemporaryFile("w", suffix=".txt", delete=False) as f:
            f.write("10\nabc\n")
        try:
            self.assert_erro(rodar("--arquivo", f.name), "linha 2")
        finally:
            os.unlink(f.name)

    def test_arquivo_vazio(self):
        with tempfile.NamedTemporaryFile("w", suffix=".txt", delete=False) as f:
            f.write("\n\n")
        try:
            self.assert_erro(rodar("--arquivo", f.name), "vazi")
        finally:
            os.unlink(f.name)

    def test_arquivo_binario(self):
        with tempfile.NamedTemporaryFile("wb", suffix=".txt", delete=False) as f:
            f.write(b"\xff\xfe\x00\x01")
        try:
            r = rodar("--arquivo", f.name)
            self.assertEqual(r.returncode, 2)
            self.assertNotIn("Traceback", r.stderr)
        finally:
            os.unlink(f.name)

    def test_n_zero(self):
        self.assert_erro(rodar("--n", "0"), "n deve ser")

    def test_n_nao_numerico(self):
        self.assert_erro(rodar("--n", "abc"), "inteiro")

    def test_percentil_zero(self):
        self.assert_erro(rodar("--percentis", "0"), "(0, 100]")

    def test_percentil_acima_de_100(self):
        self.assert_erro(rodar("--percentis", "50", "101"), "(0, 100]")

    def test_percentil_nao_numerico(self):
        self.assert_erro(rodar("--percentis", "abc"), "número")

    def test_percentil_nan(self):
        self.assert_erro(rodar("--percentis", "nan"), "(0, 100]")

    def test_k_zero_fala_em_um_indexado(self):
        self.assert_erro(rodar("--arquivo", ARQUIVO, "--k", "0"), "entre 1 e 25")

    def test_k_acima_de_n(self):
        self.assert_erro(rodar("--arquivo", ARQUIVO, "--k", "26"), "entre 1 e 25")

    def test_n_e_arquivo_juntos(self):
        r = rodar("--n", "10", "--arquivo", ARQUIVO)
        self.assertEqual(r.returncode, 2)
        self.assertNotIn("Traceback", r.stderr)


class TestPipeFechado(unittest.TestCase):
    """O leitor fecha o pipe antes do fim, como em `main.py | head -1`."""

    def rodar_com_leitor_que_fecha(self, *args, linhas_lidas=0):
        proc = subprocess.Popen(
            [sys.executable, "main.py", *args], cwd=REPO, text=True,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        )
        for _ in range(linhas_lidas):
            proc.stdout.readline()
        proc.stdout.close()
        erros = proc.stderr.read()
        proc.stderr.close()
        proc.wait(timeout=60)
        return erros

    def test_saida_longa_termina_sem_traceback(self):
        erros = self.rodar_com_leitor_que_fecha(
            "--n", "100000", "--seed", "1", "--trace", linhas_lidas=1)
        self.assertEqual(erros, "")

    def test_saida_curta_termina_sem_aviso(self):
        erros = self.rodar_com_leitor_que_fecha("--arquivo", ARQUIVO)
        self.assertEqual(erros, "")


if __name__ == "__main__":
    unittest.main()
