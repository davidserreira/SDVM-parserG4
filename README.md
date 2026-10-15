# SDVM-parserG4

Parser para a linguagem **SDVM**, desenvolvido no âmbito da UC de Manutenção e Evolução de Software.

A especificação da linguagem (gramática e exemplos) **não é nossa**: vem do repositório da turma
[sooraia/SDVM-lang](https://github.com/sooraia/SDVM-lang), incluído aqui como submódulo em `spec/`.

## Estrutura

```
SDVM-parserG4/
├── spec/                 ← submódulo: gramática da turma (NÃO editar)
│   ├── README.md         (gramática BNF)
│   └── examples/         (programas de exemplo, usados como testes)
├── extensions/
│   ├── GRAMMAR-EXT.md    ← extensões do grupo à gramática
│   └── examples/         ← programas que usam as extensões
├── src/                  ← código do parser
└── tests/                ← testes
```

## Setup (primeira vez)

```bash
git clone --recurse-submodules https://github.com/davidserreira/SDVM-parserG4.git
```

Se já clonaram sem `--recurse-submodules` e a pasta `spec/` está vazia:

```bash
git submodule update --init
```

## Regras do grupo

1. **Nunca editar nada dentro de `spec/`.** É o repositório da turma; alterações à gramática vão para
   `extensions/GRAMMAR-EXT.md`.
2. **Trabalhar em branches** (`expressoes`, `statements`, ...) e juntar ao `main` por Pull Request,
   para que os outros revejam.
3. **Commits separados** para alterações à gramática (`extensions/`) e ao parser (`src/`).
4. **Atualizar a spec é uma decisão do grupo**, não automática (ver abaixo).

## Atualizar a versão da gramática

O submódulo está fixado num commit específico da spec. Para adotar a versão mais recente:

```bash
git submodule update --remote spec
git diff spec                      # ver que commit mudou
git -C spec log --oneline -5       # ver o que mudou na spec
git commit -am "spec: atualiza para <commit>"
git push
```

Os outros elementos, depois de `git pull`, correm:

```bash
git submodule update
```

## Propor alterações à gramática da turma

Este repositório é privado e não é um fork, por isso não dá para abrir PR diretamente.
Abrir uma *issue* em [sooraia/SDVM-lang](https://github.com/sooraia/SDVM-lang/issues) com a proposta,
ou fazer um fork público **apenas com a alteração à gramática** (nunca código do parser).
