from mel_ast import *
from scope import Scope


class SemanticAnalyzer:
    def __init__(self):
        self.errors = []
        self.current_scope = Scope()
        self.global_scope = self.current_scope
        self.classes = {}
        self.functions = {}

    def add_error(self, msg: str):
        if msg not in self.errors:
            self.errors.append(msg)

    def analyze(self, node):
        self.visit(node)

    def visit(self, node):
        if isinstance(node, list):
            for item in node:
                self.visit(item)
            return
        method_name = f'visit_{type(node).__name__}'
        method = getattr(self, method_name, self.generic_visit)
        method(node)

    def visit_StmtListNode(self, node):
        parent = self.current_scope
        self.current_scope = Scope(parent=parent)
        for stmt in node.stmts:
            self.visit(stmt)
        self.current_scope = parent

    def visit_VarsDeclNode(self, node):
        var_type = get_type_from_typename(node.type.typename)

        def flatten(lst):
            for item in lst:
                if isinstance(item, list):
                    yield from flatten(item)
                else:
                    yield item

        for var in flatten(node.vars):
            if isinstance(var, AssignNode):
                self.visit(var.val)
                if isinstance(var.var, IdentNode):
                    var_name = var.var.name
                    value_type = get_type_from_node(var.val)
                    if value_type is None and isinstance(var.val, IdentNode):
                        value_type = self.current_scope.lookup(var.val.name)
                    if value_type is None:
                        continue
                    if not equals_simple_type(var_type, value_type):
                        self.add_error(f"Присвоение {value_type} в переменную типа {var_type} внутри блока")
                    try:
                        self.current_scope.declare(var_name, var_type)
                    except Exception as e:
                        self.add_error(str(e))
            elif isinstance(var, IdentNode):
                try:
                    self.current_scope.declare(var.name, var_type)
                except Exception as e:
                    self.add_error(str(e))

    def visit_AssignNode(self, node):
        self.visit(node.val)

        if isinstance(node.val, FuncCallNode):
            return

        if isinstance(node.var, MemberAccessNode):
            obj_name = node.var.obj.name
            field_name = node.var.member.name
            obj_type = self.current_scope.lookup(obj_name)
            if not isinstance(obj_type, ClassType):
                return
            class_def = self.classes.get(obj_type.name)
            if class_def:
                for stmt in class_def.body.stmts:
                    if isinstance(stmt, VarsDeclNode):
                        field_type = get_type_from_typename(stmt.type.typename)
                        for var in stmt.vars:
                            if isinstance(var, IdentNode) and var.name == field_name:
                                value_type = get_type_from_node(node.val)
                                if value_type is None and isinstance(node.val, IdentNode):
                                    value_type = self.current_scope.lookup(node.val.name)
                                if value_type is None:
                                    return
                                if not equals_simple_type(field_type, value_type):
                                    self.add_error(f"Присвоение {value_type} в поле типа {field_type} внутри класса")
                                return
            return

        if isinstance(node.var, IdentNode):
            var_name = node.var.name
            value_type = get_type_from_node(node.val)
            if value_type is None and isinstance(node.val, IdentNode):
                value_type = self.current_scope.lookup(node.val.name)
            if value_type is None:
                return
            var_type = self.current_scope.lookup(var_name)
            if var_type is None:
                self.add_error(f"Переменная {var_name} не объявлена в глобальной области видимости")
                return
            if not equals_simple_type(var_type, value_type):
                self.add_error(f"Присвоение {value_type} в переменную типа {var_type} внутри блока")

    def visit_ArrayAssignNode(self, node: ArrayAssignNode):
        array_type = self.current_scope.lookup(node.ident.name)
        if array_type is None or not isinstance(array_type, ArrayType):
            return  # тип будет проверен в другом месте при объявлении
        value_type = get_type_from_node(node.value)
        if value_type is None and isinstance(node.value, IdentNode):
            value_type = self.current_scope.lookup(node.value.name)
        if value_type is None:
            return
        if not equals_simple_type(array_type.base_type, value_type):
            self.add_error(f"Присвоение {value_type} в элемент массива типа {array_type.base_type}")

    def visit_IfNode(self, node):
        self.visit(node.cond)
        self.check_boolean_condition(node.cond)

        parent = self.current_scope
        self.current_scope = Scope(parent=parent)
        self.visit(node.then_stmt)
        self.current_scope = parent

        if node.else_stmt:
            self.current_scope = Scope(parent=parent)
            self.visit(node.else_stmt)
            self.current_scope = parent

    def check_boolean_condition(self, cond_node):
        cond_type = get_type_from_node(cond_node)
        if not isinstance(cond_type, PrimitiveType) or cond_type.name != "bool":
            self.add_error(f"Condition must be boolean, got {cond_type}")

    def visit_FuncDeclNode(self, node):
        self.functions[node.name.name] = node
        self.visit(node.body)

    def visit_FuncCallNode(self, node: FuncCallNode):
        func_decl = self.functions.get(node.func.name)
        if not func_decl:
            self.add_error(f"Функция {node.func.name} не найдена")
            return

        expected_types = []
        for param in func_decl.params.vars:
            param_type = get_type_from_typename(param.type.typename)
            for _ in param.vars:
                expected_types.append(param_type)

        if len(expected_types) != len(node.params):
            self.add_error(f"Неверное количество аргументов в функции {node.func.name}")
            return

        for expected, actual in zip(expected_types, node.params):
            actual_type = get_type_from_node(actual)
            if actual_type is None and isinstance(actual, IdentNode):
                actual_type = self.current_scope.lookup(actual.name)
            if actual_type is None:
                continue
            if not equals_simple_type(expected, actual_type):
                self.add_error(f"Передан аргумент {actual_type} вместо {expected} в функцию {node.func.name}")

    def visit_ClassDeclNode(self, node):
        self.classes[node.name.name] = node
        self.visit(node.body)

    def generic_visit(self, node):
        if hasattr(node, 'children'):
            for child in node.children:
                if child is not None:
                    self.visit(child)


def get_type_from_typename(typename: str) -> Type:
    if typename == "int": return PrimitiveType("int")
    if typename == "float": return PrimitiveType("float")
    if typename == "string": return PrimitiveType("string")
    if typename == "bool": return PrimitiveType("bool")
    if typename.endswith("[]"):
        return ArrayType(get_type_from_typename(typename[:-2]))
    return ClassType(typename)