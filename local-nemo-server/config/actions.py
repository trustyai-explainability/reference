from typing import Optional
from nemoguardrails.actions import action


@action(is_system_action=True)
async def check_message_length(context: Optional[dict] = None) -> str:
    """Check if user message is within acceptable length limits."""
    user_message = context.get("user_message", "")
    word_count = len(user_message.split())
    MAX_WORDS = 100
    if word_count > MAX_WORDS:
        return "blocked_too_long"
    elif word_count > MAX_WORDS * 0.8:
        return "warning_long"
    return "allowed"