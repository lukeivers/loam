# SYNTHETIC TEST FIXTURE — see ../../../README.md
# RECOGNIZER: migrations (CreateXxx class + change method).
class CreateCustomers < ActiveRecord::Migration[7.1]
  def change
    create_table :customers do |t|
      t.string :email, null: false
      t.string :name, null: false
      t.string :password_digest, null: false
      t.boolean :suspended, null: false, default: false
      t.timestamp :suspended_at
      t.timestamps
    end

    add_index :customers, :email, unique: true
    add_index :customers, :suspended
  end
end
