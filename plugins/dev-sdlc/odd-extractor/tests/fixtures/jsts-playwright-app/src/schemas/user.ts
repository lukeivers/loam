// SYNTHETIC TEST FIXTURE — Zod user schema.
// Module shape: ESM (TypeScript).
import { z } from 'zod';

export interface User {
  email: string;
  name: string;
  age?: number;
}

export type UserId = string;

export const userSchema = z.object({
  email: z.string().email(),
  name: z.string().min(2),
  age: z.number().min(0).optional(),
});

export const userArraySchema = z.array(userSchema);

export type UserInput = z.infer<typeof userSchema>;
