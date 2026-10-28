"""Fast ML prefilter: estimates P(risky) so the LLM is only called when useful."""
import pathlib
import joblib

MODEL_PATH = pathlib.Path(__file__).resolve().parent.parent / "ml" / "risk_clf.joblib"


class RiskClassifier:
    def __init__(self, path=MODEL_PATH):
        self.model = joblib.load(path)

    def risk(self, text: str) -> float:
        return float(self.model.predict_proba([text])[0][1])


def load_classifier():
    return RiskClassifier() if MODEL_PATH.exists() else None
