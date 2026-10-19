"""Faz o parsing de programas SDVM e imprime a AST em árvore.

Uso (a partir de src/david, com o venv ativo):
  python main.py <ficheiro> [<ficheiro> ...]   imprime a AST de cada ficheiro
  python main.py --all                         testa todos os exemplos da spec (OK/FALHA)
"""

import sys
from dataclasses import fields, is_dataclass
from pathlib import Path

from parsy import ParseError

from parser_sdvm_david import program

EXAMPLES = Path(__file__).resolve().parents[2] / "spec" / "examples"


def show(node, indent=0):
    """Representação da AST com um nó por linha, indentada pela profundidade."""
    pad = "  " * indent
    if isinstance(node, list):
        return "\n".join(show(item, indent) for item in node)
    if not is_dataclass(node):
        return pad + repr(node)

    name = type(node).__name__
    values = [(f.name, getattr(node, f.name)) for f in fields(node)]

    # Nós sem filhos ficam numa linha só: Var('x'), IntLit(3), Break
    if all(not is_dataclass(v) and not isinstance(v, list) for _, v in values):
        args = ", ".join(repr(v) for _, v in values)
        return f"{pad}{name}({args})" if values else pad + name

    lines = [pad + name]
    for field, value in values:
        if is_dataclass(value) or (isinstance(value, list) and value):
            lines.append(f"{pad}  {field}:")
            lines.append(show(value, indent + 2))
        else:
            lines.append(f"{pad}  {field}: {value!r}")
    return "\n".join(lines)


def parse_file(path):
    return program.parse(Path(path).read_text(encoding="utf-8"))


def print_ast(path):
    try:
        ast = parse_file(path)
    except ParseError as e:
        print(f"=== {path}: erro de sintaxe\n{e}")
        return False

    # ALTERADO (19/10/2026): antes, um ficheiro inexistente fazia o programa
    # terminar com o erro técnico do Python (FileNotFoundError). Agora mostra uma
    # mensagem clara e continua com os outros ficheiros (ideia da versão do Maia).
    except FileNotFoundError:
        print(f"=== {path}: o ficheiro não existe")
        return False

    print(f"=== {path}")
    print(show(ast))
    return True


def check_examples():
    files = sorted(p for p in EXAMPLES.iterdir() if p.is_file())
    ok = 0
    for path in files:
        try:
            parse_file(path)
        except ParseError as e:
            print(f"FALHA  {path.name}: {e}")
        else:
            print(f"OK     {path.name}")
            ok += 1
    print(f"\n{ok}/{len(files)} exemplos reconhecidos")
    return ok == len(files)


def main(args):
    if not args:
        print(__doc__)
        return 2
    if args == ["--all"]:
        return 0 if check_examples() else 1
    results = [print_ast(path) for path in args]
    return 0 if all(results) else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
