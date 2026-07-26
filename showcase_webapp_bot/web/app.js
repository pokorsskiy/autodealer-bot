const telegram = window.Telegram?.WebApp;

const state = {
  cars: [],
  search: "",
  location: "",
  brand: "",
  maxPrice: "",
  minYear: "",
  maxMileage: "",
  body: "",
  drive: "",
  sort: "new",
  view: sessionStorage.getItem("dealer-auto-view") || "grid",
  favorites: new Set(JSON.parse(sessionStorage.getItem("dealer-auto-favorites") || "[]")),
};

const elements = {
  list: document.querySelector("#car-list"),
  empty: document.querySelector("#empty-state"),
  resultCount: document.querySelector("#result-count"),
  favoriteHead: document.querySelector("#favorite-head"),
  favoriteHeadCount: document.querySelector("#favorite-head-count"),
  activeFilterCount: document.querySelector("#active-filter-count"),
  filtersButton: document.querySelector("#filters-button"),
  filtersPanel: document.querySelector("#filters-panel"),
  search: document.querySelector("#search"),
  brand: document.querySelector("#brand-filter"),
  price: document.querySelector("#price-filter"),
  year: document.querySelector("#year-filter"),
  mileage: document.querySelector("#mileage-filter"),
  body: document.querySelector("#body-filter"),
  drive: document.querySelector("#drive-filter"),
  sort: document.querySelector("#sort"),
  heroImage: document.querySelector("#hero-image"),
  favoritesDialog: document.querySelector("#favorites-dialog"),
  favoritesList: document.querySelector("#favorites-list"),
  favoritesEmpty: document.querySelector("#favorites-empty"),
  favoritesSummary: document.querySelector("#favorites-summary"),
  carDialog: document.querySelector("#car-dialog"),
  carDialogContent: document.querySelector("#car-dialog-content"),
  leadDialog: document.querySelector("#lead-dialog"),
  leadForm: document.querySelector("#lead-form"),
  carInterest: document.querySelector("#car-interest"),
  leadKicker: document.querySelector("#lead-kicker"),
  leadTitle: document.querySelector("#lead-dialog-title"),
  leadDescription: document.querySelector("#lead-description"),
  calculatorForm: document.querySelector("#calculator-form"),
  calculationResult: document.querySelector("#calculation-result"),
  toast: document.querySelector("#toast"),
};

if (telegram) {
  telegram.ready();
  telegram.expand();
  telegram.setHeaderColor?.("#17191d");
  telegram.setBackgroundColor?.("#f4f3f0");
}

const formatRub = (value) => `${Math.round(value).toLocaleString("ru-RU")} ₽`;
const escapeHtml = (value) => String(value)
  .replaceAll("&", "&amp;")
  .replaceAll("<", "&lt;")
  .replaceAll(">", "&gt;")
  .replaceAll('"', "&quot;")
  .replaceAll("'", "&#039;");
const locationLabel = (location) => location === "port" ? "В порту" : "В городе";
const firstImage = (car) => car.images?.[0]?.url || "";

const pluralCars = (count) => {
  const mod10 = count % 10;
  const mod100 = count % 100;
  if (mod10 === 1 && mod100 !== 11) return `${count} автомобиль`;
  if ([2, 3, 4].includes(mod10) && ![12, 13, 14].includes(mod100)) return `${count} автомобиля`;
  return `${count} автомобилей`;
};

let toastTimer;
function showToast(message) {
  window.clearTimeout(toastTimer);
  elements.toast.textContent = message;
  elements.toast.classList.add("is-visible");
  toastTimer = window.setTimeout(() => elements.toast.classList.remove("is-visible"), 2800);
}

function persistFavorites() {
  sessionStorage.setItem("dealer-auto-favorites", JSON.stringify([...state.favorites]));
}

function fillSelect(select, values) {
  [...new Set(values.filter(Boolean))].sort((a, b) => a.localeCompare(b, "ru")).forEach((value) => {
    select.add(new Option(value, value));
  });
}

