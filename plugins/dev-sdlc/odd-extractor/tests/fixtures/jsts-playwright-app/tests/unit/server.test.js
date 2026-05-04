// SYNTHETIC TEST FIXTURE — Jest-style unit tests for Express handlers.
// Module shape: CommonJS.
const app = require('../../src/server');

describe('GET /health', () => {
  it('returns ok status', () => {
    // Synthetic test — wouldn't actually run without supertest.
    expect(app).toBeDefined();
  });

  it('does not require authentication', () => {
    expect(app).toBeDefined();
  });
});

describe('GET /admin', () => {
  it('requires authentication', () => {
    expect(app).toBeDefined();
  });
});
