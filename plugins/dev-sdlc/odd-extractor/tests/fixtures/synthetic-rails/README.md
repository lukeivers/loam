# synthetic-rails — SYNTHETIC TEST FIXTURE

**This is NOT a real Rails app.** It is a structural fixture for the
v0.1.8 Cycle 3 Ruby/Rails adapter test surface, deliberately sized
small (11 files) and shaped to exercise every Rails idiom recognizer
in :mod:`loam_odd_extractor.lang.ruby.recognizers`.

Running ``bundle install`` and ``rspec`` against this fixture will
fail (no real ``application.rb``, no ``database.yml``, no test
helpers). The canonical full Ruby-Rails-payment fixture lands in
v0.1.8 Cycle 4.

## Idiom coverage map

| File | Recognizer-target |
|---|---|
| `Gemfile` | adapter `supports()` smoke-positive |
| `config/routes.rb` | routes recognizer (resources / namespace / get) |
| `app/controllers/payments_controller.rb` | controller class |
| `app/models/payment.rb` | active_record + callbacks + concerns + polymorphic |
| `app/models/concerns/auditable.rb` | concerns (definition) |
| `app/jobs/payment_webhook_job.rb` | jobs (ActiveJob + queue_as) |
| `app/jobs/sidekiq_metrics_worker.rb` | jobs (Sidekiq + sidekiq_options queue) |
| `db/migrate/20260101000001_create_payments.rb` | migrations (create_table + add_reference polymorphic + add_index) |
| `spec/models/payment_spec.rb` | rspec_tests (3 it blocks) |
| `spec/jobs/payment_webhook_job_spec.rb` | rspec_tests (1 it block) |
| `test/integration/payment_flow_test.rb` | minitest_tests (1 test block) |

## Heuristic-inference exercise

The fixture exercises 4 of 5 heuristics in
:mod:`loam_odd_extractor.lang.ruby.heuristic_inferences`:

- `validates :amount_cents, presence: true` → required-on-create.
- `belongs_to :owner, polymorphic: true` → multi-type-ownership.
- `before_save :normalize_amount` → normalised-before-save.
- `after_create :enqueue_webhook_job` → async-after-create.

(The uniqueness heuristic is not exercised here; covered by
:file:`tests/lang/ruby/snippets/`.)
