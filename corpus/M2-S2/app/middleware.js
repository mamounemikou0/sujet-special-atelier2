function requireAuth(req, res, next) {
  if (!req.session.userId) {
    return res.redirect('/login?redirect=' + encodeURIComponent(req.originalUrl));
  }
  next();
}

function requireManager(req, res, next) {
  if (!req.session.userId) {
    return res.redirect('/login');
  }
  if (req.session.userRole !== 'gestionnaire') {
    return res.status(403).send('Accès refusé - Réservé aux gestionnaires');
  }
  next();
}

module.exports = { requireAuth, requireManager };
