# SYNTHETIC TEST FIXTURE — see ../README.md
# RECOGNIZER: rails_routes (5 RESTful resources + custom routes).
Rails.application.routes.draw do
  namespace :api do
    resources :payments, only: %i[index show create update destroy] do
      member do
        post :refund
      end
    end

    resources :customers, only: %i[index show create update] do
      collection do
        get :search
      end
    end

    resources :webhook_events, only: %i[index show]

    resources :sessions, only: %i[create destroy]

    get :health, to: 'health#show'
  end

  root to: 'api/health#show'
end
