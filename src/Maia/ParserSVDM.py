from parsy import string, regex, generate, forward_declaration, seq
from functools import reduce
from arvoreSVDMlang import *

# Ignorar espaços em branco e comentários de linha dupla (//)
whitespace = regex(r"(\s|//.*)+")

def lexeme(p):
    return p << whitespace.optional()

# Símbolos básicos
lparen = lexeme(string("("))
rparen = lexeme(string(")"))
lbrace = lexeme(string("{"))
rbrace = lexeme(string("}"))
lbracket = lexeme(string("["))
rbracket = lexeme(string("]"))
semi = lexeme(string(";"))
comma = lexeme(string(","))
assign_op = lexeme(string("="))

# Tipos e Identificadores
identifier = lexeme(regex(r"[a-zA-Z_][a-zA-Z0-9_]*"))
int_lit = lexeme(regex(r"[0-9]+")).map(lambda s: IntVal(int(s)))
string_lit = lexeme(regex(r'"[^"]*"')).map(lambda s: StringVal(s[1:-1]))
type_name = lexeme(string("int") | string("void"))

# Declarações recursivas
pExp = forward_declaration()
pStmt = forward_declaration()

# --- EXPRESSÕES ---
@generate
def pFactor():
    # Uma chamada de função, acesso a array, variável, literal ou expressão entre parênteses
    yield whitespace.optional()
    
    # Chamada de função: nome(arg1, arg2)
    func_call = seq(
        identifier,
        lparen >> pExp.sep_by(comma) << rparen
    ).combine(lambda name, args: FuncCall(name, args))
    
    # Acesso a array: nome[index]
    array_access = seq(
        identifier,
        lbracket >> pExp << rbracket
    ).combine(lambda name, index: ArrayAccess(name, index))
    
    # Variável simples
    var = identifier.map(Var)
    
    # Expressão entre parênteses
    parens = lparen >> pExp << rparen
    
    # Tenta resolver pela ordem correta
    return (yield func_call | array_access | var | int_lit | string_lit | parens)

# Função auxiliar para criar operadores binários associativos à esquerda
def left_assoc(parser, op_parser):
    @generate
    def inner():
        first = yield parser
        rest = yield seq(op_parser, parser).many()
        return reduce(lambda acc, pair: BinOp(pair[0], acc, pair[1]), rest, first)
    return inner

# Hierarquia de precedência de operadores
pTerm = left_assoc(pFactor, lexeme(string("*") | string("/") | string("%")))
pArith = left_assoc(pTerm, lexeme(string("+") | string("-")))
pRel = left_assoc(pArith, lexeme(string("<=") | string(">=") | string("<") | string(">")))
pEq = left_assoc(pRel, lexeme(string("==") | string("!=")))
pAnd = left_assoc(pEq, lexeme(string("&&")))
pExp.become(left_assoc(pAnd, lexeme(string("||"))))

# --- INSTRUÇÕES ---
@generate
def pVarDecl():
    v_type = yield type_name
    name = yield identifier
    
    is_array = False
    array_size = None
    array_elements = None
    expr = None
    
    # Verifica se é um array
    has_bracket = yield lbracket.optional()
    if has_bracket:
        is_array = True
        array_size = yield int_lit.optional()
        yield rbracket
    
    # Verifica se tem atribuição
    has_assign = yield assign_op.optional()
    if has_assign:
        if is_array:
            yield lbrace
            array_elements = yield pExp.sep_by(comma)
            yield rbrace
        else:
            expr = yield pExp
            
    yield semi
    return VarDecl(v_type, name, is_array, array_size, expr, array_elements)

@generate
def pAssign():
    target = yield (
        seq(identifier, lbracket >> pExp << rbracket).combine(lambda n, i: ArrayAccess(n, i)) |
        identifier.map(Var)
    )
    yield assign_op
    expr = yield pExp
    yield semi
    return Assign(target, expr)

@generate
def pIf():
    yield lexeme(string("if"))
    yield lparen
    cond = yield pExp
    yield rparen
    yield lbrace
    true_body = yield pStmt.many()
    yield rbrace
    
    has_else = yield lexeme(string("else")).optional()
    false_body = []
    if has_else:
        yield lbrace
        false_body = yield pStmt.many()
        yield rbrace
        
    return If(cond, true_body, false_body)

@generate
def pWhile():
    yield lexeme(string("while"))
    yield lparen
    cond = yield pExp
    yield rparen
    yield lbrace
    body = yield pStmt.many()
    yield rbrace
    return While(cond, body)

@generate
def pFor():
    yield lexeme(string("for"))
    yield lparen
    init = yield (pVarDecl | pAssign)
    cond = yield pExp
    yield semi
    
    # O update no for não tem ponto e vírgula no final
    update_target = yield identifier.map(Var)
    yield assign_op
    update_expr = yield pExp
    update = Assign(update_target, update_expr)
    
    yield rparen
    yield lbrace
    body = yield pStmt.many()
    yield rbrace
    return For(init, cond, update, body)

@generate
def pReturn():
    yield lexeme(string("return"))
    expr = yield pExp.optional()
    yield semi
    return Return(expr)

pBreak = lexeme(string("break")) >> semi.result(Break())
pContinue = lexeme(string("continue")) >> semi.result(Continue())

@generate
def pExprStmt():
    expr = yield pExp
    yield semi
    return ExprStmt(expr)

# O parser de statements tenta todas as possibilidades
pStmt.become(pVarDecl | pIf | pWhile | pFor | pReturn | pBreak | pContinue | pAssign | pExprStmt)

# --- PROGRAMA / FUNÇÕES ---
@generate
def pParam():
    p_type = yield type_name
    p_name = yield identifier
    return (p_type, p_name)

@generate
def pFuncDef():
    ret_type = yield type_name
    name = yield identifier
    yield lparen
    params = yield pParam.sep_by(comma)
    yield rparen
    yield lbrace
    body = yield pStmt.many()
    yield rbrace
    return FuncDef(ret_type, name, params, body)

@generate
def pProgram():
    yield whitespace.optional()
    funcs = yield pFuncDef.many()
    return Program(funcs)