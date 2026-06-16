const express = require('express');
const { db } = require('../db');
const { render, escapeHtml, flash, verifyCsrf } = require('../view-engine');
const { requireAuth } = require('../middleware');
const router = express.Router();
router.use(requireAuth);
router.get('/notifications', (req, res) => {
  const notifications = db.prepare('SELECT * FROM notifications WHERE user_id = ? ORDER BY created_at DESC').all(req.session.user.id);
  const items = notifications.map(n => `<li class="notification ${n.is_read ? '' : 'unread'}"><p>${escapeHtml(n.message)}</p><small>${escapeHtml(n.created_at)}</small></li>`).join('');
  render(req, res, 'notifications', { title: 'Notifications', notifications: items || '<li>Aucune notification.</li>' });
});
router.post('/notifications/read', verifyCsrf, (req, res) => {
  db.prepare('UPDATE notifications SET is_read = 1 WHERE user_id = ?').run(req.session.user.id);
  flash(req, 'success', 'Notifications marquées comme lues.');
  res.redirect('/notifications');
});
module.exports = router;
