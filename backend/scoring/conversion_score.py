class ConversionScore:
    @staticmethod
    def evaluate(confidence: float) -> float:
        return max(0.0, min(100.0, confidence))
