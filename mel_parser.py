from lark import Lark, Transformer
from mel_ast import *

parser = Lark('''
    %import common.NUMBER
    %import common.CNAME
    %import common.NEWLINE
    %import common.WS
    %import common.CPP_COMMENT
    %import common.C_COMMENT
    %import common.ESCAPED_STRING

    %ignore WS
    COMMENT: CPP_COMMENT | C_COMMENT
    %ignore COMMENT

    BOOL: "true" | "false"
    literal: NUMBER | ESCAPED_STRING | BOOL
    ident: CNAME | /[a-zA-Z_][a-zA-Z0-9_]*/
    DOT: "."
    %ignore DOT

    array_type: ident "[" "]" -> array_type
    type_decl: CNAME | array_type | type ident "=" expr
    type: ident | ident "[" "]" -> array_type
    member_access: THIS DOT ident -> member_access
                 | ident DOT ident -> member_access
    THIS: "this"

    
    new_expr: "new" ident ("[" expr "]")+ -> new_array
        | "new" ident "(" (expr ("," expr)*)? ")" -> new_object
        
        
    group: literal
          | ident
          | func_call
          | member_access
          | "(" expr ")"

    ?mult: group
        | mult "*" group  -> mul
        | mult "/" group  -> div
        | mult "%" group  -> mod

    ?add: mult
     | add "+" mult   -> add
     | add "-" mult   -> sub
        
    ?inc_dec: ident "++" -> inc
        | ident "--" -> dec
        | add "+" mult -> add
        | add "-" mult -> sub

    ?compare1: add
        | add ">" add     -> gt
        | add ">=" add    -> ge
        | add "<" add     -> lt
        | add "<=" add    -> le

    ?compare2: compare1
        | compare1 "==" compare1  -> eq
        | compare1 "!=" compare1  -> ne

    ?and: compare2
        | and "&&" compare2

    ?or: and
        | or "||" and

    ?unary: "-" unary      -> neg
        | "!" unary      -> not
        | group

    ?expr: or
    | member_access
    | "this" DOT ident -> member_access
    | ident
    | "(" expr ")" 
    | new_expr

    func_call: ident "(" (expr ("," expr)*)? ")"

    none_stmt:   -> stmt_list
    none_expr: -> empty
    array_assign: ident "[" expr "]" "=" expr -> array_assign
            | ident "=" array -> array_init

    ?var_decl: ident
        | ident "=" expr     -> assign
        | ident "=" array   -> array_init
        | ident "[" expr "]" "=" expr -> array_assign
    vars_decl: type_decl var_decl ("," var_decl)*
    

    param_decl: type_decl ident  -> vars_decl
    func_decl: type_decl ident "(" (param_decl ("," param_decl)*)? ")" "{" stmt_list "}"

    array: "{" (expr ("," expr)*)? "}"  -> array
    class_decl : "class" ident "{" (constructor_decl | stmt)* "}"
    constructor_decl: "constructor" "(" param_decl? ")" "{" stmt_list "}"

    func_access: ident DOT ident -> func_access 

    return_stmt: "return" ";"  -> return_stmt
    if_stmt: "if" "(" expr ")" stmt ("else" stmt)? -> if_stmt
    while_stmt: "while" "(" expr ")" stmt -> while_stmt
    for_stmt: "for" "(" (stmt1 | none_stmt) ";" (expr | none_expr) ";" (stmt1 | none_stmt) ")" stmt -> for_stmt
    
    new_array_init: "new" ident "[" expr "]" "{" (expr ("," expr)*)? "}" -> new_array_init

    ?stmt1: ident "=" expr   -> assign
        | "return" expr      -> return
        | var_decl
        | if_stmt
        | while_stmt
        | for_stmt
        | stmt_list
        | func_call
        | vars_decl

    ?stmt2: "{" stmt_list "}"
        | "while" "(" expr ")" stmt              -> while
        | "if" "(" expr ")" stmt ("else" stmt)?  -> if
        | "for" "(" (stmt1 | none_stmt) ";" (expr | none_expr) ";" (stmt1 | none_stmt) ")" (stmt | ";" none_stmt)  -> for
        | func_decl

    ?stmt: return_stmt | stmt1 ";" | stmt2 

    stmt_list: (stmt ";"*)* | stmt*
    ?prog: stmt_list | class_decl

    ?start: prog |
''', start="start")

