import re

import re

BLOCKED_PATTERNS = [

    # Prompt injection
    r"ignore\s+(all\s+)?previous\s+instructions",
    r"ignore\s+(all\s+)?instructions",
    r"forget\s+.*instructions",

    # Identity attacks
    r"forget\s+you\s+are",
    r"you\s+are\s+now",
    r"pretend\s+to\s+be",
    r"act\s+as",
    r"roleplay\s+as",

    # System prompt extraction
    r"system\s+prompt",
    r"developer\s+prompt",
    r"hidden\s+prompt",
    r"hidden\s+instructions",
    r"reveal\s+your\s+prompt",
    r"show\s+your\s+prompt",
    r"print\s+your\s+system\s+message",

    # Jailbreak attempts
    r"bypass",
    r"jailbreak",
    r"do\s+anything\s+now",
    r"dan\s+mode",
    r"disable\s+safety",
    r"ignore\s+safety",
]

class KillSwitch:

    @staticmethod
    def check(query: str):

        q = query.lower()

        for pattern in BLOCKED_PATTERNS:
            if re.search(pattern, q):
                return False, pattern

        return True, None