const telegram = window.Telegram?.WebApp;

if (telegram) {
  telegram.ready();
  telegram.expand();
}

const form = document.querySelector('#lead-form');
const carSelect = document.querySelector('#car-interest');

document.querySelectorAll('[data-car]').forEach((button) => {
  button.addEventListener('click', () => {
    carSelect.value = button.dataset.car;
    carSelect.scrollIntoView({ behavior: 'smooth', block: 'center' });
  });
});

form.addEventListener('submit', (event) => {
  event.preventDefault();
  if (!form.reportValidity()) return;

  const lead = Object.fromEntries(new FormData(form));
  if (!telegram) {
    alert('Откройте эту страницу из Telegram, чтобы отправить заявку.');
    return;
  }
  telegram.sendData(JSON.stringify(lead));
});