'''
class MelASTBuilder(Transformer):
    def return_stmt(self, _):
        return ReturnNode(EmptyNode())

    def literal(self, arg: str) -> LiteralNode:
        return LiteralNode(arg)

    def assign(self, ident: IdentNode, expr: ExprNode) -> AssignNode:
        return AssignNode(ident, expr)

    def while_stmt(self, cond: ExprNode, body: StmtNode) -> WhileNode:
        return WhileNode(cond, body)

    def add(self, arg1: ExprNode, arg2: ExprNode) -> ExprNode:
        return BinOpNode(BinOp.ADD, arg1, arg2)
        
    def mod(self, arg1: ExprNode, arg2: ExprNode) -> ExprNode:
        return BinOpNode(BinOp.MOD, arg1, arg2)

    def sub(self, arg1: ExprNode, arg2: ExprNode) -> ExprNode:
        return BinOpNode(BinOp.SUB, arg1, arg2)

    def neg(self, arg: ExprNode) -> ExprNode:
        return UnaryOpNode(UnaryOp.NEG, arg)

    def not_op(self, arg: ExprNode) -> ExprNode:
        return UnaryOpNode(UnaryOp.NOT, arg)

    def empty(self) -> EmptyNode:
        return EmptyNode()

    def array(self, *elements):
        return ArrayNode(tuple(elements))

    def class_decl(self, name: IdentNode, *members):
        body = StmtListNode(list(members))
        print(f"Создание класса: {name}, с членами: {body}")
        return ClassDeclNode(name, body)

    def constructor_decl(self, params=None, body=None):
        if params is None:
            params = []
        if body is None:
            body = StmtListNode([])
        return ConstructorDeclNode(params, body)

    def member_access(self, obj, member):
    # Проверяем, является ли obj (левая часть) "this"
    if isinstance(obj, str) and obj == "this":
        return MemberAccessNode(obj, member)
    else:
        # Прочие случаи для member_access
        if not isinstance(obj, ExprNode):
            raise TypeError(f"obj must be an instance of ExprNode, got {type(obj)}")
        if not isinstance(member, IdentNode):
            raise TypeError(f"member must be an instance of IdentNode, got {type(member)}")
        return MemberAccessNode(obj, member)

    def func_access(self, obj, method):
        return FuncAccessNode(obj, method)

    def array_assign(self, array, index, value):
        return ArrayAssignNode(array, index, value)

    def array_init(self, ident, array):
        return ArrayAssignNode(ident, array)
    
    def array_type(self, name):
        return ArrayTypeNode(name)

    def method_decl(self, return_type, name, params=None, body=None):
        if params is None:
            params = []
        if body is None:
            body = StmtListNode([])
        print(f"Создание метода: {name}, с параметрами: {params}, с телом: {body}")
        return MethodDeclNode(return_type, name, params, body)

    def new_expr(self, class_name, *args):
        return NewExprNode(class_name, list(args))
        
    def func_decl(self, return_type, name, params=None, body=None):
        if params is None:
            params = []
        if body is None:
            body = StmtListNode()
        return FuncDeclNode(return_type, name, params, body)

    def func_call(self, name, *args):
        return FuncCallNode(name, args)

    def ident(self, name):
        if name == "this":
            return IdentNode("this")
        return IdentNode(name)
        
    
    def new_array(self, type_name, *dimensions):
        # Обрабатываем многомерные массивы
        current_node = NewArrayNode(type_name, dimensions[-1])
        for dim in reversed(dimensions[:-1]):
            current_node = NewArrayNode(type_name, dim)
            # Здесь нужно адаптировать для поддержки многомерных массивов
        return current_node
        
    def new_object(self, class_name, *args):
        return NewObjectNode(class_name, args)
        
    def new_array_init(self, type_name, size, *elements):
        return NewArrayInitNode(type_name, size, elements)
        


'''


