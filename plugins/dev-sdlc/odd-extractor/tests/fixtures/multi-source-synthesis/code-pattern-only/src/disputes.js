// Express dispute filing routes — no docs, no tests.
const express = require("express");
const router = express.Router();

router.post("/disputes", (req, res) => {
  res.json({ ok: true });
});

router.get("/disputes/:id", (req, res) => {
  res.json({ id: req.params.id });
});

module.exports = router;
