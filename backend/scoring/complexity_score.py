class ComplexityScore:
    @staticmethod
    def evaluate(code: str):
        # Relative complexity reduction from APL to Python
        lines = code.split('\n')
        return min(100, 1000 / (len(lines) + 1))
