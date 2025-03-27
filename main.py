import os
import mel_parser


def main():
    prog = mel_parser.parse('''
    class MyClass {
        int a;
        void method() { }
        MyClass constructor(int v) {
            this.a = v;
        }
    }
    ''')

    print(*prog.tree, sep=os.linesep)


if __name__ == "__main__":
    main()