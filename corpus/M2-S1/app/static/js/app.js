// Confirm before delete
function confirmDelete(name) {
  return confirm(`Êtes-vous sûr de vouloir supprimer ${name} ? Cette action est irréversible.`);
}

// Stagger user cards animation
document.addEventListener("DOMContentLoaded", () => {
  const cards = document.querySelectorAll(".user-card");
  cards.forEach((card, i) => {
    card.style.animationDelay = `${i * 0.05}s`;
  });

  // Auto-dismiss alerts
  const alerts = document.querySelectorAll(".alert-success");
  alerts.forEach(alert => {
    setTimeout(() => {
      alert.style.transition = "opacity 0.5s";
      alert.style.opacity = "0";
      setTimeout(() => alert.remove(), 500);
    }, 4000);
  });
});
