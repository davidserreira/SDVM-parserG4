# main.py
import sys
from ParserSVDM import pProgram

def print_ast(node, indent=0):
    """
    Função auxiliar simples para imprimir a AST formatada
    em vez de uma única linha gigante.
    """
    spacing = "  " * indent
    if isinstance(node, list):
        for item in node:
            print_ast(item, indent)
    elif hasattr(node, "__dataclass_fields__"):
        print(f"{spacing}{node.__class__.__name__}:")
        for field in node.__dataclass_fields__:
            value = getattr(node, field)
            print(f"{spacing}  {field}=")
            print_ast(value, indent + 2)
    else:
        print(f"{spacing}{node}")

def main():
    if len(sys.argv) < 2:
        print("Uso: python main.py <ficheiro_codigo>")
        print("Exemplo: python main.py control_flow")
        return

    file_path = sys.argv[1]
    
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            code = file.read()
    except FileNotFoundError:
        print(f"Erro: O ficheiro '{file_path}' não foi encontrado.")
        return

    try:
        # Pede ao parsy para ler e construir a árvore
        ast = pProgram.parse(code)
        
        print(f"--- AST gerada com sucesso para {file_path} ---")
        print_ast(ast)
        
    except Exception as e:
        print(f"Erro de Sintaxe no ficheiro: \n{e}")

if __name__ == "__main__":
    main()