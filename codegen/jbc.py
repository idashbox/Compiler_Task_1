from typing import Dict, Any, Optional
from .base import CodeGenBase
from mel_ast import *

class JBCGenerator(CodeGenBase):
    def __init__(self):
        super().__init__()
        self.stack_size = 0
        self.max_stack = 0
        self.label_counter = 0
        self.current_class = None
        self.current_method = None
        self.encoding = 'utf-8'
        
    def get_label(self) -> str:
        """Генерирует уникальную метку"""
        self.label_counter += 1
        return f"L{self.label_counter}"
        
    def visit_literal(self, node: LiteralNode) -> None:
        if isinstance(node.value, int):
            if -1 <= node.value <= 5:
                self.emit(f"iconst_{node.value}")
            elif -128 <= node.value <= 127:
                self.emit(f"bipush {node.value}")
            elif -32768 <= node.value <= 32767:
                self.emit(f"sipush {node.value}")
            else:
                self.emit(f"ldc {node.value}")
        elif isinstance(node.value, str):
            self.emit(f'ldc "{node.value}"')
        elif isinstance(node.value, bool):
            self.emit("iconst_1" if node.value else "iconst_0")
            
    def visit_ident(self, node: IdentNode) -> None:
        if node.name in self.locals:
            index = self.locals[node.name]
            if index <= 3:
                self.emit(f"iload_{index}")
            else:
                self.emit(f"iload {index}")
        else:
            self.emit(f"getstatic {self.current_class}/{node.name} I")
            
    def visit_bin_op(self, node: BinOpNode) -> None:
        # Загружаем первый операнд
        if isinstance(node.arg1, LiteralNode):
            self.visit_literal(node.arg1)
        elif isinstance(node.arg1, IdentNode):
            index = self.locals[node.arg1.name]
            if index <= 3:
                self.emit(f"iload_{index}")
            else:
                self.emit(f"iload {index}")
        else:
            self.visit(node.arg1)
            
        # Загружаем второй операнд
        if isinstance(node.arg2, LiteralNode):
            self.visit_literal(node.arg2)
        elif isinstance(node.arg2, IdentNode):
            index = self.locals[node.arg2.name]
            if index <= 3:
                self.emit(f"iload_{index}")
            else:
                self.emit(f"iload {index}")
        else:
            self.visit(node.arg2)
        
        # Выполняем операцию
        op_map = {
            BinOp.ADD: "iadd",
            BinOp.SUB: "isub",
            BinOp.MUL: "imul",
            BinOp.DIV: "idiv",
            BinOp.MOD: "irem",
            BinOp.GT: "if_icmpgt",
            BinOp.GE: "if_icmpge",
            BinOp.LT: "if_icmplt",
            BinOp.LE: "if_icmple",
            BinOp.EQ: "if_icmpeq",
            BinOp.NE: "if_icmpne",
            BinOp.AND: "iand",
            BinOp.OR: "ior"
        }
        
        self.emit(op_map[node.op])
        
    def visit_unary_op(self, node: UnaryOpNode) -> None:
        node.arg.visit(self)
        if node.op == UnaryOp.NEG:
            self.emit("ineg")
        elif node.op == UnaryOp.NOT:
            self.emit("iconst_1")
            self.emit("ixor")
            
    def visit_assign(self, node: AssignNode) -> None:
        node.val.visit(self)
        if isinstance(node.var, IdentNode):
            if node.var.name in self.locals:
                index = self.locals[node.var.name]
                if index <= 3:
                    self.emit(f"istore_{index}")
                else:
                    self.emit(f"istore {index}")
            else:
                self.emit(f"putstatic {self.current_class}/{node.var.name} I")
                
    def visit_if(self, node: IfNode) -> None:
        else_label = self.get_label()
        end_label = self.get_label()
        
        node.cond.visit(self)
        self.emit(f"ifeq {else_label}")
        
        node.then_stmt.visit(self)
        self.emit(f"goto {end_label}")
        
        self.emit(f"{else_label}:")
        if node.else_stmt:
            node.else_stmt.visit(self)
            
        self.emit(f"{end_label}:")
        
    def visit_while(self, node: WhileNode) -> None:
        start_label = self.get_label()
        end_label = self.get_label()
        
        self.emit(f"{start_label}:")
        node.cond.visit(self)
        self.emit(f"ifeq {end_label}")
        
        node.body.visit(self)
        self.emit(f"goto {start_label}")
        self.emit(f"{end_label}:")
        
    def visit_for(self, node: ForNode) -> None:
        start_label = self.get_label()
        end_label = self.get_label()
        
        node.init.visit(self)
        self.emit(f"{start_label}:")
        
        node.cond.visit(self)
        self.emit(f"ifeq {end_label}")
        
        node.body.visit(self)
        node.step.visit(self)
        self.emit(f"goto {start_label}")
        self.emit(f"{end_label}:")
        
    def visit_stmt_list(self, node: StmtListNode) -> None:
        if isinstance(node.stmts, tuple) and len(node.stmts) == 1:
            stmts = node.stmts[0]
        else:
            stmts = node.stmts
            
        for stmt in stmts:
            if isinstance(stmt, list):
                for s in stmt:
                    self.visit(s)
            else:
                self.visit(stmt)
            
    def visit_func_call(self, node: FuncCallNode) -> None:
        if node.func.name == 'println':
            # Получаем System.out
            self.emit("getstatic java/lang/System/out Ljava/io/PrintStream;")
            
            # Загружаем параметры
            for param in node.params:
                if isinstance(param, LiteralNode):
                    self.visit_literal(param)
                elif isinstance(param, IdentNode):
                    self.visit_ident(param)
                elif isinstance(param, BinOpNode):
                    self.visit_bin_op(param)
                else:
                    self.visit(param)
                    
            # Вызываем println
            self.emit("invokevirtual java/io/PrintStream/println(I)V")
        else:
            # Загружаем параметры
            for param in node.params:
                param.visit(self)
            # Вызываем функцию
            self.emit(f"invokestatic {self.current_class}/{node.func.name}")
        
    def visit_func_decl(self, node: FuncDeclNode) -> None:
        self.current_method = node.name.name
        signature = self._get_method_signature(node)
        self.emit(f".method public static {node.name.name}{signature}")
        self.emit(".limit stack 100")  # Примерное значение
        self.emit(".limit locals 100")  # Примерное значение
        
        # Local variables
        self.locals = {}
        local_index = 0
        if node.params:
            for param in node.params.vars:
                self.locals[param.name] = local_index
                local_index += 1
                
        node.body.visit(self)
        
        # Добавляем return, если его нет
        if not isinstance(node.body.children[-1], ReturnNode):
            self.emit("return")
            
        self.emit(".end method")
        self.current_method = None
        
    def visit_class_decl(self, node: ClassDeclNode) -> None:
        self.current_class = node.name.name
        self.emit(f".class public {node.name.name}")
        self.emit(".super java/lang/Object")
        
        # Constructor
        self.emit(".method public <init>()V")
        self.emit("aload_0")
        self.emit("invokespecial java/lang/Object/<init>()V")
        self.emit("return")
        self.emit(".end method")
        
        if node.body:
            node.body.visit(self)
            
        self.current_class = None
        
    def visit_member_access(self, node: MemberAccessNode) -> None:
        node.obj.visit(self)
        self.emit(f"getfield {node.obj.name}/{node.member.name} I")
        
    def visit_array(self, node: ArrayNode) -> None:
        self.emit(f"bipush {len(node.elements)}")
        self.emit("newarray int")
        
        for i, element in enumerate(node.elements):
            self.emit("dup")
            self.emit(f"bipush {i}")
            element.visit(self)
            self.emit("iastore")
            
    def visit_array_index(self, node: ArrayIndexNode) -> None:
        node.array.visit(self)
        node.index.visit(self)
        self.emit("iaload")
        
    def visit_array_assign(self, node: ArrayAssignNode) -> None:
        node.array.visit(self)
        node.index.visit(self)
        node.value.visit(self)
        self.emit("iastore")
        
    def visit_new_instance(self, node: NewInstanceNode) -> None:
        self.emit(f"new {node.class_name.name}")
        self.emit("dup")
        self.emit(f"invokespecial {node.class_name.name}/<init>()V")
        
    def visit_return(self, node: ReturnNode) -> None:
        if node.result:
            node.result.visit(self)
            self.emit("ireturn")
        else:
            self.emit("return")
            
    def _get_method_signature(self, node: FuncDeclNode) -> str:
        """Генерирует сигнатуру метода в формате JVM"""
        params = ""
        if node.params:
            for param in node.params.vars:
                params += "I"  # Пока поддерживаем только int
        return f"({params})I"  # Возвращаем int 

    def emit(self, instruction: str) -> None:
        self.code.append(instruction)
        
    def __call__(self, node: AstNode) -> None:
        self.code = []
        self.locals = {}
        self.current_class = "Program"
        
        # Генерируем заголовок класса
        self.emit(".class public Program")
        self.emit(".super java/lang/Object")
        
        # Конструктор
        self.emit(".method public <init>()V")
        self.emit("aload_0")
        self.emit("invokespecial java/lang/Object/<init>()V")
        self.emit("return")
        self.emit(".end method")
        
        # Метод main
        self.emit(".method public static main([Ljava/lang/String;)V")
        self.emit(".limit stack 100")
        self.emit(".limit locals 100")
        
        # Генерируем код для узла AST
        if isinstance(node, StmtListNode):
            for stmt in node.stmts[0]:
                self.visit(stmt)
        else:
            self.visit(node)
        
        # Завершаем метод main
        self.emit("return")
        self.emit(".end method")

    def visit(self, node: AstNode) -> None:
        if isinstance(node, LiteralNode):
            self.visit_literal(node)
        elif isinstance(node, IdentNode):
            self.visit_ident(node)
        elif isinstance(node, BinOpNode):
            self.visit_bin_op(node)
        elif isinstance(node, AssignNode):
            self.visit_assign(node)
        elif isinstance(node, VarsDeclNode):
            self.visit_VarsDeclNode(node)
        elif isinstance(node, FuncCallNode):
            self.visit_func_call(node)
        elif isinstance(node, StmtListNode):
            self.visit_stmt_list(node)
        elif isinstance(node, TypedDeclNode):
            self.visit_TypedDeclNode(node)
        else:
            print(f"Warning: No visit method for {node.__class__.__name__}")
            
    def visit_VarsDeclNode(self, node: VarsDeclNode) -> None:
        for var in node.vars:
            if isinstance(var, list):
                for v in var:
                    if isinstance(v, AssignNode):
                        # Загружаем значение
                        if isinstance(v.val, LiteralNode):
                            self.visit_literal(v.val)
                        elif isinstance(v.val, BinOpNode):
                            self.visit_bin_op(v.val)
                        else:
                            self.visit(v.val)
                        # Сохраняем в локальную переменную
                        self.locals[v.var.name] = len(self.locals)
                        index = self.locals[v.var.name]
                        if index <= 3:
                            self.emit(f"istore_{index}")
                        else:
                            self.emit(f"istore {index}")
                    elif isinstance(v, IdentNode):
                        self.locals[v.name] = len(self.locals)
                        index = self.locals[v.name]
                        self.emit("iconst_0")
                        if index <= 3:
                            self.emit(f"istore_{index}")
                        else:
                            self.emit(f"istore {index}")
            elif isinstance(var, AssignNode):
                # Загружаем значение
                if isinstance(var.val, LiteralNode):
                    self.visit_literal(var.val)
                elif isinstance(var.val, BinOpNode):
                    self.visit_bin_op(var.val)
                else:
                    self.visit(var.val)
                # Сохраняем в локальную переменную
                self.locals[var.var.name] = len(self.locals)
                index = self.locals[var.var.name]
                if index <= 3:
                    self.emit(f"istore_{index}")
                else:
                    self.emit(f"istore {index}")
            elif isinstance(var, IdentNode):
                self.locals[var.name] = len(self.locals)
                index = self.locals[var.name]
                self.emit("iconst_0")
                if index <= 3:
                    self.emit(f"istore_{index}")
                else:
                    self.emit(f"istore {index}")
                    
    def visit_TypedDeclNode(self, node: TypedDeclNode) -> None:
        if isinstance(node.assign_node, AssignNode):
            if isinstance(node.assign_node.val, LiteralNode):
                self.visit_literal(node.assign_node.val)
            elif isinstance(node.assign_node.val, BinOpNode):
                self.visit_bin_op(node.assign_node.val)
            else:
                self.visit(node.assign_node.val)
            self.locals[node.assign_node.var.name] = len(self.locals)
            index = self.locals[node.assign_node.var.name]
            if index <= 3:
                self.emit(f"istore_{index}")
            else:
                self.emit(f"istore {index}") 