function deleteUser(userId) {
    if (confirm('Êtes-vous sûr de vouloir supprimer cet utilisateur ? Cette action est irréversible.')) {
        fetch(`/users/delete/${userId}`, {
            method: 'POST',
        }).then(response => {
            if (response.redirected) {
                window.location.href = response.url;
            } else {
                return response.json();
            }
        }).then(data => {
            if (data && data.error) {
                alert(data.error);
            } else {
                window.location.reload();
            }
        }).catch(error => {
            console.error('Erreur:', error);
            alert('Une erreur est survenue lors de la suppression');
        });
    }
}

function deleteAccount() {
    if (confirm('Êtes-vous sûr de vouloir supprimer votre compte ? Cette action est irréversible.')) {
        const userId = document.querySelector('.profile-info p strong');
        // On récupère l'ID depuis la session
        fetch(`/users/delete/${currentUserId}`, {
            method: 'POST',
        }).then(response => {
            if (response.redirected) {
                window.location.href = response.url;
            }
        }).catch(error => {
            console.error('Erreur:', error);
            alert('Une erreur est survenue lors de la suppression de votre compte');
        });
    }
}

// Ajouter l'ID utilisateur dans la page profile
if (document.querySelector('.profile-container')) {
    const userInfo = document.querySelector('.profile-info');
    const usernameSpan = userInfo.querySelector('strong');
    if (usernameSpan) {
        window.currentUserId = document.querySelector('.user-row span:first-child').textContent;
    }
}