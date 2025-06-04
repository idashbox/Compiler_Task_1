package CompilerDemo;

import java.util.Scanner;

public class Runtime {
    private static Scanner scanner = new Scanner(System.in);

    public static void println(int value) {
        System.out.println(value);
    }

    public static void println(String value) {
        System.out.println(value);
    }

    public static void println(double value) {
        System.out.println(value);
    }

    public static void println(boolean value) {
        System.out.println(value);
    }

    public static int input() {
        System.out.print("Введите: ");
        return scanner.nextInt();
    }

    public static String concat(String s1, String s2) {
        return s1 + s2;
    }
}