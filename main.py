import os
import mel_parser
from interpreter import Interpreter
from scope import Scope
from semantics import SemanticAnalyzer


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


def main():
    test_scope_and_types()

    prog1 = mel_parser.parse('''
    class A {
        int x = 5;
        float y = 3.14;
        int[] arr = {1, 2, 3};
        arr[1] = 42;
        x = arr[2];
        string s = "Hello";
        int z;
        z = 5;
        z = 5 * 7;
    }''')

    prog1 = mel_parser.parse('''
    int a = 5;
    int b = 3;
    int c = a + b * 2;
    bool result = c > 10 || b < 2;
    ''')

    # prog = mel_parser.parse('''
    #     class Point {
    #         int x = 0;
    #         int y = 0;
    #     }
    #     Point p;
    #     p.x = 5;
    # ''')

    prog = mel_parser.parse('''
            class Point {
                int x = 0;
                int y = 0;
            }
            Point p1;
            Point p2;
            p1.x = 5;
            p2.x = 10;
    ''')

    prog1 = mel_parser.parse('''
        int sum(int a, int b) {
            return a + b;
        }
        int r = sum(3, 4);
    ''')

    analyzer = SemanticAnalyzer()

    analyzer.analyze(prog)

    if analyzer.errors:
        print("Найдены ошибки семантики:")
        for err in analyzer.errors:
            print("-", err)
    else:
        print("Семантический анализ прошёл успешно")

    print(*prog.tree, sep=os.linesep)

    interpreter = Interpreter()
    result = interpreter.eval(prog)

    print("Глобальные переменные после выполнения:")
    print(interpreter.variables)


if __name__ == "__main__":
    main()
