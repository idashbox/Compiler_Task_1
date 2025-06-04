# code_gen_base.py
from typing import Any, List
from mel_ast import StmtListNode, VarsDeclNode


class CodeLabel:
    def __init__(self):
        self.name = f"L{hash(self)}"

    def __str__(self):
        return self.name

class CodeGenerator:
    def __init__(self):
        self.code: List[str] = []
        self.current_scope = None
        self.functions = {}

    def add(self, line: str):
        self.code.append(line)

    def get_type_from_node(self, node: Any) -> Any:
        return node.get_type() if hasattr(node, 'get_type') else None

def find_vars_decls(prog: StmtListNode) -> List[Any]:
    decls = []
    for stmt in prog.stmts:
        if isinstance(stmt, VarsDeclNode):
            decls.append(stmt)
    return decls