import argparse
import os
import sys

import mel_parser
from scope import Scope


import traceback
from mel_parser import parse  # Явный импорт parse из mel_parser
from semantics import SemanticAnalyzer
from jbc import JbcCodeGenerator
from interpreter import Interpreter



def test_scope_and_types():
    test_cases = [
        (
            '''
            int x = 5;
            bool true;
            if (true){
                x = "hello";
            }
            ''',
            "Type mismatch: cannot assign string to int"
        ),
        (
            '''
            if (true){
                int x = 5;
            }
            x = 10;
            ''',
            "Ошибка: переменная x не объявлена в глобальной области видимости"
        ),
        (
            '''
            int x = 10;
            if (true){
                x = 20;
            }
            ''',
            "Нет ошибок — корректное использование переменной из внешнего scope"
        ),
        (
            '''
            int sum(int a, int b) {
                return a + b;
            }
            int result = sum(3, "4");
            ''',
            "Ошибка: передан аргумент string вместо int"
        ),
        (
            '''
            class A {
                int x;
            }
            A a;
            a.x = "hello";
            ''',
            "Ошибка: присвоение string в поле типа int внутри класса"
        ),
        (
            '''
            int[] arr = {1, 2, 3};
            arr[0] = "hello";
            ''',
            "Ошибка: присвоение string в элемент массива типа int"
        )
    ]
    print("\n=== Тест: Проверка Scope и Типов ===")

    for i, (code, desc) in enumerate(test_cases, 1):
        print(f"\nТест {i}: {desc}")
        try:
            prog = mel_parser.parse(code)
            analyzer = SemanticAnalyzer()
            analyzer.analyze(prog)
            if analyzer.errors:
                print("Найдены ошибки:")
                for err in analyzer.errors:
                    print("-", err)
            else:
                print("Ошибок не найдено")
        except Exception as e:
            print(f"Ошибка при анализе: {e}")


# def main():
#     test_scope_and_types()
#
#     prog1 = mel_parser.parse('''
#     class A {
#         int x = 5;
#         float y = 3.14;
#         int[] arr = {1, 2, 3};
#         arr[1] = 42;
#         x = arr[2];
#         string s = "Hello";
#         int z;
#         z = 5;
#         z = 5 * 7;
#     }''')
#
#     prog1 = mel_parser.parse('''
#     int a = 5;
#     int b = 3;
#     int c = a + b * 2;
#     bool result = c > 10 || b < 2;
#     ''')
#
#     # prog = mel_parser.parse('''
#     #     class Point {
#     #         int x = 0;
#     #         int y = 0;
#     #     }
#     #     Point p;
#     #     p.x = 5;
#     # ''')
#
#     prog = mel_parser.parse('''
#             class Point {
#                 int x = 0;
#                 int y = 0;
#             }
#             Point p2 = new Point();
#             Point p1 = new Point();
#             p1.x = 5;
#             p2.x = 10;
#     ''')
#
#     prog1 = mel_parser.parse('''
#         int sum(int a, int b) {
#             return a + b;
#         }
#         int r = sum(3, 4);
#     ''')
#
#     prog = mel_parser.parse('''
#             int r = 3 + 5;
#     ''')
#
#     analyzer = SemanticAnalyzer()
#
#     analyzer.analyze(prog)
#
#     if analyzer.errors:
#         print("Найдены ошибки семантики:")
#         for err in analyzer.errors:
#             print("-", err)
#     else:
#         print("Семантический анализ прошёл успешно")
#
#     print(*prog.tree, sep=os.linesep)
#
#     interpreter = Interpreter()
#     result = interpreter.eval(prog)
#
#     print("Глобальные переменные после выполнения:")
#     print(interpreter.variables)

def execute(prog: str, jbc_only: bool = False, file_name: str = None, output_file: str = None):
    try:
        prog_ast = parse(prog)
    except Exception as e:
        print(f'Ошибка парсинга: {e}', file=sys.stderr)
        traceback.print_exc(file=sys.stderr)
        sys.exit(1)

    if not jbc_only:
        print('AST saved to ast_output.txt')

    analyzer = SemanticAnalyzer()
    errors = analyzer.analyze(prog_ast)
    if errors:
        print('Ошибки семантики:')
        for err in errors:
            print(f'- {err}')
        sys.exit(2)
    elif not jbc_only:
        print('Семантический анализ успешен')

    if jbc_only:
        try:
            gen = JbcCodeGenerator(file_name)
            gen.current_scope = analyzer.current_scope  # Передаём область видимости
            gen.gen_program(prog_ast)
            # Сохраняем .jbc в указанный выходной файл
            output_path = output_file if output_file else file_name.replace('.mel', '.jbc')
            with open(output_path, 'w', encoding='utf-8') as f:
                for line in gen.code:
                    f.write(line + '\n')
        except Exception as e:
            print(f'Ошибка генерации JBC: {e}', file=sys.stderr)
            sys.exit(4)
    else:
        interpreter = Interpreter()
        interpreter.eval(prog_ast)
        print("Глобальные переменные после выполнения:")
        print(interpreter.variables)

def main():
    parser = argparse.ArgumentParser(description='Compiler demo program')
    parser.add_argument('src', type=str, help='source code file')
    parser.add_argument('output', type=str, nargs='?', default=None, help='output jbc file (optional)')
    parser.add_argument('--jbc-only', action='store_true', help='print only Java bytecode')
    args = parser.parse_args()

    with open(args.src, mode='r', encoding="utf-8") as f:
        src = f.read()

    execute(src, args.jbc_only, args.src, args.output)

if __name__ == "__main__":
    main()

