import os
import mel_parser
from interpreter import Interpreter
from semantics import SemanticAnalyzer


def main():
    prog = mel_parser.parse('''class A {
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

    # prog = mel_parser.parse('''
    # # int a = 5;
    # # int b = 3;
    # # int c = a + b * 2;
    # # bool result = c > 10 || b < 2;
    # # ''')

    # prog = mel_parser.parse('''
    #     class Point {
    #         int x = 0;
    #         int y = 0;
    #     }
    #     var Point p;
    #     p.x = 5;
    # ''')

    # prog = mel_parser.parse('''
    #     int sum(int a, int b) {
    #         return a + b;
    #     }
    #     int r = sum(3, 4);
    # ''')

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
