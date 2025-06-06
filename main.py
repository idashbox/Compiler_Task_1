#!/usr/bin/env python3
import os
import sys
import argparse
from mel_parser import parse
from semantics import SemanticAnalyzer
from codegen.jbc import JBCGenerator

def main():
    parser = argparse.ArgumentParser(description='Mel compiler.')
    parser.add_argument('source', help='Source file')
    parser.add_argument('--target', choices=['jvm'], default='jvm', help='Target platform')
    args = parser.parse_args()

    if not os.path.isfile(args.source):
        print(f"File {args.source} not found", file=sys.stderr)
        sys.exit(1)

    with open(args.source, 'r', encoding='utf-8') as f:
        source = f.read()

    try:
        ast = parse(source)
        print(f"DEBUG: Parsed AST: {ast}")
        analyzer = SemanticAnalyzer()
        analyzer.analyze(ast)
        if analyzer.errors:
            print("Найдены ошибки семантики:")
            for err in analyzer.errors:
                print("-", err)
            sys.exit(1)
        print(f"Семантический анализ: успешно")

        if args.target == 'jvm':
            print(f"Генерация кода: visit_StmtListNode для {ast}")
            generator = JBCGenerator()
            generator(ast)
            # with open('mel.j', 'w', encoding='utf-8') as f:
            #     f.write('\n'.join(generator.code))
            print(f"StmtListNode: {len(ast.stmts)} переменных, адресов {id(ast)}, stmts: {ast.stmts}")
    except Exception as e:
        print(f"Compilation error: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == '__main__':
    main()
