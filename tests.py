import pytest
import mel_parser
from scope import Scope
from semantics import SemanticAnalyzer


@pytest.mark.parametrize("code, expected_errors", [
    ('''
    int x = 5;
    {
        int x = "hello";
    }
    ''', ["Присвоение string в переменную типа int внутри блока"]),

    ('''
    {
        int x = 5;
    }
    x = 10;
    ''', ["Переменная x не объявлена в глобальной области видимости"]),

    ('''
    int x = 10;
    {
        x = 20;
    }
    ''', []),

    ('''
    int sum(int a, int b) {
        return a + b;
    }
    int result = sum(3, "4");
    ''', ["Передан аргумент string вместо int в функцию sum"]),

    ('''
    class A {
        int x;
    }
    A a;
    a.x = "hello";
    ''', ["Присвоение string в поле типа int внутри класса"]),

    ('''
    int[] arr = {1, 2, 3};
    arr[0] = "hello";
    ''', ["Присвоение string в элемент массива типа int"]),
])
def test_scope_and_types(code, expected_errors):
    analyzer = SemanticAnalyzer()
    prog = mel_parser.parse(code)

    analyzer.analyze(prog)

    actual_errors = [str(err) for err in analyzer.errors]
    assert actual_errors == expected_errors, f"\nОжидалось: {expected_errors}\nПолучено: {actual_errors}"
