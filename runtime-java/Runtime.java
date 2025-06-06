package melcompiler;

import java.util.Scanner;

public class Runtime {
    private static final Scanner scanner = new Scanner(System.in);

    public static String read() {
        return scanner.nextLine();
    }

    public static void print(String value) {
        System.out.print(value);
    }

    public static void println(String value) {
        System.out.println(value);
    }

    public static int toInt(String value) {
        return Integer.parseInt(value);
    }

    public static float toFloat(String value) {
        return Float.parseFloat(value);
    }

    public static String toString(int value) {
        return Integer.toString(value);
    }

    public static String toString(float value) {
        return Float.toString(value);
    }

    public static String toString(boolean value) {
        return Boolean.toString(value);
    }

    public static String concat(String a, String b) {
        return a + b;
    }

    public static int compare(String a, String b) {
        return a.compareTo(b);
    }
} 