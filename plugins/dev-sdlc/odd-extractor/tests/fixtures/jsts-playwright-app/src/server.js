// SYNTHETIC TEST FIXTURE — Express app entry point.
// Module shape: CommonJS (require / module.exports).
const express = require('express');
const usersRouter = require('./routes/users');
const { requireAuth } = require('./middleware/auth');

const app = express();
app.use(express.json());

app.get('/health', (req, res) => res.json({ status: 'ok' }));
app.use('/users', usersRouter);

// Module-level admin gate.
app.get('/admin', requireAuth, (req, res) => res.json({ admin: true }));

module.exports = app;

if (require.main === module) {
  const PORT = process.env.PORT || 3000;
  app.listen(PORT, () => {
    // eslint-disable-next-line no-console
    console.log(`server listening on ${PORT}`);
  });
}
