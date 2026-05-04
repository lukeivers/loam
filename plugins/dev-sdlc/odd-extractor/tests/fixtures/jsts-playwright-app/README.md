# jsts-playwright-app — SYNTHETIC TEST FIXTURE — NOT A REAL APP

This is a small but realistic JavaScript/TypeScript/Playwright codebase used to exercise the loam odd-extractor JS/TS adapter (v0.1.8 Cycle 4a). It is shaped like Eric's first project per the cycle plan-doc:

- **TypeScript Playwright tests + page objects** under `src/playwright/` and `tests/playwright/`.
- **JavaScript Node.js/Express backend** under `src/` (mix of CommonJS and ESM module shapes).
- **Plain HTML/JS surface** under `public/`.
- **Schemas** — Zod (in `src/schemas/user.ts`) and class-validator (in `src/schemas/session-class-validator.ts`).
- **Test runners exercised** — Playwright Test, Vitest, Jest-style.

It is NOT a runnable application. Running `npm install && npm test` will not work — there is no real implementation behind the surface; the fixture exists to exercise loam's JS/TS adapter recognizers end-to-end.

## File map

```
package.json              # declares express, @playwright/test, zod, vitest, class-validator
tsconfig.json             # TypeScript compilation config (strict; ES2022)
playwright.config.ts      # Playwright configuration

src/
  server.js               # Express app entry (CommonJS)
  routes/
    users.js              # Express user routes (CJS — `module.exports = router`)
    sessions.mjs          # Express session routes (ESM — `export default router`)
  middleware/
    auth.js               # `requireAuth` / `authenticate` middleware (CJS)
  schemas/
    user.ts               # Zod schema for users (TS, ESM)
    session-class-validator.ts   # class-validator-decorated DTO (TS, ESM)
  playwright/
    login-page.ts         # Playwright page object — LoginPage class
    dashboard-page.ts     # Playwright page object — DashboardPage class

tests/
  playwright/
    login.spec.ts         # Playwright tests using LoginPage
    dashboard.spec.ts     # Playwright tests using DashboardPage
  unit/
    users.test.ts         # Vitest unit tests for the user Zod schema
    server.test.js        # Jest-style unit tests for Express handlers (CJS)

public/
  index.html              # Plain HTML/JS — script tag with client-side JS
  admin.html              # Second plain HTML page

README.md                 # This file
```

## Recognizer coverage

Every recognizer in `loam_odd_extractor.lang.jsts.recognizers` has at least one match in this fixture:

| Recognizer | File(s) |
|---|---|
| `express_routes` | `src/routes/users.js` (CJS), `src/routes/sessions.mjs` (ESM) |
| `playwright_tests` | `tests/playwright/login.spec.ts`, `tests/playwright/dashboard.spec.ts` |
| `playwright_page_objects` | `src/playwright/login-page.ts`, `src/playwright/dashboard-page.ts` |
| `ts_types` | `src/schemas/user.ts`, `src/schemas/session-class-validator.ts` |
| `zod_schemas` | `src/schemas/user.ts` |
| `class_validator` | `src/schemas/session-class-validator.ts` |
| `test_runners` (Vitest) | `tests/unit/users.test.ts` |
| `test_runners` (Jest-style) | `tests/unit/server.test.js` |
| `plain_html_js` | `public/index.html`, `public/admin.html` |

## Heuristic inferences this fixture triggers

- Zod `email: z.string().email()` → "userSchema requires a valid email".
- Zod `name: z.string().min(...)` → minimum-length inference.
- class-validator `@IsEmail()` → email-required inference.
- Express middleware `requireAuth` / `authenticate` → "route requires authentication" inference.
- Playwright page-object `login*` method → auth entry point inference.

## Test counts (per cycle plan-doc AC.FIXTURES.1 — ≥10 across runners)

- Playwright: ≥3 in `login.spec.ts` + ≥2 in `dashboard.spec.ts` = ≥5.
- Vitest: ≥3 in `users.test.ts`.
- Jest-style: ≥2 in `server.test.js`.
- **Total: ≥10**.
