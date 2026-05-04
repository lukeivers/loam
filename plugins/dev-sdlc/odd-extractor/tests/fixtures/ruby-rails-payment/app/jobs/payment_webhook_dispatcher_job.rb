# SYNTHETIC TEST FIXTURE — see ../../README.md
# RECOGNIZER: jobs (include Sidekiq::Job; fan-out pattern;
# perform method).
class PaymentWebhookDispatcherJob
  include Sidekiq::Job

  sidekiq_options queue: 'webhooks', retry: 5

  def perform(webhook_event_id)
    event = WebhookEvent.find(webhook_event_id)
    return if event.dispatched?

    subscribers_for(event).each do |subscriber|
      DeliverWebhookJob.perform_async(event.id, subscriber.id)
    end

    event.update!(dispatched_at: Time.current)
  end

  private

  def subscribers_for(event)
    # In a real app this would consult a subscriber registry filtered
    # by event_type. Synthetic stub.
    []
  end
end
