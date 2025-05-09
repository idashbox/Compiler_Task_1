from mel_ast import AstNode, LiteralNode, VarsDeclNode, TypeDeclNode, ArrayTypeNode, IdentNode, ArrayNode, AssignNode

class Type:
    """Базовый класс всех типов."""
    def __eq__(self, other):
        return self.__class__ == other.__class__ and str(self) == str(other)

    def __str__(self):
        return self.__class__.__name__

    def __repr__(self):
        return str(self)


class PrimitiveType(Type):
    def __init__(self, name: str):
        self.name = name

    def __eq__(self, other):
        return isinstance(other, PrimitiveType) and self.name == other.name

    def __repr__(self):
        return self.name


class ArrayType(Type):
    def __init__(self, base_type: Type):
        self.base_type = base_type

    def __eq__(self, other):
        return isinstance(other, ArrayType) and self.base_type == other.base_type

    def __repr__(self):
        return f"{self.base_type}[]"


class ClassType(Type):
    def __init__(self, name: str):
        self.name = name

    def __eq__(self, other):
        return isinstance(other, ClassType) and self.name == other.name

    def __repr__(self):
        return f"class {self.name}"


# Примитивные типы
INT = PrimitiveType("int")
FLOAT = PrimitiveType("float")
STRING = PrimitiveType("string")
BOOL = PrimitiveType("bool")


def get_type_from_node(node):
    if isinstance(node, LiteralNode):
        value = node.value
        if isinstance(value, bool):
            return BOOL
        elif isinstance(value, int):
            return INT
        elif isinstance(value, float):
            return FLOAT
        elif isinstance(value, str):
            return STRING

    elif isinstance(node, IdentNode):
        # Для идентификаторов тип будет определен из таблицы символов
        return None

    elif isinstance(node, ArrayNode):
        if node.elements:
            element_type = get_type_from_node(node.elements[0])
            return ArrayType(element_type)
        return ArrayType(INT)  # Для пустых массивов

    elif isinstance(node, VarsDeclNode):
        return get_type_from_node(node.type)

    elif isinstance(node, AssignNode):
        return get_type_from_node(node.var)

    elif isinstance(node, TypeDeclNode):
        if isinstance(node.typename, ArrayTypeNode):
            return ArrayType(get_type_from_typename(node.typename.name))
        return get_type_from_typename(node.typename)

    elif isinstance(node, ArrayTypeNode):
        return ArrayType(get_type_from_typename(node.name))

    return None


def get_type_from_typename(typename):
    if isinstance(typename, str):
        if typename == "int":
            return INT
        elif typename == "float":
            return FLOAT
        elif typename == "string":
            return STRING
        elif typename == "bool":
            return BOOL
        elif typename.endswith("[]"):
            return ArrayType(get_type_from_typename(typename[:-2]))
        else:
            return ClassType(typename)
    return None


def equals_simple(node1: AstNode, node2: AstNode) -> bool:
    type1 = get_type_from_node(node1)
    type2 = get_type_from_node(node2)
    return equals_simple_type(type1, type2)


def equals_simple_type(type1: Type, type2: Type) -> bool:
    if type1 is None or type2 is None:
        return False
    return type1 == type2