function filteredCars() {
  const query = state.search.trim().toLocaleLowerCase("ru");
  const cars = state.cars.filter((car) => {
    const title = `${car.brand} ${car.model}`.toLocaleLowerCase("ru");
    return (!query || title.includes(query))
      && (!state.location || car.location === state.location)
      && (!state.brand || car.brand === state.brand)
      && (!state.maxPrice || car.price <= Number(state.maxPrice))
      && (!state.minYear || car.year >= Number(state.minYear))
      && (!state.maxMileage || car.mileage <= Number(state.maxMileage))
      && (!state.body || car.body === state.body)
      && (!state.drive || car.drive === state.drive);
  });
  return cars.sort((a, b) => {
    if (state.sort === "price-asc") return a.price - b.price;
    if (state.sort === "price-desc") return b.price - a.price;
    return b.year - a.year || a.sort_order - b.sort_order;
  });
}

function toggleFavorite(carId) {
  if (state.favorites.has(carId)) {
    state.favorites.delete(carId);
    showToast("Удалено из избранного");
  } else {
    state.favorites.add(carId);
    showToast("Добавлено в избранное");
  }
  persistFavorites();
  render();
  if (elements.favoritesDialog.open) renderFavorites();
}

function carCard(car) {
  const article = document.createElement("article");
  article.className = "car-card";

  const media = document.createElement("div");
  media.className = "car-card__media";
  const image = document.createElement("img");
  image.src = firstImage(car);
  image.alt = `${car.brand} ${car.model}, ${car.year}`;
  image.loading = "lazy";
  image.addEventListener("error", () => {
    image.removeAttribute("src");
    image.alt = `Фото ${car.brand} ${car.model} временно недоступно`;
  });
  const status = document.createElement("span");
  status.className = `car-card__status ${car.location}`;
  status.textContent = locationLabel(car.location);
  const favorite = document.createElement("button");
  favorite.type = "button";
  favorite.className = `favorite-button ${state.favorites.has(car.id) ? "is-active" : ""}`;
  favorite.textContent = state.favorites.has(car.id) ? "♥" : "♡";
  favorite.setAttribute("aria-label", `${state.favorites.has(car.id) ? "Удалить" : "Добавить"} ${car.brand} ${car.model} ${state.favorites.has(car.id) ? "из" : "в"} избранное`);
  favorite.addEventListener("click", () => toggleFavorite(car.id));
  media.append(image, status, favorite);
  if (car.images.length > 1) {
    const dots = document.createElement("span");
    dots.className = "car-card__dots";
    const dotItems = car.images.slice(0, 5).map(() => document.createElement("i"));
    dotItems[0].classList.add("is-active");
    dotItems.forEach((dot) => dots.append(dot));
    const next = document.createElement("button");
    next.type = "button";
    next.className = "card-gallery-next";
    next.textContent = "→";
    next.setAttribute("aria-label", "Следующее фото");
    let cardIndex = 0;
    next.addEventListener("click", () => {
      cardIndex = (cardIndex + 1) % car.images.length;
      image.src = car.images[cardIndex].url;
      image.alt = car.images[cardIndex].alt_text || `${car.brand} ${car.model}`;
      dotItems.forEach((dot, index) => dot.classList.toggle("is-active", index === Math.min(cardIndex, 4)));
    });
    media.append(dots, next);
  }

  const body = document.createElement("button");
  body.type = "button";
  body.className = "car-card__body";
  body.innerHTML = `
    <span class="car-card__brand">${escapeHtml(car.brand)}</span>
    <span class="car-card__title">${escapeHtml(car.model)}</span>
    <span class="car-card__meta">${car.year} · ${car.mileage.toLocaleString("ru-RU")} км · ${escapeHtml(car.drive)}</span>
    <span class="car-card__price">${formatRub(car.price)}</span>
  `;
  body.addEventListener("click", () => openCar(car.id));
  article.append(media, body);
  return article;
}

function render() {
  const visible = filteredCars();
  elements.list.classList.toggle("is-list", state.view === "list");
  elements.list.replaceChildren(...visible.map(carCard));
  elements.empty.hidden = visible.length !== 0;
  elements.resultCount.textContent = pluralCars(visible.length);
  elements.favoriteHeadCount.textContent = state.favorites.size;
  elements.activeFilterCount.textContent = [
    state.brand, state.maxPrice, state.minYear, state.maxMileage, state.body, state.drive,
  ].filter(Boolean).length;

  document.querySelectorAll("[data-location]").forEach((button) => {
    button.classList.toggle("is-active", button.dataset.location === state.location);
  });
  document.querySelectorAll("[data-view]").forEach((button) => {
    button.classList.toggle("is-active", button.dataset.view === state.view);
  });
}

