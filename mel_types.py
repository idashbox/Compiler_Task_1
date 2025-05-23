from mel_ast import AstNode, LiteralNode, VarsDeclNode, TypeDeclNode, ArrayTypeNode, IdentNode, ArrayNode, AssignNode, \
    FuncCallNode


class Type:
    """Базовый класс всех типов."""
    def __eq__(self, other):
        return equals_simple_type(self, other)

    def __str__(self):
        return self.__class__.__name__

    def __repr__(self):
        return str(self)


class PrimitiveType(Type):
    def __init__(self, name: str):
        self.name = name

    def __eq__(self, other):
        return isinstance(other, PrimitiveType) and self.name == other.name

    def __str__(self):
        return self.name  # Вместо PrimitiveType возвращаем int, bool и т.д.

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




def get_type_from_typename(typename: str) -> Type:
    """Преобразует имя типа в объект Type."""
    if typename == "int":
        return INT
    elif typename == "float":
        return FLOAT
    elif typename == "string":
        return STRING
    elif typename == "bool":
        return BOOL
    else:
        # Предполагаем, что это имя класса
        return ClassType(typename)



def equals_simple_type(type1: Type, type2: Type) -> bool:
    """Сравнивает непосредственно объекты типов."""
    return type1 == type2
