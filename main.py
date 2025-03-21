import os
import mel_parser


def main():
    prog = mel_parser.parse('''class A {
        int x = 5;
        float y = 3.14;
        int[] arr = {1, 2, 3};
    }''')

    print(*prog.tree, sep=os.linesep)


if __name__ == "__main__":
    main()