function favoriteRow(car) {
  const article = document.createElement("article");
  article.className = "favorite-row";
  const image = document.createElement("img");
  image.src = firstImage(car);
  image.alt = `${car.brand} ${car.model}`;
  image.loading = "lazy";

  const content = document.createElement("button");
  content.type = "button";
  content.className = "favorite-row__content";
  const title = document.createElement("b");
  title.textContent = `${car.brand} ${car.model}`;
  const meta = document.createElement("span");
  meta.textContent = `${car.year} · ${locationLabel(car.location)}`;
  const price = document.createElement("strong");
  price.textContent = formatRub(car.price);
  content.append(title, meta, price);
  content.addEventListener("click", () => {
    elements.favoritesDialog.close();
    openCar(car.id);
  });

  const remove = document.createElement("button");
  remove.type = "button";
  remove.className = "favorite-row__remove";
  remove.textContent = "×";
  remove.setAttribute("aria-label", `Удалить ${car.brand} ${car.model} из избранного`);
  remove.addEventListener("click", () => toggleFavorite(car.id));
  article.append(image, content, remove);
  return article;
}

function renderFavorites() {
  const favorites = state.cars.filter((car) => state.favorites.has(car.id));
  elements.favoritesList.replaceChildren(...favorites.map(favoriteRow));
  elements.favoritesList.hidden = favorites.length === 0;
  elements.favoritesEmpty.hidden = favorites.length !== 0;
  elements.favoritesSummary.textContent = pluralCars(favorites.length);
}

function openFavorites() {
  renderFavorites();
  elements.favoritesDialog.showModal();
}

function openCar(carId) {
  const car = state.cars.find((item) => item.id === carId);
  if (!car) return;
  const images = car.images.length ? car.images : [{ url: "", alt_text: `${car.brand} ${car.model}` }];
  let imageIndex = 0;
  elements.carDialogContent.innerHTML = `
    <div class="car-gallery">
      <img alt="${escapeHtml(images[0].alt_text || `${car.brand} ${car.model}`)}">
      <span class="gallery-count">1 / ${images.length}</span>
      ${images.length > 1 ? '<div class="gallery-nav"><button type="button" data-prev aria-label="Предыдущее фото">←</button><button type="button" data-next aria-label="Следующее фото">→</button></div>' : ""}
    </div>
    <div class="car-detail">
      <div class="car-detail__top">
        <div><p class="eyebrow">${escapeHtml(locationLabel(car.location))} · ${car.year}</p><h2 id="car-dialog-title">${escapeHtml(car.brand)} ${escapeHtml(car.model)}</h2></div>
        <button class="favorite-button ${state.favorites.has(car.id) ? "is-active" : ""}" type="button" data-detail-favorite>${state.favorites.has(car.id) ? "♥" : "♡"}</button>
      </div>
      <p class="car-detail__price">${formatRub(car.price)}</p>
      <dl class="detail-specs">
        <div><dt>Пробег</dt><dd>${car.mileage.toLocaleString("ru-RU")} км</dd></div>
        <div><dt>Кузов</dt><dd>${escapeHtml(car.body)}</dd></div>
        <div><dt>Привод</dt><dd>${escapeHtml(car.drive)}</dd></div>
        <div><dt>Двигатель</dt><dd>${escapeHtml(car.engine)}</dd></div>
        <div><dt>Мощность</dt><dd>${escapeHtml(car.power)}</dd></div>
        <div><dt>Статус</dt><dd>${escapeHtml(locationLabel(car.location))}</dd></div>
      </dl>
      <p class="car-detail__description">${escapeHtml(car.description)}</p>
      <button class="primary-button" type="button" data-discuss>Обсудить с менеджером <span>→</span></button>
    </div>
  `;
  const galleryImage = elements.carDialogContent.querySelector(".car-gallery img");
  const galleryCount = elements.carDialogContent.querySelector(".gallery-count");
  const showImage = () => {
    galleryImage.src = images[imageIndex].url;
    galleryImage.alt = images[imageIndex].alt_text || `${car.brand} ${car.model}`;
    galleryCount.textContent = `${imageIndex + 1} / ${images.length}`;
  };
  elements.carDialogContent.querySelector("[data-prev]")?.addEventListener("click", () => {
    imageIndex = (imageIndex - 1 + images.length) % images.length;
    showImage();
  });
  elements.carDialogContent.querySelector("[data-next]")?.addEventListener("click", () => {
    imageIndex = (imageIndex + 1) % images.length;
    showImage();
  });
  elements.carDialogContent.querySelector("[data-detail-favorite]").addEventListener("click", () => {
    toggleFavorite(car.id);
    elements.carDialog.close();
    openCar(car.id);
  });
  elements.carDialogContent.querySelector("[data-discuss]").addEventListener("click", () => openLead("car", car));
  showImage();
  elements.carDialog.showModal();
}

