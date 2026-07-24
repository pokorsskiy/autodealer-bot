const telegram = window.Telegram?.WebApp;
const form = document.querySelector('#lead-form');
const carSelect = document.querySelector('#car-interest');
const toast = document.querySelector('#toast');

if (telegram) {
  telegram.ready();
  telegram.expand();
}

const showToast = (message) => {
  toast.textContent = message;
  toast.classList.add('is-visible');
  window.setTimeout(() => toast.classList.remove('is-visible'), 2600);
};

document.querySelectorAll('[data-car]').forEach((card) => {
  card.addEventListener('click', () => {
    const selectedCar = card.dataset.car;
    carSelect.value = selectedCar;
    document.querySelectorAll('[data-car]').forEach((item) => {
      const selected = item === card;
      item.classList.toggle('is-selected', selected);
      item.setAttribute('aria-pressed', String(selected));
    });
    showToast(`${selectedCar} добавлен в заявку`);
  });
});

form.addEventListener('submit', (event) => {
  event.preventDefault();
  if (!form.reportValidity()) return;

  const lead = Object.fromEntries(new FormData(form));
  if (!telegram) {
    showToast('Откройте страницу из Telegram для отправки заявки');
    return;
  }
  telegram.sendData(JSON.stringify(lead));
});
