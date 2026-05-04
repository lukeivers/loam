# SYNTHETIC TEST FIXTURE — see ../README.md
# RECOGNIZER: routes — exercises resources, namespace, get verbs.
Rails.application.routes.draw do
  resources :payments

  namespace :api do
    resources :webhooks, only: [:create]
  end

  get '/health', to: 'health#index'
end
