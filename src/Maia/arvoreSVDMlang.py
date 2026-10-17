from dataclasses import dataclass
from typing import List, Optional

class ASTNode: pass
class Exp(ASTNode): pass
class Stmt(ASTNode): pass

# --- EXPRESSÕES ---
@dataclass
class IntVal(Exp):
    value: int

@dataclass
class StringVal(Exp):
    value: str

@dataclass
class Var(Exp):
    name: str

@dataclass
class ArrayAccess(Exp):
    name: str
    index: Exp

@dataclass
class BinOp(Exp):
    op: str
    left: Exp
    right: Exp

@dataclass
class FuncCall(Exp):
    name: str
    args: List[Exp]

# --- INSTRUÇÕES (STATEMENTS) ---
@dataclass
class VarDecl(Stmt):
    var_type: str
    name: str
    is_array: bool
    array_size: Optional[Exp]
    expr: Optional[Exp]
    array_elements: Optional[List[Exp]]

@dataclass
class Assign(Stmt):
    target: Exp  # Pode ser Var ou ArrayAccess
    expr: Exp

@dataclass
class If(Stmt):
    condition: Exp
    true_body: List[Stmt]
    false_body: List[Stmt]

@dataclass
class While(Stmt):
    condition: Exp
    body: List[Stmt]

@dataclass
class For(Stmt):
    init: Stmt
    condition: Exp
    update: Stmt
    body: List[Stmt]

@dataclass
class Return(Stmt):
    expr: Optional[Exp]

@dataclass
class Break(Stmt):
    pass

@dataclass
class Continue(Stmt):
    pass

@dataclass
class ExprStmt(Stmt):
    expr: Exp

# --- ESTRUTURAS GLOBAIS ---
@dataclass
class FuncDef(ASTNode):
    return_type: str
    name: str
    params: List[tuple[str, str]]
    body: List[Stmt]

@dataclass
class Program(ASTNode):
    functions: List[FuncDef]