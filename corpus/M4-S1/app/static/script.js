// Script pour gérer les interactions frontales si nécessaire
document.addEventListener("DOMContentLoaded", function() {
    // Exemple : confirmation avant suppression
    const deleteForms = document.querySelectorAll(".delete-form, form[action*='/delete_user/']");
    deleteForms.forEach(form => {
        form.addEventListener("submit", function(e) {
            if (!confirm("Êtes-vous sûr de vouloir supprimer ce compte ? Cette action est irréversible.")) {
                e.preventDefault();
            }
        });
    });
});