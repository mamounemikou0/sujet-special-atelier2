const Database = require('better-sqlite3');
const db = new Database('app.db');

function requireAuth(req, res, next) {
    if (req.session.userId) {
        req.user = db.prepare('SELECT * FROM users WHERE id = ?').get(req.session.userId);
        if (req.user) {
            return next();
        }
    }
    res.redirect('/login');
}

function requireAdmin(req, res, next) {
    if (req.session.userId) {
        req.user = db.prepare('SELECT * FROM users WHERE id = ?').get(req.session.userId);
        if (req.user && req.user.role === 'admin') {
            return next();
        }
    }
    res.redirect('/login');
}

module.exports = { requireAuth, requireAdmin, db };