from typing import Any, List, Union
from pathlib import Path
from mel_ast import *
from mel_types import Type, PrimitiveType, ArrayType, ClassType, get_type_from_typename
from code_gen_base import CodeLabel, CodeGenerator, find_vars_decls

JBC_TYPE_NAMES = {
    'int': 'int',
    'float': 'double',
    'bool': 'boolean',
    'string': 'java.lang.String',
    'void': 'void'
}

JBC_TYPE_SIZES = {
    'int': 1,
    'float': 2,
    'bool': 1,
    'string': 1,
    'void': 0
}

JBC_TYPE_PREFIXES = {
    'int': 'i',
    'float': 'd',
    'bool': 'i',
    'string': 'a',
    'void': ''
}

JBC_COMPARE_SUFFIXES = {
    BinOp.GT: 'gt',
    BinOp.LT: 'lt',
    BinOp.GE: 'ge',
    BinOp.LE: 'le',
    BinOp.EQ: 'eq',
    BinOp.NE: 'ne'
}

RUNTIME_CLASS_NAME = 'CompilerDemo.Runtime'

class JbcException(Exception):
    def __init__(self, message, **kwargs):
        self.message = message

class JbcCodeGenerator(CodeGenerator):
    def __init__(self, file_name: str):
        super().__init__()
        self.file_name = file_name
        self.class_name = Path(file_name).stem
        if not self.class_name[0].isidentifier():
            self.class_name = f'_{self.class_name}'
        self.local_var_offset = 0
        self.global_var_index = 0
        self.global_vars = {}  # Словарь для хранения типов глобальных переменных

    def start(self):
        self.add('version 6;')
        self.add(f'public class {self.class_name} extends java.lang.Object')
        self.add('{')

    def end(self):
        self.add('}')

    def push_const(self, type_name: str, value: Any):
        if type_name == 'int':
            self.add('ldc', value)
        elif type_name == 'float':
            self.add('ldc2_w', f'{value:.20f}D')
        elif type_name == 'bool':
            self.add(f'iconst_{1 if value else 0}')
        elif type_name == 'string':
            self.add('ldc', f'"{value}"')

    def get_type_from_node(self, node: ExprNode) -> Type:
        if isinstance(node, LiteralNode):
            return node.get_type()
        elif isinstance(node, IdentNode):
            # Сначала проверяем global_vars
            if node.name in self.global_vars:
                return self.global_vars[node.name]
            # Затем проверяем current_scope
            var_type = self.current_scope.lookup(node.name) if self.current_scope else None
            if not var_type:
                raise JbcException(f"Variable {node.name} not found")
            return var_type
        elif isinstance(node, BinOpNode):
            return self.get_type_from_node(node.arg1)
        elif isinstance(node, FuncCallNode):
            func_info = self.functions.get(node.func.name)
            if not func_info:
                raise JbcException(f"Function {node.func.name} not found")
            return func_info['return_type']
        else:
            raise JbcException(f"Cannot determine type for node {type(node).__name__}")

    def visit(self, node):
        method_name = f'jbc_{type(node).__name__}'
        method = getattr(self, method_name, self.generic_jbc)
        return method(node)

    def generic_jbc(self, node):
        for child in node.children:
            if child:
                self.visit(child)

    def jbc_LiteralNode(self, node: LiteralNode):
        type_name = node.get_type().name
        self.push_const(type_name, node.value)

    def jbc_IdentNode(self, node: IdentNode):
        # Проверяем global_vars или current_scope
        if node.name in self.global_vars:
            var_type = self.global_vars[node.name]
        else:
            var_type = self.current_scope.lookup(node.name) if self.current_scope else None
            if not var_type:
                raise JbcException(f"Variable {node.name} not found")
        type_name = var_type.name
        if hasattr(node, 'jbc_offset'):
            self.add(f'{JBC_TYPE_PREFIXES[type_name]}load', node.jbc_offset)
        else:
            self.add(f'getstatic {self.class_name}#{JBC_TYPE_NAMES[type_name]} _gv{node.name}')

    def jbc_AssignNode(self, node: AssignNode):
        self.visit(node.val)
        if isinstance(node.var, IdentNode):
            if node.var.name in self.global_vars:
                var_type = self.global_vars[node.var.name]
            else:
                var_type = self.current_scope.lookup(node.var.name) if self.current_scope else None
                if not var_type:
                    raise JbcException(f"Variable {node.var.name} not found")
            type_name = var_type.name
            if hasattr(node.var, 'jbc_offset'):
                self.add(f'{JBC_TYPE_PREFIXES[type_name]}store', node.var.jbc_offset)
            else:
                self.add(f'putstatic {self.class_name}#{JBC_TYPE_NAMES[type_name]} _gv{node.var.name}')
        elif isinstance(node.var, MemberAccessNode):
            self.add(f'putfield {node.var.obj.name}.{node.var.member.name}')

    def jbc_VarsDeclNode(self, node: VarsDeclNode):
        var_type = get_type_from_typename(node.type.typename)
        for var in node.vars:
            if isinstance(var, IdentNode):
                var.jbc_offset = self.local_var_offset
                self.local_var_offset += JBC_TYPE_SIZES[var_type.name]
            elif isinstance(var, AssignNode):
                self.visit(var)

    def jbc_BinOpNode(self, node: BinOpNode):
        self.visit(node.arg1)
        self.visit(node.arg2)
        type_name = self.get_type_from_node(node.arg1).name
        op_map = {
            BinOp.ADD: 'add',
            BinOp.SUB: 'sub',
            BinOp.MUL: 'mul',
            BinOp.DIV: 'div',
            BinOp.MOD: 'rem'
        }
        if node.op in op_map:
            self.add(f'{JBC_TYPE_PREFIXES[type_name]}{op_map[node.op]}')
        elif node.op in [BinOp.EQ, BinOp.NE, BinOp.GT, BinOp.LT, BinOp.GE, BinOp.LE]:
            if type_name == 'string':
                self.add('invokevirtual java.lang.String#int compareTo(java.lang.String)')
                self.bool_val_gen(f'if{JBC_COMPARE_SUFFIXES[node.op]}')
            elif type_name == 'float':
                self.add('dcmpg')
                self.bool_val_gen(f'if{JBC_COMPARE_SUFFIXES[node.op]}')
            else:
                self.bool_val_gen(f'if_icmp{JBC_COMPARE_SUFFIXES[node.op]}')
        elif node.op in [BinOp.AND, BinOp.OR]:
            self.add('iand' if node.op == BinOp.AND else 'ior')

    def bool_val_gen(self, cmd: str):
        true_label = CodeLabel()
        end_label = CodeLabel()
        self.add(cmd, true_label)
        self.add('iconst_0')
        self.add('goto', end_label)
        self.add(true_label)
        self.add('iconst_1')
        self.add(end_label)

    def jbc_FuncCallNode(self, node: FuncCallNode):
        for param in node.params:
            self.visit(param)
        if node.func.name == 'println':
            param_type = self.get_type_from_node(node.params[0]).name if node.params else 'void'
            java_type = JBC_TYPE_NAMES.get(param_type, 'java.lang.Object')
            self.add(f'invokestatic {RUNTIME_CLASS_NAME}/println({java_type})V')
        else:
            func_info = self.functions.get(node.func.name)
            if not func_info:
                raise JbcException(f"Function {node.func.name} not found")
            param_types = ', '.join(JBC_TYPE_NAMES[p.name] for p in func_info['param_types'])
            ret_type = JBC_TYPE_NAMES[func_info['return_type'].name]
            self.add(f'invokestatic {self.class_name}#{ret_type} {node.func.name}({param_types})')

    def jbc_FuncDeclNode(self, node: FuncDeclNode):
        self.local_var_offset = 0
        ret_type = JBC_TYPE_NAMES[node.return_type.typename]
        params = []
        for p in node.params.vars:
            p_type = JBC_TYPE_NAMES[p.type.typename]
            for v in p.vars:
                v.jbc_offset = self.local_var_offset
                self.local_var_offset += JBC_TYPE_SIZES[p.type.typename]
                params.append(f'{p_type} {v.name}')
        params_str = ', '.join(params)
        self.add(f'public static {ret_type} {node.name.name}({params_str})')
        self.add('{')
        self.visit(node.body)
        if ret_type != 'void':
            self.add(f'{JBC_TYPE_PREFIXES[ret_type]}return')
        self.add('}')

    def jbc_IfNode(self, node: IfNode):
        else_label = CodeLabel()
        end_label = CodeLabel()
        self.visit(node.cond)
        self.add('ifeq', else_label)
        self.visit(node.then_stmt)
        self.add('goto', end_label)
        self.add(else_label)
        if node.else_stmt:
            self.visit(node.else_stmt)
        self.add(end_label)

    def jbc_WhileNode(self, node: WhileNode):
        start_label = CodeLabel()
        end_label = CodeLabel()
        self.add(start_label)
        self.visit(node.cond)
        self.add('ifeq', end_label)
        self.visit(node.body)
        self.add('goto', start_label)
        self.add(end_label)

    def jbc_ClassDeclNode(self, node: ClassDeclNode):
        self.add(f'public class {node.name.name}')
        self.add('{')
        for stmt in node.body.stmts:
            if isinstance(stmt, VarsDeclNode):
                for var in stmt.vars:
                    var_type = JBC_TYPE_NAMES[stmt.type.typename]
                    var_name = var.name if isinstance(var, IdentNode) else var.var.name
                    self.add(f'public {var_type} {var_name};')
        self.add('}')

    def jbc_NewInstanceNode(self, node: NewInstanceNode):
        self.add(f'new {node.class_name.name}')
        self.add('dup')
        self.add(f'invokespecial {node.class_name.name}#void <init>()')

    def jbc_StmtListNode(self, node: StmtListNode):
        for stmt in node.stmts:
            self.visit(stmt)

    def gen_program(self, prog: StmtListNode):
        self.start()
        global_vars = find_vars_decls(prog)
        for node in global_vars:
            var_type = get_type_from_typename(node.type.typename)
            vars_flat = []
            for var in node.vars:
                if isinstance(var, list):
                    vars_flat.extend(var)
                else:
                    vars_flat.append(var)
            for var in vars_flat:
                if isinstance(var, IdentNode):
                    var_name = var.name
                    self.global_vars[var_name] = var_type  # Регистрируем глобальную переменную
                    self.add(f'public static {JBC_TYPE_NAMES[var_type.name]} _gv{var_name};')
                elif isinstance(var, AssignNode):
                    var_name = var.var.name
                    self.global_vars[var_name] = var_type  # Регистрируем глобальную переменную
                    self.add(f'public static {JBC_TYPE_NAMES[var_type.name]} _gv{var_name};')
                    self.visit(var)
                else:
                    raise JbcException(f"Unexpected var type in VarsDeclNode: {type(var)}")
        self.add('')
        self.add('public static void main(java.lang.String[])')
        self.add('{')
        for stmt in prog.stmts:
            if not isinstance(stmt, (FuncDeclNode, ClassDeclNode)):
                self.visit(stmt)
        self.add('return')
        self.add('}')
        for stmt in prog.stmts:
            if isinstance(stmt, (FuncDeclNode, ClassDeclNode)):
                self.visit(stmt)
        self.end()