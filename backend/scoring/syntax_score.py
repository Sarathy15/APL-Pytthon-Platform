import ast

class SyntaxScore:
    @staticmethod
    def evaluate(code: str):
        try:
            ast.parse(code)
            return 100
        except SyntaxError:
            return 0