function fillTelegramUser() {
  const user = telegram?.initDataUnsafe?.user;
  if (!user) return;
  elements.leadForm.elements.name.value = [user.first_name, user.last_name].filter(Boolean).join(" ");
  elements.leadForm.elements.username.value = user.username ? `@${user.username}` : "";
}

function openLead(type, car = null) {
  if (elements.carDialog.open) elements.carDialog.close();
  elements.leadForm.reset();
  fillTelegramUser();
  elements.leadForm.elements.lead_type.value = type;
  elements.leadForm.elements.car_id.value = car?.id || "";
  const comment = elements.leadForm.elements.comment;
  comment.required = type === "manager";
  comment.placeholder = type === "manager"
    ? "Например: семейный кроссовер до 5 млн ₽"
    : "Комплектация, цвет и другие пожелания";
  comment.closest("label").querySelector("small").textContent = type === "manager" ? "обязательно" : "необязательно";
  elements.carInterest.value = car ? `${car.brand} ${car.model} (${car.year})` : "Нужна помощь с выбором";
  elements.leadKicker.textContent = type === "car" ? locationLabel(car.location) : "Персональный подбор";
  elements.leadTitle.textContent = type === "car" ? "Обсудить автомобиль" : "Подобрать автомобиль";
  elements.leadDescription.textContent = type === "car"
    ? `${car.brand} ${car.model} уже добавлен в заявку. Оставьте контакты.`
    : "Опишите задачу — менеджер предложит подходящие варианты.";
  elements.leadDialog.showModal();
}

function resetFilters() {
  Object.assign(state, {
    search: "", brand: "", maxPrice: "", minYear: "", maxMileage: "",
    body: "", drive: "",
  });
  [elements.search, elements.brand, elements.price, elements.year, elements.mileage, elements.body, elements.drive]
    .forEach((field) => { field.value = ""; });
  render();
}

const engineRate = (engineCc, brackets) => brackets.find(([limit]) => engineCc <= limit)?.[1] ?? brackets.at(-1)[1];
function calculateDutyEur(priceEur, age, engineCc) {
  if (age === "under_3") {
    const brackets = [
      [8_500, .54, 2.5], [16_700, .48, 3.5], [42_300, .48, 5.5],
      [84_500, .48, 7.5], [169_000, .48, 15], [Infinity, .48, 20],
    ];
    const [, percent, minPerCc] = brackets.find(([limit]) => priceEur <= limit);
    return Math.max(priceEur * percent, engineCc * minPerCc);
  }
  if (age === "3_to_5") {
    return engineCc * engineRate(engineCc, [[1000, 1.5], [1500, 1.7], [1800, 2.5], [2300, 2.7], [3000, 3], [10000, 3.6]]);
  }
  return engineCc * engineRate(engineCc, [[1000, 3], [1500, 3.2], [1800, 3.5], [2300, 4.8], [3000, 5], [10000, 5.7]]);
}

elements.calculatorForm.addEventListener("submit", (event) => {
  event.preventDefault();
  if (!elements.calculatorForm.reportValidity()) return;
  const values = Object.fromEntries(new FormData(elements.calculatorForm));
  const priceRub = Number(values.price);
  const eurRate = 100;
  const dutyRub = calculateDutyEur(priceRub / eurRate, values.age, Math.round(Number(values.engine) * 1000)) * eurRate;
  const total = priceRub + dutyRub + 450_000;
  elements.calculationResult.innerHTML = `
    <h3>${formatRub(total)}</h3>
    <dl><dt>Автомобиль</dt><dd>${formatRub(priceRub)}</dd><dt>Таможенная пошлина</dt><dd>${formatRub(dutyRub)}</dd><dt>Доставка и расходы</dt><dd>${formatRub(450_000)}</dd></dl>
    <p>Предварительный расчёт по условному курсу 1 € = ${eurRate} ₽. Точную стоимость уточнит менеджер.</p>
  `;
  elements.calculationResult.hidden = false;
});

