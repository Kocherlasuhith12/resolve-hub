import hashlib
from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True)
class EmailMessage:
    recipient: str
    subject: str
    text_body: str
    idempotency_key: str


class EmailProvider(Protocol):
    async def send(self, message: EmailMessage) -> str: ...


class DeterministicEmailProvider:
    """Side-effect-free provider used until a deployment configures an email adapter."""

    async def send(self, message: EmailMessage) -> str:
        digest = hashlib.sha256(message.idempotency_key.encode()).hexdigest()[:24]
        return f"deterministic:{digest}"
