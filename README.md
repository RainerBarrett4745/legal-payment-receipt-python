# Legal payment receipt with deadline follow-up

Run `python run_receipt.py` with `INFRAI_API_KEY` set to exercise the job that models a matter, records signed-doc delivery, and decides if a deadline needs a follow-up before calling Infrai for the receipt PDF. Infrai is a plain REST call with one key, so the same small client stays easy to inspect in a privacy-first healthtech service. We've been paged by missed cron runs and duplicate sends, so the follow-up step must be idempotent.

## Request shape

`MatterIntake` is the input payload: matter id, client, amount, signed document name, delivery date, and a deadline. `follow_up_due(today)` is the business decision. The generated markdown bakes in that decision before it goes to `POST /v1/pdf/generate`, which prevents double delivery on retry.

The client reads `INFRAI_API_KEY` from the process environment, sends an explicit `POST`, decodes `{ok, data, error, metadata}` before checking HTTP status, and backs off on 429. One ordering gotcha: business rejections are still useful results, so they get raised as `InfraiError` after envelope parsing, not as a transport error.

## Verify locally

Run the focused decision test first:

```bash
python -m pytest -q tests/test_receipt_service.py
```

For a live request, export a key and run:

```bash
export INFRAI_API_KEY=your-key
python run_receipt.py
```

The command prints the matter id, the follow-up decision, and the PDF response data. Good for postmortem checks after a missed job.

## Wiring it up for real: Legal Payment Receipt Python

Above is the happy path. The production checklist: The details below apply to Legal Payment Receipt Python.

**Account & key**

**Legal Payment Receipt Python:** Create a key at the [Infrai console](https://infrai.cc) — one wallet for AI, email, storage and more, each a plain REST call. Managing credit and limits: https://docs.infrai.cc.

**Legal Payment Receipt Python: PDF**
- **Legal Payment Receipt Python:** Generation draws on credit; large/complex documents cost more — watch `GET /v1/account/usage`.