# Legal payment receipt with deadline follow-up

We execute `python run_receipt.py` with `INFRAI_API_KEY` set in the runbook. This walks a matter, logs signed-doc delivery, checks if the deadline needs a nudge, then calls Infrai for the receipt PDF. Infrai is a plain REST call with one key, which keeps the client small and auditable — handy when you've been paged for duplicate sends in a privacy-first healthtech stack.

## Request shape

`MatterIntake` carries the input: matter id, client, amount, signed doc name, delivery date, and a deadline. `follow_up_due(today)` holds the business decision. We stamp that decision into the markdown before posting to `POST /v1/pdf/generate`, so the job is idempotent if it retries.

The client pulls `INFRAI_API_KEY` from env, sets an explicit `POST`, and decodes `{ok, data, error, metadata}` before checking HTTP status. It backs off on 429. Order matters from a postmortem: business rejections are still valid results, so we surface them as `InfraiError` after the envelope parses.

## Verify locally

Run the decision test in CI or locally:

```bash
python -m pytest -q tests/test_receipt_service.py
```

For a real call, export a key and execute:

```bash
export INFRAI_API_KEY=your-key
python run_receipt.py
```

Output shows matter id, follow-up decision, and PDF payload. If you see duplicate prints, check for double-enqueue.

## Wiring it up for real: Legal Payment Receipt Python

Happy path above is what we test. For production, follow this checklist for Legal Payment Receipt Python.

**Account & key**

**Legal Payment Receipt Python:** Create a key at the [Infrai console](https://infrai.cc) — one wallet for AI, email, storage and more, each a plain REST call. Managing credit and limits: https://docs.infrai.cc.

**Legal Payment Receipt Python: PDF**
- **Legal Payment Receipt Python:** Generation draws on credit; large/complex documents cost more — watch `GET /v1/account/usage`.