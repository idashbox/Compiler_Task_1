class Scope:
    def __init__(self, parent=None):
        self.symbols = {}
        self.parent = parent

    def declare(self, name, var_type):
        print(f"Добавление {name}: {var_type} в область {id(self)}")  # Отладка
        if name in self.symbols:
            raise Exception(f"Переменная '{name}' уже объявлена")
        self.symbols[name] = var_type

    def lookup(self, name):
        print(f"Поиск {name} в области {id(self)}: {self.symbols.get(name)}")  # Отладка
        if name in self.symbols:
            return self.symbols[name]
        if self.parent:
            return self.parent.lookup(name)
        return None