"""
MindCare AI — Crisis Safety Detector
Scans user messages for crisis signals and returns escalation info.
"""
from config import settings


class SafetyChecker:
    """
    Scans incoming messages for crisis keywords.
    Returns structured risk assessment.
    """

    def __init__(self):
        self.keywords = [kw.lower() for kw in settings.CRISIS_KEYWORDS]

    def check(self, message: str) -> dict:
        """
        Analyze a message for crisis indicators.

        Returns:
            {
                "is_crisis": bool,
                "matched_keywords": list[str],
                "crisis_message": str | None,
                "hotline": str | None
            }
        """
        lower_msg = message.lower()
        matched = [kw for kw in self.keywords if kw in lower_msg]

        if matched:
            return {
                "is_crisis": True,
                "matched_keywords": matched,
                "crisis_message": settings.CRISIS_MESSAGE,
                "hotline": settings.CRISIS_HOTLINE,
            }

        return {
            "is_crisis": False,
            "matched_keywords": [],
            "crisis_message": None,
            "hotline": None,
        }


# Singleton
safety_checker = SafetyChecker()
