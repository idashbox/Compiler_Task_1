from mel_ast import IdentNode, AssignNode, LiteralNode, VarsDeclNode, FuncCallNode, FuncDeclNode


class SemanticAnalyzer:
    def __init__(self):
        self.errors = []
        self.symbols = {}
        self.functions = {}

    def analyze(self, tree):
        self.visit(tree)

    def visit(self, node):
        method = getattr(self, f'visit_{type(node).__name__}', self.generic_visit)
        return method(node)

    def generic_visit(self, node):
        if isinstance(node, list):
            for child in node:
                self.visit(child)
        elif hasattr(node, 'children'):
            for child in node.children:
                self.visit(child)

    def visit_VarsDeclNode(self, node: VarsDeclNode):
        var_type = node.type.typename

        for var in node.vars:
            if isinstance(var, AssignNode):
                var_name = var.var.name
                value_type = self.visit(var.val)

                if not self.check_type_compatibility(var_type, value_type):
                    self.errors.append(
                        f"Несовместимые типы: нельзя присвоить {value_type} переменной типа {var_type}"
                    )
                self.symbols[var_name] = var_type

            elif isinstance(var, IdentNode):
                var_name = var.name
                self.symbols[var_name] = var_type

    def visit_AssignNode(self, node: AssignNode):
        var_name = node.var.name

        if var_name not in self.symbols:
            self.errors.append(f"Переменная {var_name} не объявлена.")
            return None

        expected_type = self.symbols[var_name]
        value_type = self.visit(node.val)

        if not self.check_type_compatibility(expected_type, value_type):
            self.errors.append(
                f"Ошибка типа: нельзя присвоить {value_type} переменной типа {expected_type}"
            )

    def visit_FuncDeclNode(self, node: FuncDeclNode):
        func_name = node.name.name
        if func_name in self.functions:
            self.errors.append(f"Функция {func_name} уже определена")
        else:
            self.functions[func_name] = node

        self.visit(node.params)
        self.visit(node.body)

    def visit_FuncCallNode(self, node):
        func = self.lookup_function(node.func)
        if func is None:
            self.errors.append(f"Функция {node.func.name} не определена")
            return None

        if len(node.params) != len(func.params):
            self.errors.append(
                f"Неверное количество аргументов при вызове функции {node.func.name}. "
                f"Ожидалось {len(func.params)}, получено {len(node.params)}"
            )
            return func.return_type.typename if hasattr(func, 'return_type') else "unknown"

        return func.return_type.typename if hasattr(func, 'return_type') else "unknown"

    def visit_LiteralNode(self, node: LiteralNode):
        if isinstance(node.value, int):
            return "int"
        elif isinstance(node.value, float):
            return "float"
        elif isinstance(node.value, str):
            return "string"
        elif isinstance(node.value, bool):
            return "bool"
        return "unknown"

    def visit_IdentNode(self, node: IdentNode):
        return self.symbols.get(node.name, "unknown")

    def lookup_function(self, name_node):
        name = name_node.name if isinstance(name_node, IdentNode) else name_node
        return self.functions.get(name, None)

    def check_type_compatibility(self, declared_type, value_type):
        if declared_type == value_type:
            return True
        if declared_type == "float" and value_type == "int":
            return True
        return False
