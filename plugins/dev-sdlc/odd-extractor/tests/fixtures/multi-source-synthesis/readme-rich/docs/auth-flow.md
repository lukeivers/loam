# Auth flow

Operators authenticate via OAuth against the company SSO. RSA-OAEP
encrypts session tokens at rest. Tokens stay confidential under
transport (TLS 1.3 minimum).
