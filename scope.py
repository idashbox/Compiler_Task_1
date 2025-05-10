class Scope:
    def __init__(self, parent=None):
        self.parent = parent
        self.variables = {}

    def declare(self, name, var_type):
        if name in self.variables:
            raise Exception(f"Переменная '{name}' уже объявлена в данной области видимости.")
        self.variables[name] = var_type

    def lookup(self, name):
        if name in self.variables:
            return self.variables[name]
        if self.parent is not None:
            return self.parent.lookup(name)
        return None

    def is_declared_in_current_scope(self, name):
        return name in self.variables

    def __contains__(self, name):
        return name in self.variables or (self.parent is not None and name in self.parent)