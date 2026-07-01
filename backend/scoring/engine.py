from .syntax_score import SyntaxScore
from .complexity_score import ComplexityScore
from .conversion_score import ConversionScore
from .confidence_score import ConfidenceScore

class ScoreEngine:
    @staticmethod
    def calculate(python_code: str, conversion_confidence: float, semantic_score: float = 100.0) -> dict[str, float]:
        syntax_score = float(SyntaxScore.evaluate(python_code))
        complexity_score = float(ComplexityScore.evaluate(python_code))
        conversion_score = float(ConversionScore.evaluate(conversion_confidence))
        confidence_score = float(ConfidenceScore.calculate(syntax_score, complexity_score, conversion_score, semantic_score))

        return {
            "syntax_score": syntax_score,
            "complexity_score": complexity_score,
            "conversion_score": conversion_score,
            "semantic_score": float(semantic_score),
            "confidence_score": confidence_score,
        }
