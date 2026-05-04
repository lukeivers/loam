# SYNTHETIC TEST FIXTURE — see ../../../README.md
# RECOGNIZER: migrations (CreateXxx class + change method +
# polymorphic reference).
class CreateWebhookEvents < ActiveRecord::Migration[7.1]
  def change
    create_table :webhook_events do |t|
      t.references :owner, polymorphic: true, null: false, index: true
      t.string :event_type, null: false
      t.text :payload, null: false
      t.timestamp :dispatched_at
      t.timestamps
    end

    add_index :webhook_events, :event_type
    add_index :webhook_events, %i[owner_type owner_id event_type]
  end
end
