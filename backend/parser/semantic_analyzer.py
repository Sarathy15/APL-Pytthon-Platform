import ast

class SemanticAnalyzer:
    @staticmethod
    def extract_intent(apl_code: str):
        # Enterprise-grade APL pattern matching
        patterns = {
            "+/": "Sum reduction",
            "⍳": "Index generator",
            "×": "Multiplication",
            "⍴": "Shape/Reshape"
        }
        found_intents = []
        for symbol, intent in patterns.items():
            if symbol in apl_code:
                found_intents.append(intent)
        return found_intents

class OperatorMapper:
    @staticmethod
    def get_numpy_equivalent(apl_op: str):
        mapping = {
            "+/": "np.sum",
            "⍳": "np.arange",
            "⍴": "np.reshape",
            "⌈": "np.ceil",
            "⌊": "np.floor"
        }
        return mapping.get(apl_op, "unknown")