elements.leadForm.addEventListener("submit", (event) => {
  event.preventDefault();
  if (!elements.leadForm.reportValidity()) return;
  const lead = Object.fromEntries(new FormData(elements.leadForm));
  Object.keys(lead).forEach((key) => { lead[key] = lead[key].trim(); });
  if (lead.name.length < 2 || lead.phone.replace(/\D/g, "").length < 10) {
    showToast("Проверьте имя и номер телефона");
    return;
  }
  if (!telegram) {
    showToast("Для отправки откройте Web App внутри Telegram");
    return;
  }
  const submit = elements.leadForm.querySelector("[type='submit']");
  submit.disabled = true;
  submit.firstChild.textContent = "Отправляем ";
  telegram.sendData(JSON.stringify(lead));
});

elements.search.addEventListener("input", (event) => { state.search = event.target.value; render(); });
elements.brand.addEventListener("change", (event) => { state.brand = event.target.value; render(); });
elements.price.addEventListener("input", (event) => { state.maxPrice = event.target.value; render(); });
elements.year.addEventListener("input", (event) => { state.minYear = event.target.value; render(); });
elements.mileage.addEventListener("input", (event) => { state.maxMileage = event.target.value; render(); });
elements.body.addEventListener("change", (event) => { state.body = event.target.value; render(); });
elements.drive.addEventListener("change", (event) => { state.drive = event.target.value; render(); });
elements.sort.addEventListener("change", (event) => { state.sort = event.target.value; render(); });
elements.filtersButton.addEventListener("click", () => {
  elements.filtersPanel.hidden = !elements.filtersPanel.hidden;
  elements.filtersButton.setAttribute("aria-expanded", String(!elements.filtersPanel.hidden));
});
elements.favoriteHead.addEventListener("click", openFavorites);
document.querySelectorAll("[data-location]").forEach((button) => button.addEventListener("click", () => {
  state.location = button.dataset.location;
  render();
}));
document.querySelectorAll("[data-location-jump]").forEach((button) => button.addEventListener("click", () => {
  state.location = button.dataset.locationJump;
  document.querySelector("#catalog").scrollIntoView({ behavior: "smooth" });
  render();
}));
document.querySelectorAll("[data-view]").forEach((button) => button.addEventListener("click", () => {
  state.view = button.dataset.view;
  sessionStorage.setItem("dealer-auto-view", state.view);
  render();
}));
document.querySelector("#reset-filters").addEventListener("click", resetFilters);
document.querySelector("[data-reset]").addEventListener("click", resetFilters);
document.querySelector("[data-close-car]").addEventListener("click", () => elements.carDialog.close());
document.querySelector("[data-close-lead]").addEventListener("click", () => elements.leadDialog.close());
document.querySelectorAll("[data-close-favorites]").forEach((button) => {
  button.addEventListener("click", () => elements.favoritesDialog.close());
});
document.querySelector("[data-open-manager]").addEventListener("click", () => openLead("manager"));
document.querySelectorAll("[data-placeholder]").forEach((button) => {
  button.addEventListener("click", () => showToast(button.dataset.placeholder));
});
[elements.favoritesDialog, elements.carDialog, elements.leadDialog].forEach((dialog) => {
  dialog.addEventListener("click", (event) => {
    if (event.target === dialog) dialog.close();
  });
});

async function loadCatalog() {
  try {
    const response = await fetch("/api/cars", { headers: { Accept: "application/json" } });
    if (!response.ok) throw new Error("catalog unavailable");
    const data = await response.json();
    state.cars = Array.isArray(data.cars) ? data.cars : [];
    const validIds = new Set(state.cars.map((car) => car.id));
    state.favorites = new Set([...state.favorites].filter((id) => validIds.has(id)));
    persistFavorites();
    fillSelect(elements.brand, state.cars.map((car) => car.brand));
    fillSelect(elements.body, state.cars.map((car) => car.body));
    fillSelect(elements.drive, state.cars.map((car) => car.drive));
    const heroCar = state.cars.find((car) => firstImage(car));
    if (heroCar) elements.heroImage.src = firstImage(heroCar);
    render();
    if (elements.favoritesDialog.open) renderFavorites();
  } catch (_error) {
    elements.resultCount.textContent = "Каталог недоступен";
    elements.empty.hidden = false;
    elements.empty.querySelector("h3").textContent = "Не удалось загрузить каталог";
    elements.empty.querySelector("p").textContent = "Попробуйте открыть приложение ещё раз.";
  }
}

fillTelegramUser();
loadCatalog();
