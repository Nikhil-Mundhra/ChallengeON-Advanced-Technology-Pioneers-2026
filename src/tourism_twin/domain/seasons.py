"""Abu Dhabi tourism climate seasons."""

SEASONS = ["Winter_Peak", "Spring_Shoulder", "Summer_Trough", "Autumn_Shoulder"]


def assign_season(month: int) -> str:
    """Classify month into Abu Dhabi tourism climate seasons."""
    if month in (11, 12, 1, 2, 3):
        return "Winter_Peak"
    elif month in (4, 5):
        return "Spring_Shoulder"
    elif month in (6, 7, 8):
        return "Summer_Trough"
    else:
        return "Autumn_Shoulder"
