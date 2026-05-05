# Architecture

## Dispute pipeline

1. CSV upload via web form.
2. Validator parses + checks row schema; rejects malformed rows
   with line-precise errors.
3. Classifier assigns dispute reason codes.
4. Submitter dispatches to merchant portal APIs.
5. Audit logger records actor + timestamp + outcome.

## Audit trail

Every action is recorded with the actor's identity. Audit log is
queryable by case ID and date range.
