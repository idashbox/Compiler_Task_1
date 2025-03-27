from abc import ABC, abstractmethod
from contextlib import suppress
from typing import Callable, Tuple, Any, Optional, Union
from enum import Enum


class AstNode(ABC):
    @property
    def childs(self) -> Tuple['AstNode', ...]:
        return ()

    @abstractmethod
    def __str__(self) -> str:
        pass

    @property
    def tree(self) -> [str, ...]:
        res = [str(self)]
        childs = self.childs
        for i, child in enumerate(childs):
            ch0, ch = '├', '│'
            if i == len(childs) - 1:
                ch0, ch = '└', ' '

            # Проверка на None
            if child is not None:
                # Если child является списком, обработаем каждый элемент в нем
                if isinstance(child, list):
                    for subchild in child:
                        if subchild is not None:
                            res.extend(((ch0 if j == 0 else ch) + ' ' + s for j, s in enumerate(subchild.tree)))
                else:
                    res.extend(((ch0 if j == 0 else ch) + ' ' + s for j, s in enumerate(child.tree)))

        return res

    def visit(self, func: Callable[['AstNode'], None]) -> None:
        func(self)
        map(func, self.childs)

    def __getitem__(self, index):
        return self.childs[index] if index < len(self.childs) else None


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
    def childs(self) -> Tuple[ExprNode]:
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
    def childs(self) -> Tuple[ExprNode, ExprNode]:
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
    def childs(self) -> Tuple[ExprNode, ...]:
        return self.elements

    def __str__(self) -> str:
        return 'array'


class ConstructorDeclNode(StmtNode):
    def __init__(self, params: list, body: StmtNode):
        super().__init__()
        self.params = params
        self.body = body

    @property
    def childs(self) -> Tuple[StmtNode]:
        return (self.body,)

    def __str__(self) -> str:
        return 'constructor(...)'


class ClassDeclNode(StmtNode):
    def __init__(self, name: IdentNode, body: StmtNode, constructors: Optional[list] = None):
        super().__init__()
        self.name = name
        self.body = body
        self.constructors = constructors if constructors else []

    @property
    def childs(self) -> Tuple[StmtNode]:
        return (self.body,) + tuple(self.constructors)

    def __str__(self) -> str:
        return f'class {self.name}'


class ThisNode(ExprNode):
    def __str__(self) -> str:
        return "this"


class MemberAccessNode(ExprNode):
    def __init__(self, obj: ExprNode, member: IdentNode):
        super().__init__()
        if not isinstance(obj, ExprNode):
            raise TypeError(f"obj must be an instance of ExprNode, got {type(obj)}")
        if not isinstance(member, IdentNode):
            raise TypeError(f"member must be an instance of IdentNode, got {type(member)}")
        self.obj = obj
        self.member = member

    @property
    def childs(self) -> Tuple[ExprNode, IdentNode]:
        return self.obj, self.member

    def __str__(self) -> str:
        return f'{self.obj}.{self.member}'


class GroupNode(AstNode):
    def __init__(self, value):
        self.value = value

    def __str__(self):
        return f"GroupNode({self.value})"

class BinOpNode(ExprNode):
    def __init__(self, op: BinOp, arg1: ExprNode, arg2: ExprNode):
        super().__init__()
        self.op = op
        self.arg1 = arg1
        self.arg2 = arg2

    @property
    def childs(self) -> Tuple[ExprNode, ExprNode]:
        return self.arg1, self.arg2

    def __str__(self) -> str:
        return str(self.op.value)


class FuncCallNode(ExprNode):
    def __init__(self, func: IdentNode, *params: ExprNode):
        super().__init__()
        self.func = func
        self.params = params

    @property
    def childs(self) -> Tuple[ExprNode]:
        return self.params

    def __str__(self) -> str:
        return f'{self.func}()'


class AssignNode(StmtNode):
    def __init__(self, var: IdentNode, val: ExprNode):
        super().__init__()
        self.var = var
        self.val = val

    @property
    def childs(self) -> Tuple[IdentNode, ExprNode]:
        return self.var, self.val

    def __str__(self) -> str:
        return '='


class WhileNode(StmtNode):
    def __init__(self, cond: ExprNode, body: StmtNode):
        super().__init__()
        self.cond = cond
        self.body = body

    @property
    def childs(self) -> Tuple[ExprNode, StmtNode]:
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
    def childs(self) -> Tuple[ExprNode, StmtNode]:
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
    def childs(self) -> Tuple[StmtNode, ExprNode, StmtNode, StmtNode]:
        return self.init, self.cond, self.step, self.body

    def __str__(self) -> str:
        return 'for'


class StmtListNode(StmtNode):
    def __init__(self, *stmts: AstNode):
        super().__init__()
        self.stmts = stmts

    @property
    def childs(self) -> Tuple[AstNode]:
        return self.stmts

    def __str__(self) -> str:
        return '...'


class ArrayAssignNode(StmtNode):
    def __init__(self, ident, array):
        super().__init__()
        self.ident = ident
        self.array = array

    @property
    def childs(self) -> Tuple[AstNode, ...]:
        return (self.ident, self.array)

    def __str__(self):
        return f"{self.ident} = {self.array}"

    @property
    def tree(self) -> [str, ...]:
        res = [str(self)]
        childs = self.childs
        for i, child in enumerate(childs):
            ch0, ch = '├', '│'
            if i == len(childs) - 1:
                ch0, ch = '└', ' '
            res.extend(((ch0 if j == 0 else ch) + ' ' + s for j, s in enumerate(child.tree)))
        return res


class TypeDeclNode:
    def __init__(self, typename):
        if isinstance(typename, ArrayTypeNode):
            self.typename = str(typename)
        else:
            self.typename = typename

    def __repr__(self):
        return f"TypeDeclNode({self.typename})"

    def __str__(self):
        return self.typename


class ArrayTypeNode:
    def __init__(self, name):
        self.name = name

    def __str__(self):
        return f"Array of {self.name}"


class VarsDeclNode(StmtNode):
    def __init__(self, type: IdentNode, *vars: Union[IdentNode, AssignNode]):
        super().__init__()
        self.type = type
        self.vars = vars

    @property
    def childs(self) -> Tuple[AstNode]:
        return self.vars

    def __str__(self) -> str:
        return f'var ({str(self.type)})'

class FuncDeclNode(StmtNode):
    def __init__(self, type: IdentNode, name: IdentNode, *params_and_body: VarsDeclNode):
        super().__init__()
        self.type = type
        self.name = name
        self.params = params_and_body[:-1]
        self.body = params_and_body[-1]

    @property
    def childs(self) -> Tuple[AstNode]:
        return *self.params, self.body

    def __str__(self) -> str:
        return f'{self.type} {self.name} (...)'


class ReturnNode(StmtNode):
    def __init__(self, result: ExprNode):
        super().__init__()
        self.result = result

    @property
    def childs(self) -> Tuple[AstNode]:
        return self.result,

    def __str__(self) -> str:
        return 'return'

class MethodDeclNode(StmtNode):
    def __init__(self, return_type: IdentNode, name: IdentNode, params: list, body: StmtNode):
        super().__init__()
        self.return_type = return_type
        self.name = name
        self.params = params
        self.body = body

    @property
    def childs(self) -> Tuple[StmtNode]:
        return (self.body,)

    def __str__(self) -> str:
        return f'method {self.name} returns {self.return_type}'
