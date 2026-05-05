# DisputeApp

DisputeApp is an operator tool that lets operations staff file refund
disputes against the DoorDash and Uber Eats merchant portals at scale.
It replaces a manual workflow where operators logged into each portal,
clicked through dispute filing forms, and tracked outcomes in
spreadsheets.

## What it does

- Operators upload CSVs of orders + dispute reasons.
- The system validates each row, classifies disputes by reason code,
  and submits them to the right portal.
- Audit trail records who initiated each dispute and the outcome.
- SOC-2 audit-trail floor is the compliance requirement that drives
  the audit-trail design.

## Why

Without DisputeApp, operations staff spend ~3 hours per shift on
manual portal work; with it, they file 10× the disputes in a tenth
of the time, and accounting reconciles outcomes from the audit trail
instead of cross-referencing 4 systems by hand.
