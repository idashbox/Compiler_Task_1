from mel_ast import *
from scope import Scope
from mel_types import PrimitiveType, ArrayType, ClassType, Type, equals_simple_type, get_type_from_typename, INT


class SemanticAnalyzer:
    def __init__(self):
        self.errors = []
        self.current_scope = Scope()
        self.global_scope = self.current_scope
        self.classes = {}
        self.functions = {}
        self._visited_nodes = set()

    def get_type_from_node(self, node):
        if isinstance(node, LiteralNode):
            value = node.value
            if isinstance(value, bool):
                return PrimitiveType("bool")
            elif isinstance(value, int):
                return PrimitiveType("int")
            elif isinstance(value, float):
                return PrimitiveType("float")
            elif isinstance(value, str):
                return PrimitiveType("string")
        elif isinstance(node, IdentNode):
            if node.name in ['int', 'float', 'string', 'bool']:
                return get_type_from_typename(node.name)
            current_scope = self.current_scope
            while current_scope:
                var_type = current_scope.lookup(node.name)
                if var_type:
                    return var_type
                current_scope = current_scope.parent
            return PrimitiveType("int")
        elif isinstance(node, ArrayNode):
            if node.elements:
                element_type = self.get_type_from_node(node.elements[0])
                return ArrayType(element_type)
            return ArrayType(PrimitiveType("int"))
        elif isinstance(node, VarsDeclNode):
            return get_type_from_typename(node.type.typename)
        elif isinstance(node, AssignNode):
            return self.get_type_from_node(node.val)
        elif isinstance(node, TypeDeclNode):
            return get_type_from_typename(node.typename)
        elif isinstance(node, ArrayTypeNode):
            return ArrayType(get_type_from_typename(node.name))
        elif isinstance(node, FuncCallNode):
            func_info = self.functions.get(node.func.name)
            return func_info['return_type'] if func_info else PrimitiveType("int")
        elif isinstance(node, NewInstanceNode):
            return self.visit_NewInstanceNode(node)
        elif isinstance(node, MemberAccessNode):
            obj_type = self.get_type_from_node(node.obj)
            print(f"DEBUG: MemberAccessNode: obj={node.obj}, obj_type={obj_type}, member={node.member.name}")
            if isinstance(obj_type, ClassType):
                class_info = self.classes.get(obj_type.name)
                print(f"DEBUG: class_info for {obj_type.name} = {class_info}")
                if class_info:
                    field_type = class_info['fields'].get(node.member.name)
                    print(f"DEBUG: field_type for {node.member.name} = {field_type}")
                    if field_type:
                        return field_type
                    self.errors.append(f"Field '{node.member.name}' not found in class '{obj_type.name}'")
            return None
        return None

    def visit_NewInstanceNode(self, node):
        print(f"Обрабатываем NewInstanceNode: {node}")
        class_name = node.class_name.name
        if class_name not in self.classes:
            self.errors.append(f"Ошибка: класс '{class_name}' не определён")
            return None
        # Здесь можно добавить проверку, что конструктор без параметров существует,
        # но в вашем языке конструкторы не определены явно, поэтому просто возвращаем тип класса
        return ClassType(class_name)

    def visit_VarsDeclNode(self, node):
        print(f"Обрабатываем VarsDeclNode: {node}")
        var_type = get_type_from_typename(node.type.typename)
        print(f"Тип: {var_type}, переменные: {node.vars}")
        vars_flat = []
        for var in node.vars:
            if isinstance(var, list):
                vars_flat.extend(var)
            else:
                vars_flat.append(var)
        for var in vars_flat:
            print(f"Обрабатываем var: {var}")
            if isinstance(var, IdentNode):
                var_name = var.name
                print(f"Объявление переменной: {var_name} типа {var_type} в области {id(self.current_scope)}")
                try:
                    self.current_scope.declare(var_name, var_type)
                    print(f"После объявления: {self.current_scope.symbols}")
                except Exception as e:
                    self.errors.append(str(e))
            elif isinstance(var, AssignNode):
                if isinstance(var.var, MemberAccessNode):
                    value_type = self.get_type_from_node(var.val)
                    member_type = self.get_type_from_node(var.var)
                    print(f"Присваивание полю {var.var}: ожидается {member_type}, получено {value_type}")
                    if member_type and value_type and not equals_simple_type(member_type, value_type):
                        self.errors.append("Ошибка: присвоение string в поле типа int внутри класса")
                else:
                    var_name = var.var.name
                    if id(var.val) not in self._visited_nodes:
                        self._visited_nodes.add(id(var.val))
                        self.visit(var.val)
                    value_type = self.get_type_from_node(var.val)
                    print(
                        f"Объявление переменной: {var_name} типа {var_type} с присваиванием {value_type} в области {id(self.current_scope)}")
                    if not equals_simple_type(var_type, value_type):
                        self.errors.append(f"Type mismatch: cannot assign {value_type} to {var_type}")
                    try:
                        self.current_scope.declare(var_name, var_type)
                        print(f"После объявления: {self.current_scope.symbols}")
                    except Exception as e:
                        self.errors.append(str(e))
            else:
                print(f"Неизвестный тип var: {type(var)}")

    def visit_FuncCallNode(self, node):
        print(f"Обрабатываем FuncCallNode: {node}")
        func_name = node.func.name
        func_info = self.functions.get(func_name)
        if not func_info:
            self.errors.append(f"Undefined function '{func_name}'")
            return None
        expected_param_types = func_info['param_types']
        actual_args = node.params
        if len(actual_args) != len(expected_param_types):
            self.errors.append(
                f"Expected {len(expected_param_types)} arguments for '{func_name}', got {len(actual_args)}")
            return None
        for i, (arg, expected_type) in enumerate(zip(actual_args, expected_param_types)):
            arg_type = self.get_type_from_node(arg)
            print(f"Аргумент {i + 1}: ожидается {expected_type}, получено {arg_type}")
            if not equals_simple_type(arg_type, expected_type):
                self.errors.append("Ошибка: передан аргумент string вместо int")
        return func_info['return_type']

    def visit_AssignNode(self, node):
        if isinstance(node.var, MemberAccessNode):
            member_type = self.get_type_from_node(node.var)
            value_type = self.get_type_from_node(node.val)
            print(f"Присваивание полю {node.var}: ожидается {member_type}, получено {value_type}")
            if member_type and value_type and not self.equals_simple(node.var, node.val):
                self.errors.append(f"Ошибка: присвоение {value_type} полю {node.var} типа {member_type}")
            if id(node.val) not in self._visited_nodes:
                self._visited_nodes.add(id(node.val))
                self.visit(node.val)
        else:
            var_name = node.var.name
            print(f"Поиск переменной '{var_name}' в области {id(self.current_scope)}")
            var_type = None
            current_scope = self.current_scope
            while current_scope:
                var_type = current_scope.lookup(var_name)
                print(f"Проверяем область {id(current_scope)}: {var_type}")
                if var_type:
                    break
                current_scope = current_scope.parent
            if not var_type:
                self.errors.append(f"Ошибка: переменная '{var_name}' не объявлена")
                return
            if id(node.val) not in self._visited_nodes:
                self._visited_nodes.add(id(node.val))
                self.visit(node.val)
            value_type = self.get_type_from_node(node.val)
            if not self.equals_simple(node.var, node.val):
                self.errors.append(f"Ошибка: присвоение {value_type} переменной '{var_name}' типа {var_type}")

    def analyze(self, node):
        print(f"Анализируем узел: {node}")
        self._visited_nodes.clear()
        self.visit(node)
        return self.errors

    def visit(self, node):
        if isinstance(node, list):
            for item in node:
                self.visit(item)
            return
        method_name = f'visit_{type(node).__name__}'
        method = getattr(self, method_name, self.generic_visit)
        print(f"Вызываем метод: {method_name} для {node}")
        return method(node)

    def visit_StmtListNode(self, node):
        print(f"StmtListNode: {len(node.stmts)} операторов, область {id(self.current_scope)}, stmts: {node.stmts}")
        if self.current_scope is self.global_scope:
            for stmt in node.stmts:
                self.visit(stmt)
        else:
            old_scope = self.current_scope
            self.current_scope = Scope(parent=old_scope)
            print(f"Создана новая область: {id(self.current_scope)}, родитель: {id(old_scope)}")
            for stmt in node.stmts:
                self.visit(stmt)
            self.current_scope = old_scope

    def visit_IfNode(self, node):
        if id(node.cond) not in self._visited_nodes:
            self._visited_nodes.add(id(node.cond))
            self.visit(node.cond)
        self.check_boolean_condition(node.cond)
        old_scope = self.current_scope
        self.current_scope = Scope(parent=old_scope)
        print(f"Создана область для if: {id(self.current_scope)}, родитель: {id(old_scope)}")
        self.visit(node.then_stmt)
        self.current_scope = old_scope
        if node.else_stmt:
            self.current_scope = Scope(parent=old_scope)
            self.visit(node.else_stmt)
            self.current_scope = old_scope

    def check_boolean_condition(self, cond_node):
        const_type = self.get_type_from_node(cond_node)
        if not isinstance(const_type, PrimitiveType) or const_type.name != "bool":
            self.errors.append(f"Condition must be boolean, got {const_type}")

    def visit_FuncDeclNode(self, node):
        print(f"Обрабатываем FuncDeclNode: {node}")
        func_name = node.name.name
        return_type = get_type_from_typename(node.return_type.typename)
        param_types = []
        for param in node.params.vars:
            param_type = get_type_from_typename(param.type.typename)
            param_types.append(param_type)
        self.functions[func_name] = {
            'return_type': return_type,
            'param_types': param_types,
            'node': node
        }
        print(f"Функция {func_name} сохранена с возвращаемым типом {return_type} и параметрами {param_types}")
        old_scope = self.current_scope
        self.current_scope = Scope(parent=old_scope)
        print(f"Создана область для функции: {id(self.current_scope)}, родитель: {id(old_scope)}")
        for param, param_type in zip(node.params.vars, param_types):
            for var in param.vars:
                if isinstance(var, IdentNode):
                    self.current_scope.declare(var.name, param_type)
        self.visit(node.body)
        self.current_scope = old_scope

    def visit_ArrayAssignNode(self, node):
        print(f"Обрабатываем ArrayAssignNode: {node}")
        # Получаем тип массива
        array_type = self.get_type_from_node(node.ident)
        if not isinstance(array_type, ArrayType):
            self.errors.append(f"Переменная '{node.ident.name}' не является массивом")
            return
        # Получаем тип элемента массива
        element_type = array_type.base_type
        # Получаем тип присваиваемого значения
        value_type = self.get_type_from_node(node.value)
        print(f"Присваивание элементу массива: ожидается {element_type}, получено {value_type}")
        # Проверяем совместимость типов
        if not equals_simple_type(element_type, value_type):
            self.errors.append(f"Ошибка: присвоение {value_type} в элемент массива типа {element_type}")
        # Проверяем тип индекса
        index_type = self.get_type_from_node(node.index)
        if not equals_simple_type(index_type, INT):
            self.errors.append(f"Ошибка: индекс массива должен быть типа int, получено {index_type}")
        # Обходим дочерние узлы, чтобы избежать повторного посещения
        if id(node.index) not in self._visited_nodes:
            self._visited_nodes.add(id(node.index))
            self.visit(node.index)
        if id(node.value) not in self._visited_nodes:
            self._visited_nodes.add(id(node.value))
            self.visit(node.value)

    def visit_ClassDeclNode(self, node):
        print(f"Обрабатываем ClassDeclNode: {node}")
        class_name = node.name.name
        self.classes[class_name] = {'fields': {}}
        old_scope = self.current_scope
        self.current_scope = Scope(parent=old_scope)
        print(f"Создана область для класса {class_name}: {id(self.current_scope)}")
        for stmt in node.body.stmts:
            if isinstance(stmt, VarsDeclNode):
                var_type = get_type_from_typename(stmt.type.typename)
                vars_flat = []
                for var in stmt.vars:
                    if isinstance(var, list):
                        vars_flat.extend(var)
                    else:
                        vars_flat.append(var)
                for var in vars_flat:
                    if isinstance(var, IdentNode):
                        var_name = var.name
                        self.classes[class_name]['fields'][var_name] = var_type
                        print(f"Добавлено поле {var_name}: {var_type} в класс {class_name}")
                    elif isinstance(var, AssignNode):
                        var_name = var.var.name
                        value_type = self.get_type_from_node(var.val)
                        if not self.equals_simple(var.var, var.val):
                            self.errors.append(
                                f"Type mismatch in field {var_name}: cannot assign {value_type} to {var_type}")
                        self.classes[class_name]['fields'][var_name] = var_type
                        print(f"Добавлено поле {var_name}: {var_type} в класс {class_name}")
                    else:
                        print(f"DEBUG: Неожиданный тип var: {type(var)} в stmt.vars")
        print(f"DEBUG: После обработки класса {class_name}: {self.classes}")
        self.current_scope = old_scope

    def generic_visit(self, node):
        if hasattr(node, 'children'):
            for child in node.children:
                if child is not None and id(child) not in self._visited_nodes:
                    self._visited_nodes.add(id(child))
                    self.visit(child)

    def equals_simple(self, node1: AstNode, node2: AstNode) -> bool:
        type1 = self.get_type_from_node(node1)
        type2 = self.get_type_from_node(node2)
        print(type1, type2)
        if isinstance(type1, PrimitiveType) and isinstance(type2, PrimitiveType):
            print(type1.name, type2.name)
            return type1.name == type2.name
        if isinstance(type1, ArrayType) and isinstance(type2, ArrayType):
            print(type1.base_type, type2.base_type)
            return equals_simple_type(type1.base_type, type2.base_type)
        if isinstance(type1, ClassType) and isinstance(type2, ClassType):
            return type1.name == type2.name
        return type1 == type2
