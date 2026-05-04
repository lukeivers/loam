// SYNTHETIC TEST FIXTURE — Express user routes.
// Module shape: CommonJS (require / module.exports).
const express = require('express');
const { requireAuth, authenticate } = require('../middleware/auth');

const router = express.Router();

// Public — list users.
router.get('/', (req, res) => {
  res.json([{ id: 1, name: 'alice' }]);
});

// Auth-gated — create user.
router.post('/', requireAuth, (req, res) => {
  res.status(201).json({ id: 2, name: req.body.name });
});

// Admin-gated — delete user.
router.delete('/:id', authenticate, (req, res) => {
  res.sendStatus(204);
});

// Auth-gated — update user.
router.put('/:id', requireAuth, (req, res) => {
  res.json({ id: req.params.id, name: req.body.name });
});

// Public — get-by-id.
router.get('/:id', (req, res) => {
  res.json({ id: req.params.id, name: 'alice' });
});

module.exports = router;
