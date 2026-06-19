from services import gemini_service

VALID_CATEGORIES = [
    "Newsletter",
    "Job/Recruitment",
    "Finance",
    "Notifications",
    "Personal",
    "Work/Professional",
]


def get_category(subject: str, sender: str, snippet: str) -> str:
    """Categorize an email into one of the valid categories using Gemini AI."""
    try:
        category = gemini_service.categorize_email(subject, sender, snippet)
        category = category.strip()

        if category in VALID_CATEGORIES:
            return category

        # Try partial match (case-insensitive)
        for valid in VALID_CATEGORIES:
            if valid.lower() in category.lower():
                return valid

        return "Work/Professional"
    except Exception:
        return "Work/Professional"
