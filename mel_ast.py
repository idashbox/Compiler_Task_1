from abc import ABC, abstractmethod
from contextlib import suppress
from typing import Callable, Tuple, Any, Optional, Union, List
from enum import Enum

class AstNode(ABC):
    @property
    def children(self) -> Tuple['AstNode', ...]:
        return ()

    @abstractmethod
    def __str__(self) -> str:
        pass

    @property
    def tree(self) -> Tuple[str, ...]:
        res = [str(self)]
        children = self.children
        for i, child in enumerate(children):
            ch0, ch = '├', '│'
            if i == len(children) - 1:
                ch0, ch = '└', ' '

            if isinstance(child, list):
                for k, sub in enumerate(child):
                    res.extend(((ch0 if k == 0 else ch) + ' ' + s for j, s in enumerate(sub.tree)))
            else:
                res.extend(((ch0 if j == 0 else ch) + ' ' + s for j, s in enumerate(child.tree)))
        return tuple(res)

    def visit(self, func: Callable[['AstNode'], None]) -> None:
        func(self)
        for child in self.children:
            child.visit(func)

    def get_type(self):  # в LiteralNode
        return self.type

    def __getitem__(self, index):
        return self.children[index] if index < len(self.children) else None


class ExprNode(AstNode):
    pass


class StmtNode(AstNode):
    pass


class LiteralNode(ExprNode):
    def __init__(self, value: Any):
        super().__init__()
        self.value = value

        if isinstance(value, int):
            self.type = INT
        elif isinstance(value, float):
            self.type = FLOAT
        elif isinstance(value, bool):
            self.type = BOOL
        elif isinstance(value, str):
            if value in ('true', 'false'):
                self.type = BOOL
                self.value = value == 'true'
            else:
                self.type = STRING
        else:
            self.type = None

        if isinstance(value, str) and value.startswith('"'):
            self.value = value[1:-1]
            return

        with suppress(Exception):
            self.value = int(value)
            return

        with suppress(Exception):
            self.value = float(value)
            return

    def __str__(self) -> str:
        if isinstance(self.value, bool):
            return str(self.value).lower()
        if isinstance(self.value, str):
            return f'"{self.value}"'
        return str(self.value)



class IdentNode(ExprNode):
    def __init__(self, name: str):
        super().__init__()
        self.name = str(name)

    def __str__(self) -> str:
        return str(self.name)


class BinOp(Enum):
    ADD = '+'
    SUB = '-'
    MUL = '*'
    DIV = '/'
    MOD = '%'
    GT = '>'
    GE = '>='
    LT = '<'
    LE = '<='
    EQ = '=='
    NE = '!='
    BIT_AND = '&'
    BIN_OR = '|'
    AND = '&&'
    OR = '||'


class UnaryOp(Enum):
    NEG = '-'
    NOT = '!'


class UnaryOpNode(ExprNode):
    def __init__(self, op: UnaryOp, arg: ExprNode):
        super().__init__()
        self.op = op
        self.arg = arg

    @property
    def children(self) -> Tuple[ExprNode]:
        return (self.arg,)

    def __str__(self) -> str:
        return self.op.value


class BoolOpNode(ExprNode):
    def __init__(self, op: BinOp, arg1: ExprNode, arg2: ExprNode):
        super().__init__()
        self.op = op
        self.arg1 = arg1
        self.arg2 = arg2

    @property
    def children(self) -> Tuple[ExprNode, ExprNode]:
        return self.arg1, self.arg2

    def __str__(self) -> str:
        return str(self.op.value)


class EmptyNode(ExprNode):
    def __str__(self):
        return "empty"


class ArrayNode(ExprNode):
    def __init__(self, elements: Tuple[ExprNode, ...]):
        super().__init__()
        self.elements = elements

    @property
    def children(self) -> Tuple[ExprNode, ...]:
        return self.elements

    def __str__(self) -> str:
        return 'array'


