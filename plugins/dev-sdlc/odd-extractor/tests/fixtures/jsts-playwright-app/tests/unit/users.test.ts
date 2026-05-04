// SYNTHETIC TEST FIXTURE — Vitest unit tests for the user Zod schema.
import { describe, it, test, expect } from 'vitest';
import { userSchema, userArraySchema } from '../../src/schemas/user';

describe('userSchema', () => {
  it('accepts a valid user', () => {
    const result = userSchema.parse({
      email: 'alice@example.com',
      name: 'Alice',
    });
    expect(result.email).toBe('alice@example.com');
  });

  it('rejects an invalid email', () => {
    expect(() =>
      userSchema.parse({ email: 'not-an-email', name: 'Alice' })
    ).toThrow();
  });

  it('rejects a too-short name', () => {
    expect(() =>
      userSchema.parse({ email: 'alice@example.com', name: 'A' })
    ).toThrow();
  });

  test('userArraySchema accepts an array', () => {
    const result = userArraySchema.parse([
      { email: 'a@b.com', name: 'AB' },
      { email: 'c@d.com', name: 'CD' },
    ]);
    expect(result).toHaveLength(2);
  });
});
