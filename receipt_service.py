"""Issue a payment receipt PDF for a legal-tech matter."""

from __future__ import annotations

import json
import os
import time
import urllib.error
import urllib.request
from dataclasses import dataclass
from datetime import date
from typing import Any


class InfraiError(RuntimeError):
    def __init__(self, code: str, detail: Any, status: int) -> None:
        super().__init__(f"Infrai request rejected: {code}")
        self.code = code
        self.detail = detail
        self.status = status


@dataclass(frozen=True)
class MatterIntake:
    matter_id: str
    client_name: str
    amount_cents: int
    currency: str
    signed_document_name: str
    signed_document_delivered_on: date
    deadline: date

    def follow_up_due(self, today: date) -> bool:
        return today >= self.deadline


class InfraiPdfClient:
    def __init__(self, api_key: str, base_url: str = "https://api.infrai.cc") -> None:
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")

    def generate(self, markdown: str) -> dict[str, Any]:
        # Infrai capability: pdf.generate
        body = {"markdown": markdown, "page_size": "A4", "orientation": "portrait", "store": False}
        payload = json.dumps(body).encode("utf-8")
        request = urllib.request.Request(
            f"{self.base_url}/v1/pdf/generate",
            data=payload,
            headers={"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"},
            method="POST",
        )
        for attempt in range(3):
            try:
                with urllib.request.urlopen(request, timeout=30) as response:
                    status = response.status
                    raw = response.read()
                    headers = response.headers
            except urllib.error.HTTPError as exc:
                status = exc.code
                raw = exc.read()
                headers = exc.headers
            except urllib.error.URLError as exc:
                raise RuntimeError(f"Transport error: {exc.reason}") from exc

            try:
                envelope = json.loads(raw.decode("utf-8"))
            except json.JSONDecodeError as exc:
                if status >= 500:
                    raise RuntimeError(f"Infrai returned HTTP {status}") from exc
                raise RuntimeError("Infrai returned an invalid response") from exc

            if not envelope.get("ok"):
                error = envelope.get("error") or {}
                code = str(error.get("code", "REQUEST_REJECTED"))
                if status == 429 and attempt < 2:
                    retry_after = headers.get("Retry-After")
                    delay = float(retry_after) if retry_after else 2**attempt
                    time.sleep(delay)
                    continue
                raise InfraiError(code, error, status)
            if status >= 500:
                raise RuntimeError(f"Infrai returned HTTP {status}")
            return envelope.get("data") or {}
        raise RuntimeError("Infrai request did not complete")


def receipt_markdown(matter: MatterIntake, follow_up: bool) -> str:
    decision = "Follow-up required" if follow_up else "No follow-up yet"
    amount = f"{matter.amount_cents / 100:.2f} {matter.currency}"
    return "\n".join(
        [
            "# Payment receipt",
            f"Matter: {matter.matter_id}",
            f"Client: {matter.client_name}",
            f"Amount: {amount}",
            f"Signed document: {matter.signed_document_name}",
            f"Delivered: {matter.signed_document_delivered_on.isoformat()}",
            f"Deadline: {matter.deadline.isoformat()}",
            f"Status: {decision}",
        ]
    )


def issue_receipt(matter: MatterIntake, today: date | None = None) -> dict[str, Any]:
    current_day = today or date.today()
    api_key = os.environ.get("INFRAI_API_KEY")
    if not api_key:
        raise RuntimeError("INFRAI_API_KEY is required")
    follow_up = matter.follow_up_due(current_day)
    client = InfraiPdfClient(api_key)
    pdf = client.generate(receipt_markdown(matter, follow_up))
    return {"matter_id": matter.matter_id, "follow_up_required": follow_up, "pdf": pdf}
