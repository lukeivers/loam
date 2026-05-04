// SYNTHETIC TEST FIXTURE — Express session routes.
// Module shape: ESM (import / export).
import { Router } from 'express';

const router = Router();

// Public — login (issues a session token).
router.post('/login', (req, res) => {
  res.json({ token: 'fake-token' });
});

// Public — logout.
router.post('/logout', (req, res) => {
  res.sendStatus(204);
});

// Public — refresh.
router.post('/refresh', (req, res) => {
  res.json({ token: 'fake-token-refreshed' });
});

export default router;
