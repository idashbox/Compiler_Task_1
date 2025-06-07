.class public Fibonacci
.super java/lang/Object

.field public a I
.field public b I

.method public <init>()V
.limit stack 10
.limit locals 1
aload_0
invokespecial java/lang/Object/<init>()V
aload_0
iconst_0
putfield Fibonacci/a I
aload_0
iconst_1
putfield Fibonacci/b I
return
.end method

.method public next()I
.limit stack 10
.limit locals 10
aload_0
getfield Fibonacci/b I
istore_1
aload_0
aload_0
getfield Fibonacci/a I
aload_0
getfield Fibonacci/b I
iadd
putfield Fibonacci/b I
aload_0
iload_1
putfield Fibonacci/a I
aload_0
getfield Fibonacci/a I
ireturn
.end method