class MelASTBuilder(Transformer):
    def method_decl(self, return_type, name, params=None, body=None):
        if params is None:
            params = []
        if body is None:
            body = StmtListNode()
        print(f"Создание метода: {name}, с параметрами: {params}, с телом: {body}")
        return MethodDeclNode(return_type, name, params, body)

    def func_decl(self, return_type, name, params=None, body=None):
        if params is None:
            params = []
        if body is None:
            body = StmtListNode()
        print(f"Создание функции: {name}, с параметрами: {params}, с телом: {body}")
        return FuncDeclNode(return_type, name, params, body)

    def _call_userfunc(self, tree, new_children=None):
        children = new_children if new_children is not None else tree.children

        # Обработка member_access
        if tree.data == 'member_access':
            print(f"Обработка узла: {tree.data} с аргументами {tree.children}")
            obj, member = children
            print(f"Обработка member_access: объект {obj} и член {member}")
            return MemberAccessNode(obj, member)

        # Обработка других типов узлов
        try:
            f = getattr(self, tree.data, None)
            if f is None:
                return self.__default__(tree.data, children, tree.meta)
        except AttributeError:
            print(f"Ошибка: метод {tree.data} не найден в {self.__class__.__name__}")
            return self.__default__(tree.data, children, tree.meta)
        else:
            print(f"Обработка узла: {tree.data} с аргументами {children}")
            return f(*children)

    def __getattr__(self, item):
        if item.upper() == item:
            return lambda x: x

        # Обработка простых операций (mul, div и др.)
        if item in ('mul', 'div', 'add', 'sub', 'gt', 'ge', 'lt', 'le', 'eq', 'ne', 'and', 'or', 'mod'):
            def get_bin_op_node(arg1, arg2):
                op = BinOp[item.upper()]
                return BinOpNode(op, arg1, arg2)

            return get_bin_op_node

        # Обработка специальных случаев
        if item == 'assign':
            return lambda var, val: AssignNode(var, val)

        if item in ('array_assign', 'array_init'):
            # Оба случая используют ArrayAssignNode
            if item == 'array_assign':
                return lambda array, index, value: ArrayAssignNode(array, index, value)
            else:
                return lambda ident, array: ArrayAssignNode(ident, array)

        # Динамическое создание узлов
        def get_node(*args):
            cls_name = ''.join(x.capitalize() for x in item.split('_')) + 'Node'

            # Специальные случаи именования
            if cls_name == "ReturnStmtNode":
                cls_name = "ReturnNode"

            try:
                cls = eval(cls_name)
            except NameError:
                raise NameError(
                    f"Node class {cls_name} not defined. Did you mean: {[n for n in globals() if 'Node' in n]}")

            # Специальная обработка некоторых классов
            if cls == ArrayNode:
                return cls(tuple(args))
            if cls == ReturnNode:
                return ReturnNode(args[0] if args else None)

            return cls(*args)

        return get_node
    def class_decl(self, name, *members):
        print(f"Создание класса: {name}, с членами: {members}")
        body = StmtListNode(list(members))
        return ClassDeclNode(name, body)


def parse(prog: str) -> StmtListNode:
    prog = parser.parse(str(prog))
    prog = MelASTBuilder().transform(prog)
    return prog


class MelTransformer(Transformer):
    def return_stmt(self, *args):
        if args:
            return ReturnNode(args[0])
        return ReturnNode(EmptyNode())  # Передаём пустой узел


