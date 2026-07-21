from enum import StrEnum


class AiRunStatus(StrEnum):
    SUCCEEDED = "SUCCEEDED"
    FAILED = "FAILED"
    DISABLED = "DISABLED"


class AiSuggestionKind(StrEnum):
    CATEGORY = "CATEGORY"
    PRIORITY = "PRIORITY"
    DUPLICATE = "DUPLICATE"
    SUMMARY = "SUMMARY"
    RESPONSE = "RESPONSE"


class AiSuggestionStatus(StrEnum):
    PENDING = "PENDING"
    ACCEPTED = "ACCEPTED"
    REJECTED = "REJECTED"
