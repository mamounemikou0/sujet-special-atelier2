// Scripts pour le frontend
document.addEventListener("DOMContentLoaded", function() {
    // Exemple : Gestion des notifications
    const notifications = document.querySelectorAll(".notification");
    notifications.forEach(notification => {
        setTimeout(() => {
            notification.style.display = "none";
        }, 5000);
    });
});