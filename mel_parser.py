from lark import Lark, Transformer, Token
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
    %ignore DOT
    COMMENT: CPP_COMMENT | C_COMMENT
    %ignore COMMENT

    BOOL: "true" | "false"
    DOT: "."
    literal: NUMBER | ESCAPED_STRING | BOOL
    array_type: CNAME "[" "]"    -> array_type
    type_decl: CNAME | array_type
    type: CNAME | CNAME "[" "]"  -> array_type
    
    ?declaration: "int" CNAME "=" expr ";"
             | "float" CNAME "=" expr ";"
             | "string" CNAME "=" expr ";"

    ?assignment: CNAME "=" expr ";"

    ?group: literal
        | CNAME
        | func_call
        | "(" expr ")"
        | array_index

    ?array_index: CNAME "[" expr "]" -> array_index

    ?mult: group
        | mult "*" group    -> mul
        | mult "/" group    -> div
        | mult "%" group    -> mod

    ?add: mult
        | add "+" mult      -> add
        | add "-" mult      -> sub

    ?compare1: add
        | add ">" add       -> gt
        | add ">=" add      -> ge
        | add "<" add       -> lt
        | add "<=" add      -> le

    ?compare2: compare1
        | compare1 "==" compare1      -> eq
        | compare1 "!=" compare1      -> ne

    ?and: compare2
        | and "&&" compare2

    ?or: and
        | or "||" and

    ?unary: "-" unary      -> neg
        | "!" unary      -> not
        | group

    ?expr: or

    func_call: CNAME "(" (expr ("," expr)*)? ")"
    vars_decl: "var" type_decl var_decl ("," var_decl)*
    param_decl_list: param_decl ("," param_decl)*

    none_stmt:   -> stmt_list
    none_expr: -> empty
    array_assign_stmt: array_access "=" expr ";"
    array_access: expr "[" expr "]"
    array_assign: CNAME "[" expr "]" "=" expr -> array_assign
    array_init: CNAME "=" array -> array_init

    ?var_decl: CNAME
     | CNAME "=" expr     -> assign
     | array_init

    param_decl: type_decl CNAME  -> vars_decl
    func_decl: type_decl CNAME "(" param_decl_list? ")" "{" stmt_list "}"

    array: "{" (expr ("," expr)*)? "}"  -> array

    class_decl: "class" CNAME "{" stmt_list? "}"
    member_access: CNAME DOT CNAME

    ?stmt1: array_assign_stmt
      | array_assign             -> array_assign
      | CNAME "=" expr           -> assign
      | "return" expr            -> return
      | type_decl var_decl       -> typed_decl
      | func_call
      | vars_decl


    ?stmt2: "{" stmt_list "}"
        | "while" "(" expr ")" stmt              -> while
        | "if" "(" expr ")" stmt ("else" stmt)?  -> if
        | "for" "(" (stmt1 | none_stmt) ";" (expr | none_expr) ";" (stmt1 | none_stmt) ")" (stmt | ";" none_stmt)  -> for
        | func_decl
    ?stmt: stmt1 ";" | stmt2

    stmt_list: (stmt ";"*)*

    ?prog: (class_decl | stmt)*

    ?start: prog

''', start="start")

class MelASTBuilder(Transformer):
    def _call_userfunc(self, tree, new_children=None):
        # Assumes tree is already transformed
        children = new_children if new_children is not None else tree.children
        try:
            f = getattr(self, tree.data)
        except AttributeError:
            return self.__default__(tree.data, children, tree.meta)
        else:
            # Печать для отладки:
            print(f"Обработка узла: {tree.data} с аргументами {children}")
            if tree.data == 'array_assign' and isinstance(children[0], ArrayAssignNode):
                return children[0]
            return f(*children)

    def __getattr__(self, item):
        try:
            return super().__getattribute__(item)
        except AttributeError:
            pass
        if isinstance(item, str) and item.upper() == item:
            return lambda x: x

        if item == 'true':
            return lambda *args: LiteralNode('true')

        if item in ('mul', 'div', 'add', 'sub',
                    'gt', 'ge', 'lt', 'le', 'eq', 'ne',
                    'and', 'or'):
            def get_bin_op_node(arg1, arg2):
                op = BinOp[item.upper()]
                return BinOpNode(op, arg1, arg2)
            return get_bin_op_node

        if item == 'assign':
            def get_assign_node(var, val):
                if isinstance(var, Token):
                    var = IdentNode(str(var))
                if isinstance(val, Token):
                    val = IdentNode(str(val))
                return AssignNode(var, val)

            return get_assign_node

        else:
            def get_node(*args):
                cls_name = ''.join(x.capitalize() or '_' for x in item.split('_')) + 'Node'
                if cls_name in globals():
                    cls = globals()[cls_name]
                    if cls == ArrayNode:
                        return cls(tuple(args))
                    if cls == ParamDeclListNode:
                        return cls(list(args))
                    return cls(*args)
                else:
                    raise NameError(f"Класс {cls_name} не определён")
            return get_node

    def array_assign(self, array_name, index_expr, value_expr):
        if isinstance(array_name, Token):
            array_name = IdentNode(str(array_name))
        print(f"Обработка присваивания массива: {array_name}[{index_expr}] = {value_expr}")
        return ArrayAssignNode(array_name, index_expr, value_expr)

    def array_index(self, array_name, index_expr):
        if isinstance(array_name, Token):
            array_name = IdentNode(str(array_name))
        return ArrayIndexNode(array_name, index_expr)

    def array_access(self, array_expr, index_expr):
        return ArrayAccessNode(array_expr, index_expr)

    def array_assign_stmt(self, items):
        return AssignNode(items[0], items[1])

    def array_init(self, name, array):
        if isinstance(name, Token):
            name = IdentNode(str(name))
        return AssignNode(name, array)

    def class_decl(self, name, body=None):
        if body is None:
            body = StmtListNode()
        print(f"Создание класса: {name}, с телом: {body}")
        return ClassDeclNode(name, body)

    def param_decl_list(self, *args):
        return ParamDeclListNode(list(args))

    def param_decl(self, typ, name):
        return VarsDeclNode(typ, [name])

    def typed_decl(self, typ, decl):
        if isinstance(decl, Token):
            decl = IdentNode(str(decl))
        return VarsDeclNode(typ, [decl])

    def func_decl(self, ret_type, name, params=None, body=None):
        if params is None:
            params = ParamDeclListNode([])
        elif isinstance(params, tuple):
            params = ParamDeclListNode(list(params))
        return FuncDeclNode(ret_type, name, params, body)

    def CNAME(self, token: Token):
        print(f"Преобразование CNAME: {token} -> IdentNode")
        return IdentNode(str(token))

    def var_declaration(self, args):
        var_type, name, value = args
        return VarDeclarationNode(var_type, name, value)

    def assignment(self, args):
        name, value = args
        return AssignmentNode(name, value)

    def prog(self, *stmts):
        return StmtListNode(list(stmts))


def parse(prog: str)->StmtListNode:
    prog = parser.parse(str(prog))
    prog = MelASTBuilder().transform(prog)
    return prog
