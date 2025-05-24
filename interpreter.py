from mel_ast import *
from itertools import chain


class Interpreter:
    def __init__(self):
        self.variables = {}
        self.functions = {}
        self.classes = {}

    def eval(self, node: AstNode):
        method_name = f'eval_{type(node).__name__}'
        method = getattr(self, method_name, self.generic_eval)
        return method(node)

    def generic_eval(self, node: AstNode):
        raise Exception(f'No eval_{type(node).__name__} method')

    def eval_LiteralNode(self, node: LiteralNode):
        return node.value

    def eval_IdentNode(self, node: IdentNode):
        val = self.variables.get(node.name)
        if val is None:
            print(f"[WARN] Переменная '{node.name}' не определена!")
        return val

    def eval_AssignNode(self, node: AssignNode):
        value = self.eval(node.val)
        if isinstance(node.var, IdentNode):
            # Простое присваивание переменной
            name = node.var.name
            self.variables[name] = value
        elif isinstance(node.var, MemberAccessNode):
            # Присваивание полю объекта
            obj_name = node.var.obj.name  # Имя объекта (например, "p")
            field_name = node.var.member.name  # Имя поля (например, "x")
            obj = self.variables.get(obj_name)
            if obj is None:
                raise Exception(f"Объект '{obj_name}' не определён")
            if not isinstance(obj, dict):
                raise Exception(f"'{obj_name}' не является объектом")
            obj[field_name] = value
        else:
            raise Exception(f"Неподдерживаемый тип переменной в присваивании: {type(node.var)}")
        return value

    def eval_ArrayNode(self, node: ArrayNode):
        return [self.eval(el) for el in node.elements]

    def eval_ArrayAssignNode(self, node: ArrayAssignNode):
        array = self.variables.get(node.ident.name)
        if array is None or not isinstance(array, list):
            raise Exception(f"Variable {node.ident.name} is not an array")

        index = self.eval(node.index)
        value = self.eval(node.value)
        array[index] = value
        return value

    def visit_ArrayAccessNode(self, node):
        array = self.visit(node.array)
        index = self.visit(node.index)
        return array[index]  # с проверками границ и типов, как писал выше

    def visit_ArrayElementAssignNode(self, node):
        array = self.visit(node.array_access.array)
        index = self.visit(node.array_access.index)
        value = self.visit(node.value)

        if not isinstance(array, list):
            raise RuntimeError("Попытка обратиться к не-массиву")

        if not (0 <= index < len(array)):
            raise RuntimeError("Индекс вне границ массива")

        array[index] = value

    def eval_NewInstanceNode(self, node: NewInstanceNode):
        class_name = node.class_name.name
        class_node = self.classes.get(class_name)
        if not class_node:
            raise Exception(f"Класс '{class_name}' не определён")

        # Создаём новый объект как словарь
        obj = {}
        # Инициализируем поля класса значениями по умолчанию или заданными значениями
        for stmt in class_node.body.stmts:
            if isinstance(stmt, VarsDeclNode):
                for var in stmt.vars:
                    if isinstance(var, IdentNode):
                        # Значение по умолчанию для примитивных типов
                        type_name = stmt.type.typename
                        if type_name == "int":
                            obj[var.name] = 0
                        elif type_name == "float":
                            obj[var.name] = 0.0
                        elif type_name == "bool":
                            obj[var.name] = False
                        elif type_name == "string":
                            obj[var.name] = ""
                        else:
                            obj[var.name] = None  # Для классов или массивов
                    elif isinstance(var, AssignNode):
                        # Если поле инициализировано значением
                        obj[var.var.name] = self.eval(var.val)
        return obj

    def eval_BinOpNode(self, node: BinOpNode):
        left = self.eval(node.arg1)
        right = self.eval(node.arg2)
        op = node.op

        if op == BinOp.ADD: return left + right
        if op == BinOp.SUB: return left - right
        if op == BinOp.MUL: return left * right
        if op == BinOp.DIV: return left / right
        if op == BinOp.MOD: return left % right
        if op == BinOp.EQ: return left == right
        if op == BinOp.NE: return left != right
        if op == BinOp.GT: return left > right
        if op == BinOp.LT: return left < right
        if op == BinOp.GE: return left >= right
        if op == BinOp.LE: return left <= right
        if op == BinOp.AND: return left and right
        if op == BinOp.OR: return left or right

        raise Exception(f'Unsupported operator {op}')

    def eval_UnaryOpNode(self, node: UnaryOpNode):
        val = self.eval(node.arg)
        if node.op == UnaryOp.NEG:
            return -val
        elif node.op == UnaryOp.NOT:
            return not val
        else:
            raise Exception(f"Unknown unary operator {node.op}")

    def eval_StmtListNode(self, node):
        def flatten(stmts):
            for stmt in stmts:
                if isinstance(stmt, list):
                    yield from flatten(stmt)
                else:
                    yield stmt

        for stmt in flatten(node.stmts):
            result = self.eval(stmt)
            if isinstance(stmt, ReturnNode):
                return result
        return None

    def eval_IfNode(self, node: IfNode):
        cond = self.eval(node.cond)
        if cond:
            return self.eval(node.then_stmt)
        elif node.else_stmt:
            return self.eval(node.else_stmt)

    def eval_WhileNode(self, node: WhileNode):
        while self.eval(node.cond):
            self.eval(node.body)

    def eval_ReturnNode(self, node):
        return self.eval(node.result)

    def eval_ClassDeclNode(self, node: ClassDeclNode):
        self.classes[node.name.name] = node
        return None

    def eval_VarsDeclNode(self, node: VarsDeclNode):
        def flatten(stmts):
            for stmt in stmts:
                if isinstance(stmt, list):
                    yield from flatten(stmt)
                else:
                    yield stmt

        type_name = node.type.typename  # Имя типа (например, "Point", "int", "int[]")
        is_class_type = type_name in self.classes  # Проверяем, является ли тип классом

        for decl in flatten(node.vars):
            if isinstance(decl, IdentNode):
                var_name = decl.name
                if is_class_type:
                    # Для классов переменная изначально None, если не инициализирована
                    self.variables[var_name] = None
                else:
                    # Для примитивных типов просто объявляем переменную
                    self.variables[var_name] = None
            elif isinstance(decl, AssignNode):
                var_name = decl.var.name
                value = self.eval(decl.val)
                if is_class_type and isinstance(decl.val, NewInstanceNode):
                    # Если это new Point(), то value уже является объектом
                    self.variables[var_name] = value
                else:
                    self.variables[var_name] = value
            else:
                print(f"[WARN] Неизвестный элемент в VarsDeclNode: {decl}")

    def eval_FuncDeclNode(self, node: FuncDeclNode):
        self.functions[node.name.name] = node
        return None

    def eval_FuncCallNode(self, node: FuncCallNode):
        func = self.functions.get(node.func.name)
        if not func:
            raise Exception(f"Function {node.func.name} not found")

        old_variables = self.variables.copy()

        self.variables = {}

        params = [self.eval(arg) for arg in node.params]

        param_decls = list(chain.from_iterable(
            [decl.vars if isinstance(decl, VarsDeclNode) else [decl] for decl in func.params.vars]
        ))

        for decl, arg in zip(param_decls, params):
            if isinstance(decl, AssignNode):
                self.variables[decl.var.name] = arg
            elif isinstance(decl, IdentNode):
                self.variables[decl.name] = arg

        result = self.eval(func.body)

        self.variables = old_variables
        return result
