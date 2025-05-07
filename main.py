import os
import mel_parser
from mel_parser import parse
from interpreter import Interpreter
from semantics import SemanticAnalyzer
from mel_types import equals_simple


def main():
    test_nodes = [
        ('int x = 5;', 'int y = 10;', True),  # оба int
        ('int a = 5;', 'float b = 3.14;', False),  # int vs float
        ('int[] arr1 = {1, 2};', 'int[] arr2 = {3, 4};', True),  # оба массивы
        ('string s = "hello";', 'bool flag = true;', False)  # string vs bool
    ]

    print("\nПроверка равенства типов:")
    for code1, code2, expected in test_nodes:
        node1 = parse(code1).children[0]
        node2 = parse(code2).children[0]
        result = equals_simple(node1, node2)
        print(f"{code1} == {code2}: {result} (ожидается {expected})")

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

    prog = mel_parser.parse('''
        class Point {
            int x = 0;
            int y = 0;
        }
        Point p;
        p.x = "5";
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
