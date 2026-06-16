function confirmDeleteSelf() {
    return confirm("Êtes-vous sûr de vouloir supprimer votre compte ? Cette action est irréversible.");
}

function confirmDeleteUser(username) {
    return confirm("Supprimer le compte de '" + username + "' ?");
}
