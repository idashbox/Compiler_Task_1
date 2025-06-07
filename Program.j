.class public Program
.super java/lang/Object
.method public <init>()V
aload_0
invokespecial java/lang/Object/<init>()V
return
.end method
.method public static main([Ljava/lang/String;)V
.limit stack 100
.limit locals 100
bipush 10
istore_0
bipush 20
istore_1
iload_0
iload_1
iadd
istore_2
getstatic java/lang/System/out Ljava/io/PrintStream;
iload_2
invokevirtual java/io/PrintStream/println(I)V
bipush 15
istore_3
iconst_5
istore 4
iload_3
iload 4
iadd
istore 5
iload_3
iload 4
isub
istore 6
iload_3
iload 4
imul
istore 7
iload_3
iload 4
idiv
istore 8
getstatic java/lang/System/out Ljava/io/PrintStream;
iload 5
invokevirtual java/io/PrintStream/println(I)V
getstatic java/lang/System/out Ljava/io/PrintStream;
iload 6
invokevirtual java/io/PrintStream/println(I)V
getstatic java/lang/System/out Ljava/io/PrintStream;
iload 7
invokevirtual java/io/PrintStream/println(I)V
getstatic java/lang/System/out Ljava/io/PrintStream;
iload 8
invokevirtual java/io/PrintStream/println(I)V
new Fibonacci
dup
invokespecial Fibonacci/<init>()V
astore 9
getstatic java/lang/System/out Ljava/io/PrintStream;
aload 9
getfield Fibonacci/a I
invokevirtual java/io/PrintStream/println(I)V
aload 9
invokevirtual Fibonacci/next()I
pop
getstatic java/lang/System/out Ljava/io/PrintStream;
aload 9
getfield Fibonacci/a I
invokevirtual java/io/PrintStream/println(I)V
aload 9
invokevirtual Fibonacci/next()I
pop
getstatic java/lang/System/out Ljava/io/PrintStream;
aload 9
getfield Fibonacci/a I
invokevirtual java/io/PrintStream/println(I)V
aload 9
invokevirtual Fibonacci/next()I
pop
getstatic java/lang/System/out Ljava/io/PrintStream;
aload 9
getfield Fibonacci/a I
invokevirtual java/io/PrintStream/println(I)V
aload 9
invokevirtual Fibonacci/next()I
pop
getstatic java/lang/System/out Ljava/io/PrintStream;
aload 9
getfield Fibonacci/a I
invokevirtual java/io/PrintStream/println(I)V
aload 9
invokevirtual Fibonacci/next()I
pop
getstatic java/lang/System/out Ljava/io/PrintStream;
aload 9
getfield Fibonacci/a I
invokevirtual java/io/PrintStream/println(I)V
aload 9
invokevirtual Fibonacci/next()I
pop
getstatic java/lang/System/out Ljava/io/PrintStream;
aload 9
getfield Fibonacci/a I
invokevirtual java/io/PrintStream/println(I)V
aload 9
invokevirtual Fibonacci/next()I
pop
getstatic java/lang/System/out Ljava/io/PrintStream;
aload 9
getfield Fibonacci/a I
invokevirtual java/io/PrintStream/println(I)V
aload 9
invokevirtual Fibonacci/next()I
pop
getstatic java/lang/System/out Ljava/io/PrintStream;
aload 9
getfield Fibonacci/a I
invokevirtual java/io/PrintStream/println(I)V
return
.end method