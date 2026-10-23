from dataclasses import dataclass
from typing import Literal

type Type = Literal["int", "double", "char", "bool"]
type ReturnType = Type | Literal["void"]

# ALTERADO (23/10/2026): antes havia um `Unary(op, operand)` e um
# `Binary(op, left, right)`, com o operador guardado num campo (`UnaryOp` e
# `BinaryOp`, dois `Literal`). Agora há uma classe por operador, como o
# `Add`/`Mul` da teórica e do TP5: o operador fica no tipo do nó.
type Exp = (
    IntLit | FloatLit | CharLit | StringLit | BoolLit
    | Var | Index | Call | Cast
    | Pos | Neg | Not                            # unários
    | Or | And                                   # lógicos
    | Eq | Neq                                   # igualdade
    | Lt | Le | Gt | Ge                          # comparação
    | Add | Sub                                  # aditivos
    | Mul | Div | Mod                            # multiplicativos
)

type Stmt = (
    Block | VarDecl | ArrayDecl | Assign | IndexAssign
    | If | While | For | Return | Print | Read
    | Break | Continue | CallStmt
)

type Decl = VarDecl | ArrayDecl | FuncDef
type ForInit = VarDecl | ArrayDecl | Assign | IndexAssign
type ForUpdate = Exp | Assign | IndexAssign


# --------------------------------------------------------------------- Expressões

@dataclass
class IntLit:
    value: int

@dataclass
class FloatLit:
    value: float

@dataclass
class CharLit:
    value: str              # sem as plicas: 'A' -> "A"

@dataclass
class StringLit:
    value: str              # sem as aspas

@dataclass
class BoolLit:
    value: bool

@dataclass
class Var:
    name: str

@dataclass
class Index:                # postfix -> primary "[" expression "]"
    array: Exp
    index: Exp

@dataclass
class Call:                 # function_call -> primary "(" argument_list_optional ")"
    function: Exp           # a gramática aceita qualquer `primary`, não só nomes
    args: list[Exp]

@dataclass
class Cast:                 # unary -> "(" type ")" unary
    target: Type
    operand: Exp

# Unários: unary -> unary_operator unary

@dataclass
class Pos:                  # +e
    operand: Exp

@dataclass
class Neg:                  # -e
    operand: Exp

@dataclass
class Not:                  # !e
    operand: Exp

# Binários, do nível de precedência mais fraco (`||`) para o mais forte (`*`)

@dataclass
class Or:                   # ||
    left: Exp
    right: Exp

@dataclass
class And:                  # &&
    left: Exp
    right: Exp

@dataclass
class Eq:                   # ==
    left: Exp
    right: Exp

@dataclass
class Neq:                  # !=
    left: Exp
    right: Exp

@dataclass
class Lt:                   # <
    left: Exp
    right: Exp

@dataclass
class Le:                   # <=
    left: Exp
    right: Exp

@dataclass
class Gt:                   # >
    left: Exp
    right: Exp

@dataclass
class Ge:                   # >=
    left: Exp
    right: Exp

@dataclass
class Add:                  # +
    left: Exp
    right: Exp

@dataclass
class Sub:                  # -
    left: Exp
    right: Exp

@dataclass
class Mul:                  # *
    left: Exp
    right: Exp

@dataclass
class Div:                  # /
    left: Exp
    right: Exp

@dataclass
class Mod:                  # %
    left: Exp
    right: Exp


# --------------------------------------------------------------------- Declarações

@dataclass
class VarDecl:              # type IDENTIFIER variable_initializer
    var_type: Type
    name: str
    init: Exp | None

@dataclass
class ArrayDecl:            # type IDENTIFIER "[" INTEGER "]" array_declaration_initializer
    elem_type: Type
    name: str
    size: int
    init: list[Exp] | None  # None: sem inicializador; []: "= {}"


# --------------------------------------------------------------------- Instruções

@dataclass
class Assign:               # IDENTIFIER "=" expression
    name: str
    value: Exp

@dataclass
class IndexAssign:          # IDENTIFIER "[" expression "]" "=" expression
    name: str
    index: Exp
    value: Exp

@dataclass
class Block:                # "{" statement_list "}"
    stmts: list[Stmt]

@dataclass
class If:                   # "if" "(" expression ")" statement else_clause
    cond: Exp
    then: Stmt
    orelse: Stmt | None

@dataclass
class While:
    cond: Exp
    body: Stmt

@dataclass
class For:                  # as três partes são opcionais
    init: ForInit | None
    cond: Exp | None
    update: ForUpdate | None
    body: Stmt

@dataclass
class Return:               # a gramática obriga a ter expressão: não há `return;`
    value: Exp

@dataclass
class Print:
    value: Exp

@dataclass
class Read:                 # "read" "(" IDENTIFIER ")" ";"
    name: str

@dataclass
class Break:
    pass

@dataclass
class Continue:
    pass

@dataclass
class CallStmt:             # function_call ";"
    call: Call


# --------------------------------------------------------------------- Programa

@dataclass
class Param:
    param_type: Type
    name: str

@dataclass
class FuncDef:
    return_type: ReturnType
    name: str
    params: list[Param]
    body: Block

@dataclass
class Program:              # program -> declaration_list
    decls: list[Decl]
