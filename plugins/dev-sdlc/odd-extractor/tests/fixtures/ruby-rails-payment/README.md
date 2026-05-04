# ruby-rails-payment — SYNTHETIC fixture (canonical)

> **SYNTHETIC TEST FIXTURE** — this is a synthetic Rails-payment-shape
> codebase authored for testing the loam odd-extractor's Ruby/Rails
> adapter against a representative SaaS-payment app. **It is NOT a
> real payment processor**; it cannot accept real money; the database
> migrations + Gemfile + routes + models are illustrative shape only.

This fixture is the canonical Ruby-Rails surface for v0.1.8 Cycle 4b
end-to-end smoke (per master plan AC.FIXTURES.{2, 3-ruby, 4-ruby, 5}).
It is shape-richer than the Cycle 3 `synthetic-rails` fixture (which
is intentionally minimal for adapter unit-shape testing). Both
fixtures co-exist; this one is the **release-level smoke** target.

## Shape

Mirrors a Rails-payment-shape SaaS (think: Stripe-style payment
processor, Spree/Solidus simplified, jumpstart-pro payment surface):

- **5+ RESTful routes** under `:api` namespace — `payments`,
  `customers`, `webhook_events`, `sessions`, plus `health`.
- **3 ActiveRecord models** with callbacks, concerns, polymorphic
  associations:
  - `Payment` — `before_save` callback, `after_create` callback,
    `belongs_to :customer`, `has_many :webhook_events` (the
    polymorphic owner).
  - `Customer` — `before_validation` callback, `validates ...
    presence: true / uniqueness: true`, `has_many :payments`,
    `has_secure_password`.
  - `WebhookEvent` — `belongs_to :owner, polymorphic: true`
    (polymorphic across Payment / Customer / Refund),
    `before_save` callback, `validates :event_type, presence: true`.
- **2 concerns** under `app/models/concerns/`:
  - `Auditable` — `extend ActiveSupport::Concern`; `included do
    after_create :record_audit_log end`.
  - `Timestampable` — `extend ActiveSupport::Concern`; `included
    do before_save :update_seen_at end`.
- **2 Sidekiq jobs** under `app/jobs/`:
  - `ProcessPaymentJob` — `include Sidekiq::Job`; performs
    payment-charge orchestration.
  - `PaymentWebhookDispatcherJob` — Sidekiq fan-out pattern;
    enqueues per-subscriber webhook deliveries.
- **3 controllers** under `app/controllers/api/`:
  - `PaymentsController` — 5 RESTful actions + before-action auth.
  - `CustomersController` — 4 RESTful actions + strong params.
  - `WebhookEventsController` — 2 RESTful actions (index + show).
- **3 migrations** under `db/migrate/`.
- **≥10 RSpec specs** under `spec/` covering models, controllers,
  jobs.
- **`Gemfile`** with `rails`, `rspec-rails`, `sidekiq`, `pg`,
  `bcrypt`, `jbuilder` (representative Rails-payment gem set).
- **`config/routes.rb`** with namespaced routes.
- **`LICENSE`** Apache-2.0.

## Why this fixture exists

Cycle 4 of the v0.1.8 odd-extractor release ships first-class
adapters for Ruby/Rails (Cycle 3) and JS/TS/Playwright (Cycle 4a).
Each adapter needs a representative fixture for end-to-end smoke
testing. The Ruby fixture must exercise enough Rails idiom (callbacks
+ concerns + polymorphic + Sidekiq + ≥10 RSpec specs) that the
extractor's confidence-band distribution lands within the master
plan AC.FIXTURES.3 floor (≥3 VERIFIED + ≥5 PLAUSIBLE + ≥2
HYPOTHESISED).

## Why this fixture is "canonical" not "synthetic"

Cycle 3's `synthetic-rails` fixture is intentionally thin (one
controller, one model, ~5 RSpec specs) — enough for adapter
unit-shape testing but not a representative SaaS app. This canonical
fixture is the Cycle 4b release-level smoke target: shape-richer,
exercises more Rails idiom, sized to drive the band-distribution
sanity check.

## Why this fixture is still synthetic

A real OSS Rails-payment fixture (e.g., solidus, spree,
jumpstart-pro-clone) is the v0.2.1 fresh-user smoke target — it's
out of scope for v0.1.8. This canonical fixture is the v0.1.8
release-level surface; the v0.2.1 fresh-user smoke surface is
larger.

## Files

```
.
├── Gemfile
├── LICENSE
├── README.md (this file)
├── app/
│   ├── controllers/
│   │   └── api/
│   │       ├── customers_controller.rb
│   │       ├── payments_controller.rb
│   │       └── webhook_events_controller.rb
│   ├── jobs/
│   │   ├── payment_webhook_dispatcher_job.rb
│   │   └── process_payment_job.rb
│   └── models/
│       ├── concerns/
│       │   ├── auditable.rb
│       │   └── timestampable.rb
│       ├── customer.rb
│       ├── payment.rb
│       └── webhook_event.rb
├── config/
│   └── routes.rb
├── db/
│   └── migrate/
│       ├── 20260101000001_create_payments.rb
│       ├── 20260101000002_create_customers.rb
│       └── 20260101000003_create_webhook_events.rb
└── spec/
    ├── controllers/
    │   └── api/
    │       └── payments_controller_spec.rb
    ├── jobs/
    │   ├── payment_webhook_dispatcher_job_spec.rb
    │   └── process_payment_job_spec.rb
    └── models/
        ├── customer_spec.rb
        ├── payment_spec.rb
        └── webhook_event_spec.rb
```

20 files; ≥10 RSpec specs (verifiable via `grep -c "^\s*it " spec/`).

## License

Apache-2.0 — matches the loam parent license.
