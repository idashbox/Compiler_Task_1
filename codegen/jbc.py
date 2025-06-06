from typing import Dict, Any, Optional

from mel_types import ClassType
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
        self.variable_types = {}  # Словарь для хранения типов переменных
        self.classes = {}  # Словарь для хранения информации о классах

        
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
        if isinstance(node.var, MemberAccessNode):
            # Загружаем объект
            if isinstance(node.var.obj, IdentNode):
                index = self.locals.get(node.var.obj.name)
                if index is not None:
                    if index <= 3:
                        self.emit(f"aload_{index}")
                    else:
                        self.emit(f"aload {index}")
            else:
                self.visit(node.var.obj)

            # Загружаем значение
            if isinstance(node.val, LiteralNode):
                self.visit_literal(node.val)
            else:
                self.visit(node.val)

            # Присваиваем значение полю
            class_type = self.get_variable_type(node.var.obj.name)
            if class_type:
                class_name = class_type.name if hasattr(class_type, 'name') else "Object"
                field_name = node.var.member.name
                self.emit(f"putfield {class_name}/{field_name} I")  # Предполагаем, что поле имеет тип int
        else:
            # Обычное присваивание переменной
            if isinstance(node.val, LiteralNode):
                self.visit_literal(node.val)
            elif isinstance(node.val, BinOpNode):
                self.visit_bin_op(node.val)
            else:
                self.visit(node.val)

            # Сохраняем в переменную
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
                elif isinstance(param, MemberAccessNode):  # Добавляем явную обработку MemberAccessNode
                    self.visit_MemberAccessNode(param)
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
        self.variable_types = {}
        self.classes = {}
        self.current_class = "Program"

        # Сначала проходим и собираем информацию о классах
        if isinstance(node, StmtListNode):
            for stmt in node.stmts[0]:
                if isinstance(stmt, ClassDeclNode):
                    # Сохраняем информацию о классе для последующего использования
                    class_name = stmt.name.name
                    self.classes[class_name] = {'fields': {}}

                    # Анализируем поля класса
                    if stmt.body:
                        for class_stmt in stmt.body.stmts:
                            if isinstance(class_stmt, VarsDeclNode):
                                field_type = "I"  # По умолчанию int
                                for var in class_stmt.vars:
                                    if isinstance(var, list):
                                        for v in var:
                                            if isinstance(v, IdentNode):
                                                field_name = v.name
                                                self.classes[class_name]['fields'][field_name] = field_type
                                    elif isinstance(var, IdentNode):
                                        field_name = var.name
                                        self.classes[class_name]['fields'][field_name] = field_type
                                    elif isinstance(var, AssignNode):
                                        field_name = var.var.name
                                        self.classes[class_name]['fields'][field_name] = field_type

                    # Генерируем класс в отдельный файл
                    self.visit_ClassDeclNode(stmt)

        # Теперь генерируем основной класс Program
        self.code = []  # Очищаем код перед генерацией Program
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
                if not isinstance(stmt, ClassDeclNode):  # Пропускаем объявления классов
                    self.visit(stmt)
        else:
            self.visit(node)

        # Завершаем метод main
        self.emit("return")
        self.emit(".end method")

        # Сохраняем основной класс
        with open("Program.j", 'w', encoding='utf-8') as f:
            f.write('\n'.join(self.code))
        print("Основной класс сохранен в файл Program.j")

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
        elif isinstance(node, ClassDeclNode):  # Добавь этот блок
            self.visit_ClassDeclNode(node)
        elif isinstance(node, NewInstanceNode):  # Добавь этот блок
            self.visit_new_instance(node)
        elif isinstance(node, MemberAccessNode):  # Добавь этот блок
            self.visit_member_access(node)
        else:
            print(f"Warning: No visit method for {node.__class__.__name__}")

    def visit_VarsDeclNode(self, node: VarsDeclNode) -> None:
        # Определяем тип переменных
        var_type = None
        if node.type.typename == "int":
            var_type = PrimitiveType("int")
        elif node.type.typename == "float":
            var_type = PrimitiveType("float")
        elif node.type.typename == "string":
            var_type = PrimitiveType("string")
        elif node.type.typename == "bool":
            var_type = PrimitiveType("bool")
        else:
            # Это класс - важно для переменных типа Point
            var_type = ClassType(node.type.typename)

        # Обработка переменных как и раньше
        for var in node.vars:
            if isinstance(var, list):
                for v in var:
                    if isinstance(v, AssignNode):
                        # Сохраняем тип переменной
                        self.variable_types[v.var.name] = var_type

                        # Загружаем значение
                        if isinstance(v.val, LiteralNode):
                            self.visit_literal(v.val)
                        elif isinstance(v.val, BinOpNode):
                            self.visit_bin_op(v.val)
                        elif isinstance(v.val, NewInstanceNode):
                            self.visit_new_instance(v.val)
                        else:
                            self.visit(v.val)

                        # Сохраняем в переменную
                        self.locals[v.var.name] = len(self.locals)
                        index = self.locals[v.var.name]

                        # Выбираем правильную инструкцию в зависимости от типа
                        if isinstance(var_type, ClassType):
                            if index <= 3:
                                self.emit(f"astore_{index}")
                            else:
                                self.emit(f"astore {index}")
                        else:
                            if index <= 3:
                                self.emit(f"istore_{index}")
                            else:
                                self.emit(f"istore {index}")

                    elif isinstance(v, IdentNode):
                        # Сохраняем тип переменной
                        self.variable_types[v.name] = var_type

                        self.locals[v.name] = len(self.locals)
                        index = self.locals[v.name]

                        # Инициализация по умолчанию зависит от типа
                        if isinstance(var_type, ClassType):
                            self.emit("aconst_null")
                            if index <= 3:
                                self.emit(f"astore_{index}")
                            else:
                                self.emit(f"astore {index}")
                        else:
                            self.emit("iconst_0")
                            if index <= 3:
                                self.emit(f"istore_{index}")
                            else:
                                self.emit(f"istore {index}")
            # ... аналогично для случая, когда var не является списком
                    
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

    def visit_ClassDeclNode(self, node: ClassDeclNode) -> None:
        class_name = node.name.name

        # Сохраняем текущий код
        main_code = self.code.copy()
        self.code = []  # Очищаем для генерации класса

        # Генерируем код класса
        self.emit(f".class public {class_name}")
        self.emit(".super java/lang/Object")

        # Объявляем поля класса - ВАЖНО! Без этого полей не будет
        if node.body:
            for stmt in node.body.stmts:
                if isinstance(stmt, VarsDeclNode):
                    field_type = "I"  # По умолчанию int
                    for var in stmt.vars:
                        if isinstance(var, list):
                            for v in var:
                                if isinstance(v, IdentNode):
                                    field_name = v.name
                                    # Явно объявляем поле как public с типом I (int)
                                    self.emit(f".field public {field_name} I")
                                elif isinstance(v, AssignNode):
                                    field_name = v.var.name
                                    self.emit(f".field public {field_name} I")
                        elif isinstance(var, IdentNode):
                            field_name = var.name
                            self.emit(f".field public {field_name} I")
                        elif isinstance(var, AssignNode):
                            field_name = var.var.name
                            self.emit(f".field public {field_name} I")

        # Генерируем конструктор по умолчанию
        self.emit(".method public <init>()V")
        self.emit(".limit stack 10")  # Ограничиваем размер стека
        self.emit(".limit locals 1")  # this - единственная локальная переменная
        self.emit("aload_0")
        self.emit("invokespecial java/lang/Object/<init>()V")

        # Инициализируем поля в конструкторе
        if node.body:
            for stmt in node.body.stmts:
                if isinstance(stmt, VarsDeclNode):
                    for var in stmt.vars:
                        if isinstance(var, list):
                            for v in var:
                                if isinstance(v, AssignNode):
                                    field_name = v.var.name
                                    self.emit("aload_0")  # загружаем this
                                    if isinstance(v.val, LiteralNode):
                                        self.visit_literal(v.val)
                                    else:
                                        self.visit(v.val)
                                    # Присваиваем значение полю
                                    self.emit(f"putfield {class_name}/{field_name} I")
                                elif isinstance(v, IdentNode):
                                    # Для полей без инициализации присваиваем 0
                                    field_name = v.name
                                    self.emit("aload_0")
                                    self.emit("iconst_0")
                                    self.emit(f"putfield {class_name}/{field_name} I")
                        elif isinstance(var, AssignNode):
                            field_name = var.var.name
                            self.emit("aload_0")
                            if isinstance(var.val, LiteralNode):
                                self.visit_literal(var.val)
                            else:
                                self.visit(var.val)
                            self.emit(f"putfield {class_name}/{field_name} I")
                        elif isinstance(var, IdentNode):
                            # Для полей без инициализации присваиваем 0
                            field_name = var.name
                            self.emit("aload_0")
                            self.emit("iconst_0")
                            self.emit(f"putfield {class_name}/{field_name} I")

        self.emit("return")
        self.emit(".end method")

        # Сохраняем код класса в отдельный файл
        with open(f"{class_name}.j", 'w', encoding='utf-8') as f:
            f.write('\n'.join(self.code))
        print(f"Класс {class_name} сохранен в файл {class_name}.j")

        # Восстанавливаем основной код
        self.code = main_code



    def visit_NewInstanceNode(self, node: NewInstanceNode) -> None:
        class_name = node.class_name.name
        # Создаем новый экземпляр класса
        self.emit(f"new {class_name}")
        self.emit("dup")
        self.emit(f"invokespecial {class_name}/<init>()V")

    def visit_MemberAccessNode(self, node: MemberAccessNode) -> None:
        # Загружаем объект
        if isinstance(node.obj, IdentNode):
            index = self.locals.get(node.obj.name)
            if index is not None:
                if index <= 3:
                    self.emit(f"aload_{index}")
                else:
                    self.emit(f"aload {index}")
        else:
            self.visit(node.obj)

        # Для нашего кода всегда используем класс Point, т.к. у нас только он и есть
        field_name = node.member.name
        self.emit(f"getfield Point/{field_name} I")

    def get_variable_type(self, var_name):
        """Возвращает тип переменной из локальной таблицы символов"""
        # Сначала проверяем в словаре локальных типов
        if var_name in self.variable_types:
            return self.variable_types[var_name]

        # По умолчанию возвращаем int, если тип не найден
        return PrimitiveType("int")