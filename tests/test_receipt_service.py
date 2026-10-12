from datetime import date

from receipt_service import MatterIntake, receipt_markdown


def test_deadline_decides_follow_up_and_receipt_text() -> None:
    matter = MatterIntake(
        matter_id="MAT-7",
        client_name="Clinic A",
        amount_cents=5000,
        currency="USD",
        signed_document_name="signed.pdf",
        signed_document_delivered_on=date(2026, 9, 1),
        deadline=date(2026, 9, 10),
    )
    assert matter.follow_up_due(date(2026, 9, 10)) is True
    assert "Status: Follow-up required" in receipt_markdown(matter, True)
    assert "50.00 USD" in receipt_markdown(matter, True)
