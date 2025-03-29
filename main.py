import os
import mel_parser


def main():
    # prog = mel_parser.parse('''
    # class MyClass {
    #     int a;
    #     void method() { }
    #     MyClass constructor(int v) {
    #         this.a = v;
    #     }
    #
    #     void test() {
    #         for (int i = 0; i < 10; i=i+1) {
    #             if (i % 2 == 0) {
    #                 a = i;
    #             } else {
    #                 a = i * 2;
    #             }
    #         }
    #
    #         while (a < 50) {
    #             a = a + 5;
    #         }
    #
    #         int[] arr = new int[10];
    #         int[] arr2 = {1, 2, 3};
    #
    #
    #     }
    # }
    # ''')

    #int[] arr = new int[10];  // NewArrayNode
    #int[] arr2 = {1, 2, 3};   // ArrayNode

    # prog = mel_parser.parse('''
    #     int[] arr = new int[10];
    #     ''')

    prog = mel_parser.parse('''
    class MyClass {
        int a = 5;
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
            
            int[] arr = new int[10];
            arr = {1, 2, 3, 4, 5};
            int[] arr2 = {1, 2, 3};
            int[] arr3 = {1, 2, 3};
            x = arr[10];
            arr[0] = 1;
            A g = new A(3);
        }
    }
    ''')

    print(*prog.tree, sep=os.linesep)


if __name__ == "__main__":
    main()