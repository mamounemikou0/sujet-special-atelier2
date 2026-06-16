/* layout.js - shared nav injection */
async function initLayout() {
  const res = await fetch('/api/session');
  const session = await res.json();
  if (!session.authenticated) {
    window.location.href = '/login';
    return null;
  }

  const notifRes = await fetch('/api/notifications');
  const notifs = await notifRes.json();
  const unread = notifs.filter(n => !n.read).length;

  const nav = document.getElementById('nav');
  if (nav) {
    nav.innerHTML = `
      <div class="nav-brand"><a href="/rooms">📅 RoomBook</a></div>
      <div class="nav-links">
        <a href="/rooms" class="${location.pathname.startsWith('/rooms') ? 'active' : ''}">Salles</a>
        <a href="/reservations" class="${location.pathname.startsWith('/reservations') ? 'active' : ''}">Mes réservations</a>
        ${session.userRole === 'gestionnaire' ? `<a href="/dashboard" class="${location.pathname === '/dashboard' ? 'active' : ''}">Tableau de bord</a>` : ''}
      </div>
      <div class="nav-right">
        <button class="notif-btn" id="notifBtn" title="Notifications">
          🔔 ${unread > 0 ? `<span class="notif-badge">${unread}</span>` : ''}
        </button>
        <div class="user-menu">
          <span class="user-name">${session.userName}</span>
          ${session.userRole === 'gestionnaire' ? '<span class="badge-role">Gestionnaire</span>' : ''}
          <a href="/logout" class="btn-logout">Déconnexion</a>
        </div>
      </div>
      <div class="notif-panel hidden" id="notifPanel">
        <div class="notif-header">
          <strong>Notifications</strong>
          <button onclick="markAllRead()">Tout lire</button>
        </div>
        <div id="notifList">
          ${notifs.length === 0 ? '<p class="notif-empty">Aucune notification</p>' :
            notifs.map(n => `
              <div class="notif-item ${n.read ? 'read' : 'unread'}" data-id="${n.id}">
                <p>${n.message}</p>
                <small>${new Date(n.created_at).toLocaleString('fr-FR')}</small>
                ${!n.read ? `<button onclick="markRead(${n.id}, this)">✓</button>` : ''}
              </div>
            `).join('')}
        </div>
      </div>
    `;

    document.getElementById('notifBtn').addEventListener('click', () => {
      document.getElementById('notifPanel').classList.toggle('hidden');
    });
    document.addEventListener('click', e => {
      if (!e.target.closest('.nav-right')) {
        document.getElementById('notifPanel')?.classList.add('hidden');
      }
    });
  }

  return session;
}

async function markRead(id, btn) {
  await fetch('/api/notifications/' + id + '/read', { method: 'POST' });
  const item = btn.closest('.notif-item');
  item.classList.remove('unread');
  item.classList.add('read');
  btn.remove();
  updateBadge();
}

async function markAllRead() {
  await fetch('/api/notifications/read-all', { method: 'POST' });
  document.querySelectorAll('.notif-item').forEach(i => {
    i.classList.remove('unread');
    i.classList.add('read');
    i.querySelector('button')?.remove();
  });
  updateBadge();
}

function updateBadge() {
  const unread = document.querySelectorAll('.notif-item.unread').length;
  const badge = document.querySelector('.notif-badge');
  if (badge) badge.textContent = unread || '';
  if (unread === 0 && badge) badge.remove();
}
