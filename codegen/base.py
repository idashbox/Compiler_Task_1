from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from mel_ast import *

class CodeGenBase(ABC):
    def __init__(self):
        self.code: List[str] = []
        self.indent: int = 0
        self.locals: Dict[str, Any] = {}
        
    def emit(self, instruction: str) -> None:
        """Добавляет инструкцию в генерируемый код с учетом отступа"""
        self.code.append("    " * self.indent + instruction)
        
    def visit(self, node: AstNode) -> None:
        """Вызывает соответствующий метод visit_* для переданного узла"""
        if isinstance(node, list):
            for item in node:
                self.visit(item)
            return
        method_name = f'visit_{type(node).__name__}'
        method = getattr(self, method_name, None)
        if method is None:
            print(f"Warning: No visit method for {type(node).__name__}")
            return
        return method(node)
        
    @abstractmethod
    def visit_literal(self, node: LiteralNode) -> None:
        pass
        
    @abstractmethod
    def visit_ident(self, node: IdentNode) -> None:
        pass
        
    @abstractmethod
    def visit_bin_op(self, node: BinOpNode) -> None:
        pass
        
    @abstractmethod
    def visit_unary_op(self, node: UnaryOpNode) -> None:
        pass
        
    @abstractmethod
    def visit_assign(self, node: AssignNode) -> None:
        pass
        
    @abstractmethod
    def visit_if(self, node: IfNode) -> None:
        pass
        
    @abstractmethod
    def visit_while(self, node: WhileNode) -> None:
        pass
        
    @abstractmethod
    def visit_for(self, node: ForNode) -> None:
        pass
        
    @abstractmethod
    def visit_stmt_list(self, node: StmtListNode) -> None:
        pass
        
    @abstractmethod
    def visit_func_call(self, node: FuncCallNode) -> None:
        pass
        
    @abstractmethod
    def visit_func_decl(self, node: FuncDeclNode) -> None:
        pass
        
    @abstractmethod
    def visit_class_decl(self, node: ClassDeclNode) -> None:
        pass
        
    @abstractmethod
    def visit_member_access(self, node: MemberAccessNode) -> None:
        pass
        
    @abstractmethod
    def visit_array(self, node: ArrayNode) -> None:
        pass
        
    @abstractmethod
    def visit_array_index(self, node: ArrayIndexNode) -> None:
        pass
        
    @abstractmethod
    def visit_array_assign(self, node: ArrayAssignNode) -> None:
        pass
        
    @abstractmethod
    def visit_new_instance(self, node: NewInstanceNode) -> None:
        pass
        
    @abstractmethod
    def visit_return(self, node: ReturnNode) -> None:
        pass 