class ConfidenceScore:
    @staticmethod
    def calculate(syntax: float, complexity: float, conversion: float, semantic: float) -> float:
        return max(0.0, min(100.0, (0.2 * syntax) + (0.2 * complexity) + (0.4 * conversion) + (0.2 * semantic)))
