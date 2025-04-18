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
        if isinstance(value, str) and value.startswith('"'):
            self.value = value[1:-1]
            return
        with suppress(Exception):
            self.value = int(value)
            return
        with suppress(Exception):
            self.value = float(value)
            return
        if value in ('true', 'false'):
            self.value = value == 'true'

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


class TypeDeclNode(AstNode):
    def __init__(self, typename):
        super().__init__()
        if isinstance(typename, ArrayTypeNode):
            self.typename = str(typename)
        else:
            self.typename = typename

    def __repr__(self):
        return f"TypeDeclNode({self.typename})"

    def __str__(self):
        return str(self.typename)

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