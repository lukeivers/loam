# SYNTHETIC TEST FIXTURE — see ../../../README.md
# RECOGNIZER: jobs (Sidekiq include + sidekiq_options queue:).
class SidekiqMetricsWorker
  include Sidekiq::Job

  sidekiq_options queue: :metrics

  def perform
    Metrics.publish(payment_count: Payment.count)
  end
end
