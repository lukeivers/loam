# SYNTHETIC TEST FIXTURE — see ../../../README.md
# RECOGNIZER: migrations (CreateXxx class + change method +
# create_table block + foreign_key + index).
class CreatePayments < ActiveRecord::Migration[7.1]
  def change
    create_table :payments do |t|
      t.references :customer, null: false, foreign_key: true
      t.bigint :amount_cents, null: false
      t.string :currency, null: false, limit: 3
      t.string :status, null: false, default: 'pending'
      t.string :gateway_reference
      t.text :description
      t.text :failure_reason
      t.timestamp :seen_at
      t.timestamps
    end

    add_index :payments, %i[customer_id status]
    add_index :payments, :gateway_reference, unique: true,
              where: 'gateway_reference IS NOT NULL'
  end
end
