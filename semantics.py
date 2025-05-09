from mel_ast import *
from scope import Scope
from mel_types import get_type_from_node, equals_simple, PrimitiveType, ArrayType, ClassType, Type, equals_simple_type

from mel_ast import *
from scope import Scope
from mel_types import (get_type_from_node, equals_simple, PrimitiveType,
                       ArrayType, ClassType, Type, equals_simple_type)


class SemanticAnalyzer:
    def __init__(self):
        self.errors = []
        self.current_scope = Scope()
        self.global_scope = self.current_scope
        self.classes = {}
        self.functions = {}

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
        old_scope = self.current_scope
        self.current_scope = Scope(parent=old_scope)
        for stmt in node.stmts:
            self.visit(stmt)
        self.current_scope = old_scope

    def visit_VarsDeclNode(self, node):
        var_type = get_type_from_node(node.type)
        for var in node.vars:
            if isinstance(var, AssignNode):
                var_name = var.var.name
                value_type = get_type_from_node(var.val)

                if not equals_simple_type(var_type, value_type):
                    self.errors.append(
                        f"Type mismatch: cannot assign {value_type} to {var_type}"
                    )

                try:
                    self.current_scope.declare(var_name, var_type)
                except Exception as e:
                    self.errors.append(str(e))
            elif isinstance(var, IdentNode):
                try:
                    self.current_scope.declare(var.name, var_type)
                except Exception as e:
                    self.errors.append(str(e))

    def visit_AssignNode(self, node):
        var_name = node.var.name
        value_type = get_type_from_node(node.val)

        # Ищем переменную в цепочке областей видимости
        var_type = None
        current_scope = self.current_scope
        while current_scope:
            var_type = current_scope.lookup(var_name)
            if var_type: break
            current_scope = current_scope.parent

        if not var_type:
            # Проверяем, может быть это обращение к полю класса
            if '.' in var_name:
                parts = var_name.split('.')
                obj_name = parts[0]
                field_name = parts[1]

                obj_type = None
                current_scope = self.current_scope
                while current_scope:
                    obj_type = current_scope.lookup(obj_name)
                    if obj_type: break
                    current_scope = current_scope.parent

                if obj_type and isinstance(obj_type, ClassType):
                    class_info = self.classes.get(obj_type.name)
                    if class_info:
                        field_type = class_info['fields'].get(field_name)
                        if field_type:
                            if not equals_simple_type(field_type, value_type):
                                self.errors.append(
                                    f"Type mismatch: cannot assign {value_type} to field {field_name} of type {field_type}"
                                )
                            return
            self.errors.append(f"Undefined variable '{var_name}'")
            return

        if not equals_simple_type(var_type, value_type):
            self.errors.append(
                f"Type mismatch: cannot assign {value_type} to {var_type}"
            )

    def visit_ArrayAssignNode(self, node):
        # Получаем тип массива
        array_type = None
        current_scope = self.current_scope
        while current_scope:
            array_type = current_scope.lookup(node.ident.name)
            if array_type: break
            current_scope = current_scope.parent

        if not array_type or not isinstance(array_type, ArrayType):
            self.errors.append(f"'{node.ident.name}' is not an array")
            return

        # Проверяем тип индекса
        index_type = get_type_from_node(node.index)
        if not isinstance(index_type, PrimitiveType) or index_type.name != "int":
            self.errors.append(f"Array index must be int, got {index_type}")

        # Проверяем тип значения
        value_type = get_type_from_node(node.value)
        if not equals_simple_type(array_type.base_type, value_type):
            self.errors.append(
                f"Cannot assign {value_type} to array element of type {array_type.base_type}"
            )

    def visit_IfNode(self, node):
        self.visit(node.cond)
        self.check_boolean_condition(node.cond)

        old_scope = self.current_scope
        self.current_scope = Scope(parent=old_scope)
        self.visit(node.then_stmt)
        self.current_scope = old_scope

        if node.else_stmt:
            self.current_scope = Scope(parent=old_scope)
            self.visit(node.else_stmt)
            self.current_scope = old_scope

    def visit_FuncDeclNode(self, node):
        # Сохраняем информацию о функции
        func_type = get_type_from_node(node.return_type)
        param_types = []
        for param in node.params.vars:
            param_types.append(get_type_from_node(param.type))

        self.functions[node.name.name] = {
            'return_type': func_type,
            'param_types': param_types,
            'params': node.params,
            'body': node.body
        }

        # Анализируем параметры и тело функции
        old_scope = self.current_scope
        self.current_scope = Scope(parent=old_scope)

        # Добавляем параметры в область видимости
        for param in node.params.vars:
            self.visit(param)

        self.visit(node.body)
        self.current_scope = old_scope

    def visit_FuncCallNode(self, node):
        func_info = self.functions.get(node.func.name)
        if not func_info:
            self.errors.append(f"Function '{node.func.name}' not defined")
            return

        if len(node.params) != len(func_info['param_types']):
            self.errors.append(
                f"Function '{node.func.name}' expects {len(func_info['param_types'])} arguments, got {len(node.params)}"
            )
            return

        for param_node, expected_type in zip(node.params, func_info['param_types']):
            param_type = get_type_from_node(param_node)
            if not equals_simple_type(expected_type, param_type):
                self.errors.append(
                    f"Parameter type mismatch: expected {expected_type}, got {param_type}"
                )

    def visit_ClassDeclNode(self, node):
        class_name = node.name.name
        self.classes[class_name] = {
            'name': class_name,
            'fields': {},
            'body': node.body
        }

        # Собираем информацию о полях класса
        for stmt in node.body.stmts:
            if isinstance(stmt, VarsDeclNode):
                field_type = get_type_from_node(stmt.type)
                for var in stmt.vars:
                    if isinstance(var, (IdentNode, AssignNode)):
                        var_name = var.name if isinstance(var, IdentNode) else var.var.name
                        self.classes[class_name]['fields'][var_name] = field_type

        # Добавляем класс в текущую область видимости
        self.current_scope.declare(class_name, ClassType(class_name))

    def visit_MemberAccessNode(self, node):
        obj_type = get_type_from_node(node.obj)
        if not isinstance(obj_type, ClassType):
            self.errors.append(f"'{node.obj}' is not a class instance")
            return

        class_info = self.classes.get(obj_type.name)
        if not class_info:
            self.errors.append(f"Class '{obj_type.name}' not defined")
            return

        field_type = class_info['fields'].get(node.member.name)
        if not field_type:
            self.errors.append(f"Class '{obj_type.name}' has no field '{node.member.name}'")
            return

        return field_type

    def check_boolean_condition(self, cond_node):
        cond_type = get_type_from_node(cond_node)
        if not isinstance(cond_type, PrimitiveType) or cond_type.name != "bool":
            self.errors.append(f"Condition must be boolean, got {cond_type}")

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