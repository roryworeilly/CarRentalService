"""Mock in-process payment gateway (prototype only; no Stripe)."""
from __future__ import annotations

import uuid
from dataclasses import dataclass


DECLINE_CARD = "4000000000000002"


@dataclass
class ChargeResult:
    success: bool
    intent_id: str
    message: str
    last4: str


class MockGateway:
    """Fake PSP. Returns failure for the standard test-declined card."""

    def charge(self, *, card_number: str, amount: float, idempotency_key: str) -> ChargeResult:
        # NFR 4: never log/store full card number. Only derive last4.
        last4 = (card_number or "")[-4:].rjust(4, "0")
        intent_id = f"mock_{uuid.uuid4().hex[:16]}"
        if card_number == DECLINE_CARD:
            return ChargeResult(success=False, intent_id=intent_id, message="card declined", last4=last4)
        return ChargeResult(success=True, intent_id=intent_id, message="ok", last4=last4)
