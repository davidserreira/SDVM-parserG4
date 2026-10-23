# Parser da linguagem SDVM com parser combinators (parsy).
# Gramática: spec/README.md (repositório da turma). AST: ast_sdvm_david.py.
#
# Cada não-terminal da gramática tem um parser com o mesmo nome. As produções
# `*_tail` não aparecem: são a forma recursiva à direita de `X (op X)*`, que aqui
# se escreve com `.many()` (teórica, secção 2.4).
#
# Diferença importante em relação à teórica: no parsy o `|` é *escolha ordenada*
# (fica com a primeira alternativa que tem sucesso), não a "list of successes".
# Por isso a ordem das alternativas importa onde há prefixos comuns.

import re
from functools import reduce

from parsy import alt, eof, fail, forward_declaration, generate, regex, seq, string, success

from ast_sdvm_david import *

# --------------------------------------------------------------------- Léxico

# Espaços e comentários (`//` e `/* */`) são ignorados.
ignore = (
    regex(r"\s+")
    | regex(r"//[^\n]*")
    | regex(r"/\*.*?\*/", flags=re.DOTALL)
).many()


def lexeme(p):
    """Token seguido de espaços/comentários (o `token'` da teórica, secção 2.1)."""
    return p << ignore


def symbol(s):
    return lexeme(string(s))


# ALTERADO (23/10/2026): antes recebia só os símbolos e devolvia a string do
# operador (para o `op` do `Binary`). Agora recebe um dicionário símbolo -> classe
# do nó, e cada símbolo devolve a sua classe: é o `Add <$ symbol "+"` da teórica.
def operators(table):
    """Alternativa entre operadores. Os mais compridos têm de vir primeiro (`<=` antes de `<`)."""
    return alt(*(symbol(op).result(node) for op, node in table.items()))


KEYWORDS = {
    "int", "double", "char", "bool", "void",
    "if", "else", "while", "for", "break", "continue", "return",
    "print", "read", "true", "false",
}


def keyword(k):
    # `\b` impede que `if` reconheça o início de `iffy`
    return lexeme(regex(rf"{k}\b"))


def not_keyword(name):
    return fail("identifier") if name in KEYWORDS else success(name)


identifier = lexeme(regex(r"[A-Za-z][A-Za-z0-9_]*").bind(not_keyword))

# `=` de atribuição não pode ser o início de `==`
assign_op = lexeme(regex(r"=(?!=)"))

ESCAPES = {"n": "\n", "t": "\t", "r": "\r", "0": "\0", "\\": "\\", "'": "'", '"': '"'}


def unescape(s):
    return re.sub(r"\\(.)", lambda m: ESCAPES.get(m.group(1), m.group(1)), s)


integer = lexeme(regex(r"[0-9]+")).map(int)
FLOAT = lexeme(regex(r"[0-9]+\.[0-9]+([eE][+-]?[0-9]+)?")).map(lambda s: FloatLit(float(s)))
INTEGER = integer.map(IntLit)
CHAR = lexeme(regex(r"'([^'\\]|\\.)'")).map(lambda s: CharLit(unescape(s[1:-1])))
STRING = lexeme(regex(r'"([^"\\]|\\.)*"')).map(lambda s: StringLit(unescape(s[1:-1])))

# --------------------------------------------------------------------- Tipos

type_ = alt(*(keyword(t) for t in ("int", "double", "char", "bool")))
return_type = type_ | keyword("void")

# --------------------------------------------------------------------- Expressões

expression = forward_declaration()
unary = forward_declaration()


def left(ops, operand):
    """Combinador `left` da teórica (secção 2.4): operand (ops operand)*,
    dobrado da esquerda com `reduce` para ficar associativo à esquerda.
    Cada par de `rest` é (classe do nó, operando direito), p.ex. (Sub, IntLit(3))."""
    @generate
    def parser():
        first = yield operand
        rest = yield seq(ops, operand).many()
        return reduce(lambda acc, op_right: op_right[0](acc, op_right[1]), rest, first)
    return parser


argument_list_optional = expression.sep_by(symbol(","))

primary = (
    FLOAT                       # antes de INTEGER: senão `3.14` lia só o `3`
    | INTEGER
    | CHAR
    | STRING
    | keyword("true").result(BoolLit(True))
    | keyword("false").result(BoolLit(False))
    | identifier.map(Var)
    | symbol("(") >> expression << symbol(")")
)


@generate
def postfix():
    # postfix -> primary | primary "[" expression "]" | primary "(" args ")"
    # As três alternativas começam por `primary`: em vez de o reconhecer três
    # vezes, reconhece-se uma vez e depois vê-se o que vem a seguir.
    base = yield primary
    index = yield (symbol("[") >> expression << symbol("]")).optional()
    if index is not None:
        return Index(base, index)
    args = yield (symbol("(") >> argument_list_optional << symbol(")")).optional()
    if args is not None:
        return Call(base, args)
    return base


