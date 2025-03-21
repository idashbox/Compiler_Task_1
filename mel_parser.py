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
    array_type: ident "[" "]"    -> array_type
    type_decl: CNAME | array_type | type ident "=" expr
    type: ident | ident "[" "]"  -> array_type
    
    ?group: literal
        | ident
        | func_call
        | "(" expr ")"
    
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
    
    func_call: ident "(" (expr ("," expr)*)? ")"
    
    none_stmt:   -> stmt_list
    none_expr: -> empty
    array_assign: ident "[" expr "]" "=" expr -> array_assign
    
    ?var_decl: ident
        | ident "=" expr     -> assign
        | ident "=" array   -> array_assign
    vars_decl: type_decl var_decl ("," var_decl)*
    
    param_decl: type_decl ident  -> vars_decl
    func_decl: type_decl ident "(" (param_decl ("," param_decl)*)? ")" "{" stmt_list "}"
    
    array: "{" (expr ("," expr)*)? "}"  -> array
    
    class_decl: "class" ident "{" stmt_list? "}"
    member_access: ident "." ident
    
    ?stmt1: ident "=" expr   -> assign
        | "return" expr      -> return
        | func_call
        | vars_decl
    ?stmt2: "{" stmt_list "}"
        | "while" "(" expr ")" stmt              -> while
        | "if" "(" expr ")" stmt ("else" stmt)?  -> if
        | "for" "(" (stmt1 | none_stmt) ";" (expr | none_expr) ";" (stmt1 | none_stmt) ")" (stmt | ";" none_stmt)  -> for
        | func_decl
    ?stmt: stmt1 ";" | stmt2
    
    stmt_list: (stmt ";"*)*
    
    ?prog: stmt_list | class_decl
    
    ?start: prog

''', start="start")

'''
class MelASTBuilder0(Transformer):
    def literal(self, arg: str) -> LiteralNode:
        return LiteralNode(arg)

    def assign(self, ident: IdentNode, expr: ExprNode) -> AssignNode:
        return AssignNode(ident, expr)

    def while(self, cond: IdentNode, body: StmtNode) -> WhileNode:
        return WhileNode(cond, body)

    def add(self, arg1: ExprNode, arg2: ExprNode) -> ExprNode:
        return BinOpNode(BinOp.ADD, arg1, arg2)

    def sub(self, arg1: ExprNode, arg2: ExprNode) -> ExprNode:
        return BinOpNode(BinOp.SUB, arg1, arg2)
        
    def neg(self, arg: ExprNode) -> ExprNode:
        return UnaryOpNode(UnaryOp.NEG, arg)

    def not(self, arg: ExprNode) -> ExprNode:
        return UnaryOpNode(UnaryOp.NOT, arg)
        
    def empty(self) -> EmptyNode:
        return EmptyNode()
    
    def array(self, *elements):
        return ArrayNode(tuple(elements))
        
    def class_decl(self, name: IdentNode, body=None):
    if body is None:
        body = StmtListNode([])
    print(f"Создание класса: {name}, с телом: {body}")
    return ClassDeclNode(name, body)

    def member_access(self, obj, member):
        return MemberAccessNode(obj, member)

    def array_assign(self, array, index):
        return ArrayAssignNode(array, index)

    def array_type(self, name):
        return ArrayTypeNode(name)

    def literal(self, value):
        return LiteralNode(value)

    def ident(self, name):
        return IdentNode(name)


'''


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
            return f(*children)

    def __getattr__(self, item):
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

        # Обработка присваивания
        if item == 'assign':
            def get_assign_node(var, val):
                return AssignNode(var, val)
            return get_assign_node

        # Обработка присваивания для массивов
        if item == 'array_assign':
            def get_array_assign_node(array, index):
                # Убедитесь, что передаете все три аргумента
                print(f"Обработка присваивания для массива: array={array}, index={index}")
                return ArrayAssignNode(array, index)

            return get_array_assign_node

        # Обработка других типов узлов
        else:
            def get_node(*args):
                cls = eval(''.join(x.capitalize() or '_' for x in item.split('_')) + 'Node')
                if cls == ArrayNode:
                    return cls(tuple(args))  # Передаем аргументы как кортеж
                return cls(*args)
            return get_node

    def class_decl(self, name, body=None):
        if body is None:
            body = StmtListNode()
        print(f"Создание класса: {name}, с телом: {body}")
        return ClassDeclNode(name, body)


def parse(prog: str)->StmtListNode:
    prog = parser.parse(str(prog))
    prog = MelASTBuilder().transform(prog)
    return prog
