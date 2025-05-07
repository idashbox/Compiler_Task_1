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
        var_type = get_type_from_typename(node.type.typename)
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
            self.errors.append(f"Undefined variable '{var_name}'")
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


def get_type_from_typename(typename: str) -> Type:
    if typename == "int": return PrimitiveType("int")
    if typename == "float": return PrimitiveType("float")
    if typename == "string": return PrimitiveType("string")
    if typename == "bool": return PrimitiveType("bool")
    if typename.endswith("[]"):
        return ArrayType(get_type_from_typename(typename[:-2]))
    return ClassType(typename)