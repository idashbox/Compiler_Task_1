from typing import List, Union, Any
from mel_ast import VarsDeclNode, StmtListNode  # Импортируем необходимые классы

class CodeLabel:
    def __init__(self, prefix: str = 'L'):
        self.index = None
        self.prefix = prefix

    def __str__(self):
        return f'{self.prefix}_{self.index}'

class CodeLine:
    def __init__(self, code: Union[str, CodeLabel], *params: Union[str, CodeLabel], label: CodeLabel = None, indent: str = None):
        if isinstance(code, CodeLabel):
            code, label = None, code
        self.code = code
        self.params = params
        self.label = label
        self.indent = indent

    def __str__(self):
        line = ''
        if self.label:
            if self.indent:
                line += self.indent[2:]
            line += f'{self.label}:'
            if self.code:
                line += ' '
        else:
            if self.indent:
                line += self.indent
        if self.code:
            line += self.code
            for p in self.params:
                line += ' ' + str(p)
        return line

class CodeGenerator:
    def __init__(self):
        self.code_lines: List[CodeLine] = []
        self.indent = ''
        self.current_scope = None
        self.functions = {}

    def add(self, code: str, *params: Union[str, int, CodeLabel], label: CodeLabel = None):
        if isinstance(code, CodeLabel):
            code, label = None, code
        if code and len(code) > 0 and code[-1] == '}':
            self.indent = self.indent[2:]
        self.code_lines.append(CodeLine(code, *params, label=label, indent=self.indent))
        if code and len(code) > 0 and code[-1] == '{':
            self.indent = self.indent + '  '

    @property
    def code(self) -> List[str]:
        index = 0
        for cl in self.code_lines:
            if cl.label:
                cl.label.index = index
                index += 1
        code: List[str] = []
        for cl in self.code_lines:
            code.append(str(cl))
        return code

def find_vars_decls(prog: StmtListNode) -> List[VarsDeclNode]:
    decls = []
    for stmt in prog.stmts:
        if isinstance(stmt, VarsDeclNode):
            decls.append(stmt)
    return decls