class ClassDeclNode(StmtNode):
    def __init__(self, name: IdentNode, body: StmtNode):
        super().__init__()
        self.name = name
        self.body = body

    @property
    def children(self) -> Tuple[StmtNode]:
        return (self.body,)

    def __str__(self) -> str:
        return f'class {self.name}'


class MemberAccessNode(ExprNode):
    def __init__(self, obj: ExprNode, member: IdentNode):
        super().__init__()
        self.obj = obj
        self.member = member

    @property
    def children(self) -> Tuple[ExprNode, IdentNode]:
        return self.obj, self.member

    def __str__(self) -> str:
        return f'{self.obj}.{self.member}'


class BinOpNode(ExprNode):
    def __init__(self, op: BinOp, arg1: ExprNode, arg2: ExprNode):
        super().__init__()
        self.op = op
        self.arg1 = arg1
        self.arg2 = arg2

    @property
    def children(self) -> Tuple[ExprNode, ExprNode]:
        return self.arg1, self.arg2

    def __str__(self) -> str:
        return str(self.op.value)


class FuncCallNode(ExprNode):
    def __init__(self, func: IdentNode, *params: ExprNode):
        super().__init__()
        self.func = func
        self.params = params

    @property
    def children(self) -> Tuple[ExprNode, ...]:
        return (self.func,) + self.params

    def __str__(self) -> str:
        return f'{self.func}()'


class AssignNode(StmtNode):
    def __init__(self, var: IdentNode, val: ExprNode):
        super().__init__()
        self.var = var
        self.val = val

    @property
    def children(self) -> Tuple[IdentNode, ExprNode]:
        return self.var, self.val

    def __str__(self) -> str:
        return '='


class WhileNode(StmtNode):
    def __init__(self, cond: ExprNode, body: StmtNode):
        super().__init__()
        self.cond = cond
        self.body = body

    @property
    def children(self) -> Tuple[ExprNode, StmtNode]:
        return self.cond, self.body

    def __str__(self) -> str:
        return 'while'


class IfNode(StmtNode):
    def __init__(self, cond: ExprNode, then_stmt: StmtNode, else_stmt: Optional[StmtNode] = None):
        super().__init__()
        self.cond = cond
        self.then_stmt = then_stmt
        self.else_stmt = else_stmt

    @property
    def children(self) -> Tuple[ExprNode, StmtNode]:
        return (self.cond, self.then_stmt) + ((self.else_stmt, ) if self.else_stmt else tuple())

    def __str__(self) -> str:
        return 'if'


class ForNode(StmtNode):
    def __init__(self, init: StmtNode, cond: ExprNode, step: StmtNode, body: StmtNode):
        super().__init__()
        self.init = init
        self.cond = cond
        self.step = step
        self.body = body

    @property
    def children(self) -> Tuple[StmtNode, ExprNode, StmtNode, StmtNode]:
        return self.init, self.cond, self.step, self.body

    def __str__(self) -> str:
        return 'for'


class StmtListNode(StmtNode):
    def __init__(self, *stmts: AstNode):
        super().__init__()
        self.stmts = stmts

    @property
    def children(self) -> Tuple[AstNode, ...]:
        return self.stmts

    def __str__(self) -> str:
        return '...'


class ArrayInitNode(StmtNode):
    def __init__(self, name: IdentNode, array: ArrayNode):
        self.name = name
        self.array = array

    def __repr__(self):
        return f"ArrayInitNode(name={self.name}, array={self.array})"

    def __str__(self):
        return f'init {self.name}'


class ArrayAssignNode(StmtNode):
    def __init__(self, ident, index, value):
        self.ident = ident
        self.index = index
        self.value = value

    @property
    def children(self) -> Tuple[AstNode, ...]:
        return (self.ident, self.value)

    def __str__(self):
        return '='


class ArrayIndexNode(AstNode):
    def __init__(self, array: AstNode, index: AstNode):
        self.array = array
        self.index = index

    @property
    def children(self) -> Tuple[AstNode, ...]:
        return (self.array, self.index)

    def __str__(self):
        return '[]'


