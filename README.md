# mediana-das-medianas-latencia

Calcula percentis de latência (p50, p90, p99) sem ordenar a lista. Um percentil é o k-ésimo menor valor, então basta um algoritmo de seleção. Este projeto usa a Mediana das Medianas (BFPRT), que roda em O(n) mesmo no pior caso.

## Como rodar

Requer Python 3.10+ e não tem dependências externas.

```bash
# Gera 1000 latências reproduzíveis e mostra p50, p90 e p99
python main.py --n 1000 --seed 42

# Lê um arquivo e mostra a recursão passo a passo
python main.py --arquivo exemplos/latencias.txt --percentis 90 --trace

# Pede o 3º menor valor (na CLI, k começa em 1)
python main.py --arquivo exemplos/latencias.txt --k 3
```

Saída do primeiro comando:

```text
Entrada: n=1000 (geradas, seed 42)

p50: 76 ms | sorted: 76 ms
p90: 320 ms | sorted: 320 ms
p99: 867 ms | sorted: 867 ms
```

O primeiro valor de cada linha vem de `selecionar`. O valor de `sorted` serve só como conferência.

| Opção | Efeito |
| --- | --- |
| `--n N` | Gera `N` latências (padrão: 1000). Não combina com `--arquivo`. |
| `--seed S` | Fixa a semente da geração. |
| `--arquivo CAMINHO` | Lê uma latência por linha. |
| `--percentis P [P ...]` | Percentis em (0, 100] (padrão: 50 90 99). |
| `--k K` | Pede o k-ésimo menor, de 1 a n. Sozinho, dispensa os percentis padrão. |
| `--trace` | Mostra cada nível da recursão. |

Listas com até 30 elementos são impressas. Acima disso, só o tamanho aparece.

## Animação no terminal

```bash
python demo.py
```

A tela pede os números separados por espaço e depois o índice, e mostra a seleção uma etapa por vez. O índice começa em 0: `0` é o menor valor e `n-1` é o maior. Enter vazio usa `exemplos/latencias.txt` na lista e a mediana no índice. São aceitos até 60 inteiros, inclusive negativos e repetidos.

Usa o `curses` da biblioteca padrão e chama o `selecionar` de verdade, então o que aparece na tela é o que o código fez. Precisa de um terminal com pelo menos 80 colunas por 24 linhas para as listas maiores. No Windows, instale antes o pacote `windows-curses`, porque o Python de lá não traz o `curses`.

| Tecla | Efeito |
| --- | --- |
| Espaço | Reproduz ou pausa |
| Seta direita e seta esquerda | Avança ou volta uma etapa |
| `r` | Volta ao início |
| `n` | Digita outra lista e outro índice |
| `q` | Sai |

Passar uma entrada na linha de comando pula as perguntas e abre a animação direto:

```bash
python demo.py --arquivo exemplos/latencias.txt --percentil 90
```

| Opção | Efeito |
| --- | --- |
| `--arquivo CAMINHO` | Lê uma latência por linha. |
| `--n N` | Gera `N` latências, até 60. Não combina com `--arquivo`. |
| `--seed S` | Fixa a semente da geração. |
| `--percentil P` | Percentil em (0, 100] (padrão: 90). Não combina com `--k`. |
| `--k K` | Pede o k-ésimo menor, de 1 a n. Aqui a contagem começa em 1, como no `main.py`. |
| `--intervalo S` | Segundos em cada etapa ao reproduzir (padrão: 3). |

## Testes

```bash
python -m unittest
```

Rode da raiz do repositório. Os testes usam só a biblioteca padrão: `test_selecao.py` cobre a seleção, `test_main.py` executa a CLI e `test_demo.py` confere os quadros, o layout e a animação em um pseudo-terminal, parte que não roda no Windows.

## Algoritmo

Para achar o elemento de índice k em n valores:

1. Com n ≤ 5, ordena e devolve o resultado.
2. Divide a lista em grupos de 5. O último pode ter menos.
3. Acha a mediana de cada grupo com insertion sort, em O(1) por grupo.
4. Chama a seleção sobre as medianas para obter a mediana delas, que é o pivô.
5. Particiona a lista em menores, iguais e maiores que o pivô. A parte `iguais` absorve os valores repetidos, comuns em latências, e garante que a recursão termina.
6. Sendo `m` e `i` os tamanhos de menores e iguais, recorre em um lado só: menores se `k < m`, devolve o pivô se `k < m + i`, e senão maiores com `k - m - i`.

Metade das cerca de n/5 medianas é menor ou igual ao pivô, e cada uma delas tem 3 elementos do próprio grupo menores ou iguais a ela. Logo, pelo menos 3n/10 elementos, a menos de uma constante, ficam de cada lado do pivô, e o maior lado tem no máximo cerca de 7n/10. Isso dá a recorrência:

```text
T(n) ≤ T(n/5) + T(7n/10) + O(n)
```

Como 1/5 + 7/10 = 9/10 < 1, o trabalho cai por um fator constante a cada nível e a soma geométrica fica limitada: com o termo linear igual a cn, T(n) ≤ 10cn, ou seja, O(n). O tamanho 5 importa: com grupos de 3, as frações somam 1/3 + 2/3 = 1 e o custo sobe para O(n log n).

O percentil vira posição pela regra nearest-rank: `k = ⌈p·n/100⌉ - 1`.

## Mapa do código

| Arquivo | Função | Passo do algoritmo |
| --- | --- | --- |
| `dados.py` | `gerar_latencias`, `ler_latencias` | Obtém a entrada |
| `dados.py` | `k_do_percentil` | Converte o percentil em k |
| `pivo.py` | `dividir_em_grupos` | Passo 2 |
| `pivo.py` | `mediana_do_grupo` | Passo 3 |
| `pivo.py` | `mediana_das_medianas` | Passo 4 |
| `selecao.py` | `particionar` | Passo 5 |
| `selecao.py` | `selecionar` | Passos 1 e 6 |
| `trace.py` | `ativar`, `log` | Log indentado por profundidade |
| `main.py` | `main` | CLI e impressão dos resultados |
| `demo.py` | `gerar_quadros`, `Tela` | Animação no terminal |

`pivo.py` recebe a função de seleção por parâmetro, o que evita a importação circular com `selecao.py`.

## Exemplo com `--trace`

Saída de `python main.py --arquivo exemplos/latencias.txt --percentis 90 --trace`, sem a impressão da entrada. Cada nível de indentação é uma chamada recursiva, tanto para achar o pivô quanto para seguir um lado da partição.

```text
--- p90: selecionar(k=22) ---
selecionar: k=22, n=25
grupos: 5, tamanhos [5, 5, 5, 5, 5]
medianas: [64, 73, 67, 78, 70]
  selecionar: k=2, n=5
  caso base: 70
pivô: 70
partição: menores=12, iguais=1, maiores=12
lado: maiores
  selecionar: k=9, n=12
  grupos: 3, tamanhos [5, 5, 2]
  medianas: [91, 105, 86]
    selecionar: k=1, n=3
    caso base: 91
  pivô: 91
  partição: menores=4, iguais=1, maiores=7
  lado: maiores
    selecionar: k=4, n=7
    grupos: 2, tamanhos [5, 2]
    medianas: [118, 113]
      selecionar: k=0, n=2
      caso base: 113
    pivô: 113
    partição: menores=2, iguais=1, maiores=4
    lado: maiores
      selecionar: k=1, n=4
      caso base: 327
p90: 327 ms | sorted: 327 ms
```

## Autores

- [camposs04](https://github.com/camposs04): estrutura do repositório, dados, trace, grupos e escolha do pivô (issues #1 a #4).
- [Diogo-Olivv](https://github.com/Diogo-Olivv): particionamento, seleção recursiva, CLI e README (issues #5 a #8).
