from lark import Lark, Transformer, Tree, Token
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
    member_access: THIS "." ident -> member_access
                | ident "." ident -> member_access
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

    array_access: ident "[" expr "]" -> array_access

    ?expr: or
        | array_access
        | member_access
        | "this" DOT ident -> member_access
        | ident
        | "(" expr ")" 
        | new_expr

    func_call: ident "(" (expr ("," expr)*)? ")"

    none_stmt:   -> stmt_list
    none_expr: -> empty


    ?var_decl: ident
        | ident "=" expr     -> assign
        | ident "=" array   -> assign

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

    ?stmt1: expr "=" expr   -> assign  
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
            return self.member_access(*children)

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

    def assign(self, var, val):
        return AssignNode(var, val)

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

    def member_access(self, obj, member):
        # Преобразуем obj в IdentNode, если это токен
        if isinstance(obj, Token):
            if obj.type == 'THIS':
                obj = ThisNode()  # Создаем узел для 'this'
            else:
                obj = IdentNode(str(obj))  # Преобразуем ident в IdentNode

        if isinstance(member, Tree):
            member_name = str(member.children[0])  # Извлекаем имя из Tree
        else:
            member_name = str(member)
        return MemberAccessNode(obj, IdentNode(member_name))


def parse(prog: str) -> StmtListNode:
    prog = parser.parse(str(prog))
    prog = MelASTBuilder().transform(prog)
    return prog


class MelTransformer(Transformer):
    def return_stmt(self, *args):
        if args:
            return ReturnNode(args[0])
        return ReturnNode(EmptyNode())  # Передаём пустой узел
