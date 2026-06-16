const { db, createUpcomingNotifications } = require('./db');
const { flash } = require('./view-engine');

function attachGlobals(req, res, next) {
  createUpcomingNotifications();
  req.locals = { unreadCount: 0 };
  if (req.session.user) {
    req.locals.unreadCount = db.prepare('SELECT COUNT(*) AS total FROM notifications WHERE user_id = ? AND is_read = 0').get(req.session.user.id).total;
  }
  next();
}
function requireAuth(req, res, next) {
  if (!req.session.user) {
    flash(req, 'error', 'Veuillez vous connecter pour continuer.');
    return res.redirect('/login');
  }
  next();
}
function requireManager(req, res, next) {
  if (!req.session.user || req.session.user.role !== 'manager') return res.status(403).send('Accès réservé au gestionnaire.');
  next();
}
module.exports = { attachGlobals, requireAuth, requireManager };
