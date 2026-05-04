// SYNTHETIC TEST FIXTURE — Express auth middleware.
// Module shape: CommonJS.
function requireAuth(req, res, next) {
  if (!req.headers.authorization) {
    res.sendStatus(401);
    return;
  }
  next();
}

function authenticate(req, res, next) {
  // Simulated auth check.
  next();
}

module.exports = { requireAuth, authenticate };