class ArrayAccessNode(AstNode):
    def __init__(self, array_expr, index_expr):
        self.array_expr = array_expr
        self.index_expr = index_expr

    def _str(self, level=0):
        indent = "│ " * level
        s = f"{indent}├ []\n"
        s += self.array_expr._str(level + 1)
        s += self.index_expr._str(level + 1)
        return s

class ArrayElementAssignNode(AstNode):
    def __init__(self, array: AstNode, index: AstNode, value: AstNode):
        self.array = array
        self.index = index
        self.value = value

    def children(self) -> Tuple[AstNode, ...]:
        return (ArrayIndexNode(self.array, self.index), self.value)

    def __str__(self):
        return '='


class PrimitiveType:
    def __init__(self, name):
        self.name = name

    def __repr__(self):
        return self.name


PRIMITIVE_TYPES = {"int", "float", "bool", "string"}

class TypeDeclNode(AstNode):
    def __init__(self, typename):
        super().__init__()
        if isinstance(typename, IdentNode):
            name = typename.name
            if name in PRIMITIVE_TYPES:
                self.type = PrimitiveType(name)
                self.typename = name
            else:
                self.type = typename
                self.typename = name
        elif isinstance(typename.name, ArrayTypeNode):
            self.type = ArrayTypeNode(typename.name)
            self.typename = str(typename)
        else:
            self.type = typename
            self.typename = str(typename)

    def __repr__(self):
        return f"TypeDeclNode({self.typename})"

    def __str__(self):
        return str(self.typename)

class TypedDeclNode(StmtNode):
    def __init__(self, type_decl, assign_node):
        self.type_decl = type_decl  # TypeDeclNode
        self.assign_node = assign_node  # AssignNode

    def __repr__(self):
        var_name = self.assign_node.ident.name if isinstance(self.assign_node, AssignNode) else "?"
        return f"TypedDeclNode({self.type_decl} {var_name})"

class VarDeclarationNode(AstNode):
    def __init__(self, var_type, name, value=None):
        self.var_type = var_type
        self.name = name
        self.value = value


class AssignmentNode(AstNode):
    def __init__(self, var_name, value):
        self.var_name = var_name
        self.value = value

class ArrayTypeNode:
    def __init__(self, name):
        self.name = name

    def __str__(self):
        return f"Array of {self.name}"


class VarsDeclNode(StmtNode):
    def __init__(self, type_node: 'TypeDeclNode', *vars: IdentNode):
        super().__init__()
        self.type = type_node
        self.vars = list(vars)  # исправим на list

    @property
    def children(self) -> Tuple[AstNode, ...]:
        return (self.type,) + tuple(self.vars)

    def __str__(self) -> str:
        return f'var ({str(self.type)})'


class ParamDeclListNode(AstNode):
    def __init__(self, vars: list[VarsDeclNode]):
        self._vars = vars

    def __repr__(self):
        return f"ParamDeclListNode({self._vars})"

    @property
    def vars(self):
        return self._vars

    @property
    def children(self) -> Tuple[AstNode, ...]:
        return tuple(self._vars)

    @property
    def tree(self):
        res = [f"ParamDeclList:"]
        for param in self._vars:
            for line in param.tree:
                res.append("  " + line)
        return res

    def __str__(self):
        return f"param_decl_list ({len(self._vars)} param(s))"


class FuncDeclNode(StmtNode):
    def __init__(self, return_type: 'TypeDeclNode', name: IdentNode, params: 'ParamDeclListNode', body: 'StmtListNode'):
        super().__init__()
        self.return_type = return_type
        self.name = name
        self.params = params
        self.body = body

    @property
    def children(self) -> Tuple[AstNode, ...]:
        return (self.return_type, self.name, self.params, self.body)

    def __str__(self) -> str:
        return f'func {self.name}'



