from dataclasses import dataclass

@dataclass
class ActionItem:
    text: str
    type: str  # "Confirmed" | "Possible"