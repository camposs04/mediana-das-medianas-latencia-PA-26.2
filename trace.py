"""Log opcional e indentado para acompanhar a execução do algoritmo."""

_ativo: bool = False


def ativar(ligado: bool) -> None:
    """Liga ou desliga a impressão feita por `log`."""
    global _ativo
    _ativo = ligado


def log(profundidade: int, msg: str) -> None:
    """Imprime `msg` precedido de 2 espaços * `profundidade`, se ativado."""
    if _ativo:
        print("  " * profundidade + msg)
