from datetime import date

from receipt_service import MatterIntake, issue_receipt


if __name__ == "__main__":
    matter = MatterIntake(
        matter_id="MAT-1042",
        client_name="Northwind Health",
        amount_cents=18500,
        currency="USD",
        signed_document_name="engagement-letter.pdf",
        signed_document_delivered_on=date(2026, 9, 1),
        deadline=date(2026, 9, 15),
    )
    print(issue_receipt(matter, today=date.today()))
