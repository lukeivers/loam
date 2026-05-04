# SYNTHETIC TEST FIXTURE — see ../../../README.md
# RECOGNIZER: migrations (create_table + add_reference polymorphic
# + add_index).
class CreatePayments < ActiveRecord::Migration[7.1]
  def change
    create_table :payments do |t|
      t.bigint :amount_cents, null: false
      t.references :owner, polymorphic: true, null: false
      t.timestamps
    end

    add_index :payments, [:owner_type, :owner_id]
  end
end
