document.addEventListener('DOMContentLoaded', () => {
  const cardInput = document.querySelector('input[name="card_number"]');
  if (cardInput) {
    cardInput.addEventListener('input', () => {
      let digits = cardInput.value.replace(/\D/g, '').slice(0, 16);
      cardInput.value = digits.replace(/(.{4})/g, '$1 ').trim();
    });
  }
});
