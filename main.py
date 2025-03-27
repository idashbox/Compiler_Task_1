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

        void test() {
            for (int i = 0; i < 10; i=i+1) {
                if (i % 2 == 0) {
                    a = i;
                } else {
                    a = i * 2;
                }
            }

            while (a < 50) {
                a = a + 5;
            }
        }
    }
    ''')

    print(*prog.tree, sep=os.linesep)


if __name__ == "__main__":
    main()