cast = seq(symbol("(") >> type_ << symbol(")"), unary).combine(Cast)
unary_operation = seq(
    operators({"+": Pos, "-": Neg, "!": Not}), unary
).combine(lambda node, operand: node(operand))

# O cast vem antes de `postfix`, porque `(int) x` e `(x)` começam ambos por `(`.
# Unários e casts são recursivos à direita, logo associativos à direita.
unary.become(unary_operation | cast | postfix)

multiplicative = left(operators({"*": Mul, "/": Div, "%": Mod}), unary)
additive = left(operators({"+": Add, "-": Sub}), multiplicative)
comparison = left(operators({"<=": Le, ">=": Ge, "<": Lt, ">": Gt}), additive)
equality = left(operators({"==": Eq, "!=": Neq}), comparison)
logical_and = left(operators({"&&": And}), equality)
expression.become(left(operators({"||": Or}), logical_and))

# --------------------------------------------------------------------- Declarações

array_initializer = symbol("{") >> expression.sep_by(symbol(",")) << symbol("}")


@generate
def variable_declaration_core():
    var_type = yield type_
    name = yield identifier
    size = yield (symbol("[") >> integer << symbol("]")).optional()
    if size is None:
        init = yield (assign_op >> expression).optional()
        return VarDecl(var_type, name, init)
    init = yield (assign_op >> array_initializer).optional()
    return ArrayDecl(var_type, name, size, init)


variable_declaration = variable_declaration_core << symbol(";")

# --------------------------------------------------------------------- Instruções

statement = forward_declaration()

block = (symbol("{") >> statement.many() << symbol("}")).map(Block)


@generate
def assignment_core():
    name = yield identifier
    index = yield (symbol("[") >> expression << symbol("]")).optional()
    yield assign_op
    value = yield expression
    if index is None:
        return Assign(name, value)
    return IndexAssign(name, index, value)


assignment = assignment_core << symbol(";")


@generate
def if_statement():
    yield keyword("if")
    cond = yield symbol("(") >> expression << symbol(")")
    then = yield statement
    # O `else` fica com o `if` mais próximo (como em C), porque o `optional` é guloso.
    orelse = yield (keyword("else") >> statement).optional()
    return If(cond, then, orelse)


@generate
def while_statement():
    yield keyword("while")
    cond = yield symbol("(") >> expression << symbol(")")
    body = yield statement
    return While(cond, body)


@generate
def for_statement():
    yield keyword("for")
    yield symbol("(")
    init = yield (variable_declaration_core | assignment_core).optional()
    yield symbol(";")
    cond = yield expression.optional()
    yield symbol(";")
    # A gramática diz `expression_optional`, mas os exemplos da turma usam
    # atribuições (`i = i + 1`). Aceitam-se as duas; a atribuição primeiro.
    update = yield (assignment_core | expression).optional()
    yield symbol(")")
    body = yield statement
    return For(init, cond, update, body)


return_statement = (keyword("return") >> expression << symbol(";")).map(Return)
print_statement = (keyword("print") >> symbol("(") >> expression << symbol(")") << symbol(";")).map(Print)
read_statement = (keyword("read") >> symbol("(") >> identifier << symbol(")") << symbol(";")).map(Read)
break_statement = (keyword("break") >> symbol(";")).map(lambda _: Break())
continue_statement = (keyword("continue") >> symbol(";")).map(lambda _: Continue())

function_call = seq(primary, symbol("(") >> argument_list_optional << symbol(")")).combine(Call)
call_statement = (function_call << symbol(";")).map(CallStmt)

statement.become(
    block
    | variable_declaration
    | if_statement
    | while_statement
    | for_statement
    | return_statement
    | print_statement
    | read_statement
    | break_statement
    | continue_statement
    | assignment                # IDENTIFIER ... "=" ...
    | call_statement            # IDENTIFIER "(" ... — se não for atribuição, tenta chamada
)

# --------------------------------------------------------------------- Programa

parameter = seq(type_, identifier).combine(Param)


@generate
def function_definition():
    ret = yield return_type
    name = yield identifier
    params = yield symbol("(") >> parameter.sep_by(symbol(",")) << symbol(")")
    body = yield block
    return FuncDef(ret, name, params, body)


# `int f(...) {...}` e `int x;` começam ambos por `type IDENTIFIER`: tenta-se a
# função e, se falhar no `(`, o parsy volta atrás e tenta a variável.
declaration = function_definition | variable_declaration

# ALTERADO (19/10/2026), só comentário: o `.parse()` do parsy já exige chegar ao
# fim do texto, por isso o lixo no fim seria rejeitado mesmo sem `eof`. O `eof`
# fica para tornar a regra explícita e para valer também com `parse_partial`.
program = (ignore >> declaration.many() << eof).map(Program)
