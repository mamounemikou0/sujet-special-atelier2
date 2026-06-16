const express = require('express');
const session = require('express-session');
const path = require('path');
const { initDatabase, createUpcomingNotifications } = require('./db');
const { attachGlobals } = require('./middleware');
const { render } = require('./view-engine');

const app = express();
const PORT = Number(process.env.PORT) || 3000;
initDatabase();
createUpcomingNotifications();

app.disable('x-powered-by');
app.use(express.urlencoded({ extended: false }));
app.use(express.static(path.join(__dirname, 'public')));
app.use(session({
  secret: process.env.SESSION_SECRET || 'change-this-development-secret-in-production',
  resave: false,
  saveUninitialized: false,
  cookie: { httpOnly: true, sameSite: 'lax', secure: false, maxAge: 1000 * 60 * 60 * 8 }
}));
app.use(attachGlobals);
app.use(require('./routes/auth'));
app.use(require('./routes/rooms'));
app.use(require('./routes/bookings'));
app.use(require('./routes/notifications'));
app.use(require('./routes/manager'));
app.get('/', (req, res) => res.redirect('/rooms'));
app.use((req, res) => res.status(404).send('Page introuvable.'));
app.use((err, req, res, next) => { console.error(err); res.status(500).send('Erreur interne du serveur.'); });

const notificationTimer = setInterval(createUpcomingNotifications, 60 * 1000);
notificationTimer.unref();
if (require.main === module) app.listen(PORT, () => console.log(`Application disponible sur http://localhost:${PORT}`));
module.exports = app;
