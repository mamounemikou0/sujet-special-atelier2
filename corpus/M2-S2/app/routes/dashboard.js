const express = require('express');
const router = express.Router();
const { requireManager } = require('../middleware');
const path = require('path');

router.get('/', requireManager, (req, res) => {
  res.sendFile(path.join(__dirname, '../views/dashboard.html'));
});

module.exports = router;
