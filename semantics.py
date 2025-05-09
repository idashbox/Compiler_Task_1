from mel_ast import *
from scope import Scope
from mel_types import get_type_from_node, equals_simple, PrimitiveType, ArrayType, ClassType, Type, equals_simple_type


class SemanticAnalyzer:
    def __init__(self):
        self.errors = []
        self.current_scope = Scope()
        self.global_scope = self.current_scope
        self.classes = {}
        self.functions = {}

        self.reported_errors = set()

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
        for var in node.vars:
            self.visit(var)

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
            if ("Undefined variable", var_name) not in self.reported_errors:
                self.errors.append(f"Undefined variable '{var_name}'")
                self.reported_errors.add(("Undefined variable", var_name))
            return

        if not equals_simple_type(var_type, value_type):
            self.errors.append(
                f"Type mismatch: cannot assign {value_type} to {var_type}"
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

    def check_boolean_condition(self, cond_node):
        cond_type = get_type_from_node(cond_node)
        if not isinstance(cond_type, PrimitiveType) or cond_type.name != "bool":
            self.errors.append(f"Condition must be boolean, got {cond_type}")

    def generic_visit(self, node):
        if hasattr(node, 'children'):
            for child in node.children:
                if child is not None:
                    self.visit(child)

    def visit_TypedDeclNode(self, node):
        var_type = get_type_from_node(node.var_type)

        # Если это объявление с присваиванием
        if isinstance(node.var_node, AssignNode):
            var_name = node.var_node.target.name
            self.visit(node.var_node.value)
            value_type = get_type_from_node(node.var_node.value)

            if not equals_simple_type(var_type, value_type):
                self.errors.append(f"Присвоение {value_type} в переменную типа {var_type}")

            self.current_scope.define(var_name, var_type)
        else:
            # Просто объявление без инициализации
            var_name = node.var_node.name
            self.current_scope.define(var_name, var_type)


def get_type_from_typename(typename: str) -> Type:
    if typename == "int": return PrimitiveType("int")
    if typename == "float": return PrimitiveType("float")
    if typename == "string": return PrimitiveType("string")
    if typename == "bool": return PrimitiveType("bool")
    if typename.endswith("[]"):
        return ArrayType(get_type_from_typename(typename[:-2]))
    return ClassType(typename)