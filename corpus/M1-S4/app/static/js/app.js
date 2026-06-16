function confirmDelete(){return confirm('Supprimer cet utilisateur ? Cette action est irréversible.');}
document.querySelectorAll('input[type=date]').forEach(i=>{if(!i.value)i.value=new Date().toISOString().slice(0,10);});