class ReturnNode(StmtNode):
    def __init__(self, result: ExprNode):
        super().__init__()
        self.result = result

    @property
    def children(self) -> Tuple[AstNode]:
        return self.result,

    def __str__(self) -> str:
        return 'return'


class Type:
    """Базовый класс всех типов."""

    def __eq__(self, other):
        return equals_simple(self, other)

    def __str__(self):
        return self.__class__.__name__

    def __repr__(self):
        return str(self)


class PrimitiveType(Type):
    def __init__(self, name: str):
        self.name = name

    def __eq__(self, other):
        return isinstance(other, PrimitiveType) and self.name == other.name

    def __repr__(self):
        return self.name

    def __str__(self):
        return self.name


INT = PrimitiveType("int")
FLOAT = PrimitiveType("float")
STRING = PrimitiveType("string")
BOOL = PrimitiveType("bool")


def equals_simple(node1: AstNode, node2: AstNode) -> bool:
    type1 = get_type_from_node(node1)
    type2 = get_type_from_node(node2)
    print(type1, type2)  # Добавьте эту строку для отладки

    # Примитивные типы
    if isinstance(type1, PrimitiveType) and isinstance(type2, PrimitiveType):
        print(type1.name, type2.name)
        return type1.name == type2.name

    # Массивы
    if isinstance(type1, ArrayType) and isinstance(type2, ArrayType):
        print(type1.base_type, type2.base_type)
        return equals_simple_type(type1.base_type, type2.base_type)

    # Классы
    if isinstance(type1, ClassType) and isinstance(type2, ClassType):
        return type1.name == type2.name

    return False


class ArrayType(Type):
    def __init__(self, base_type: Type):
        self.base_type = base_type

    def __eq__(self, other):
        return isinstance(other, ArrayType) and self.base_type == other.base_type

    def __repr__(self):
        return f"{self.base_type}[]"

    def __str__(self):
        return f"{self.base_type}[]"


class ClassType(Type):
    def __init__(self, name: str):
        self.name = name

    def __eq__(self, other):
        return isinstance(other, ClassType) and self.name == other.name

    def __repr__(self):
        return f"class {self.name}"

    def __str__(self):
        return f"{self.name}"



def get_type_from_node(node):
    if isinstance(node, LiteralNode):
        return node.get_type()

    elif isinstance(node, IdentNode):
        # Идентификатор — определим его тип из текущей области видимости семантического анализатора
        # Здесь временно вернём None и пусть вызывающий обработает lookup
        return None  # пусть SemAnalyzer сам lookup'ает

    elif isinstance(node, ArrayNode):
        if node.elements:
            element_type = get_type_from_node(node.elements[0])
            return ArrayType(element_type)
        else:
            return ArrayType(PrimitiveType("int"))  # пустой массив по умолчанию

    elif isinstance(node, AssignNode):
        return get_type_from_node(node.val)

    elif isinstance(node, FuncCallNode):
        # Функция возвращает тип, нужно будет получать return_type из объявления
        # Оставим пока как None, можно доработать позже
        return None

    elif isinstance(node, VarsDeclNode):
        return get_type_from_typename(node.type.typename)

    elif isinstance(node, TypeDeclNode):
        return get_type_from_typename(node.typename)

    elif isinstance(node, ArrayTypeNode):
        return ArrayType(get_type_from_typename(node.name))

    elif isinstance(node, MemberAccessNode):
        # Нужно будет смотреть в класс по имени объекта
        return None  # пока не определить

    return None


def get_type_from_typename(typename: str) -> Type:
    """Преобразует имя типа в объект Type."""
    if typename == "int":
        return INT
    elif typename == "float":
        return FLOAT
    elif typename == "string":
        return STRING
    elif typename == "bool":
        return BOOL
    else:
        # Предполагаем, что это имя класса
        return ClassType(typename)



def equals_simple_type(type1: Type, type2: Type) -> bool:
    """Сравнивает непосредственно объекты типов."""
    return type1 == type2