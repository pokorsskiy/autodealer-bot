const telegram = window.Telegram?.WebApp;

const cars = [
  {
    id: "toyota-camry-2024",
    brand: "Toyota",
    model: "Camry",
    year: 2024,
    price: 3_850_000,
    mileage: 8_000,
    body: "Седан",
    drive: "Передний",
    engine: "2.5 л · бензин",
    power: "203 л.с.",
    image: "https://di-uploads-pod10.dealerinspire.com/wilsonvilletoyota/uploads/2023/09/2024camry-1.png",
    description: "Комфортный седан для города и трассы с просторным салоном, современными ассистентами и понятной стоимостью владения."
  },
  {
    id: "bmw-x5-2023",
    brand: "BMW",
    model: "X5",
    year: 2023,
    price: 8_900_000,
    mileage: 24_000,
    body: "Кроссовер",
    drive: "Полный",
    engine: "3.0 л · дизель",
    power: "298 л.с.",
    image: "https://cdn.bimmertoday.de/wp-content/uploads/2023/02/2023-BMW-X5-Facelift-G05-LCI-xLine-Blue-Ridge-Mountain-xDrive50e-42.jpg",
    description: "Премиальный кроссовер с полным приводом, выразительной динамикой и высоким уровнем комфорта для дальних поездок."
  },
  {
    id: "geely-monjaro-2025",
    brand: "Geely",
    model: "Monjaro",
    year: 2025,
    price: 4_650_000,
    mileage: 2_000,
    body: "Кроссовер",
    drive: "Полный",
    engine: "2.0 л · бензин",
    power: "238 л.с.",
    image: "https://www.geely.com/-/media/project/web-portal/models/new-monjaro/360-colors/green/green-0.png?h=535&hash=34D9485C11C1E9A5058F48381468D19A&iar=0&w=1500",
    description: "Современный семейный кроссовер с просторным салоном, полным приводом и богатым набором электронных помощников."
  },
  {
    id: "audi-q5-2023",
    brand: "Audi",
    model: "Q5",
    year: 2023,
    price: 7_450_000,
    mileage: 31_000,
    body: "Кроссовер",
    drive: "Полный",
    engine: "2.0 л · бензин",
    power: "265 л.с.",
    image: "https://images3.kingautos.net/spec/2023/01/kZ6Ro5Oeop2RnpGgmco.webp",
    description: "Сбалансированный премиальный кроссовер с quattro, качественным интерьером и удобным размером для ежедневной эксплуатации."
  },
  {
    id: "kia-sorento-2024",
    brand: "Kia",
    model: "Sorento",
    year: 2024,
    price: 5_300_000,
    mileage: 12_000,
    body: "Внедорожник",
    drive: "Полный",
    engine: "2.5 л · бензин",
    power: "281 л.с.",
    image: "https://www.kiamedia.com/image/landing/21417/1/2/21773?v=3",
    description: "Практичный семиместный автомобиль для семьи, путешествий и повседневных задач с продуманным пространством салона."
  },
  {
    id: "toyota-camry-2022",
    brand: "Toyota",
    model: "Camry Prestige",
    year: 2022,
    price: 3_300_000,
    mileage: 54_000,
    body: "Седан",
    drive: "Передний",
    engine: "2.5 л · бензин",
    power: "200 л.с.",
    image: "https://di-uploads-pod10.dealerinspire.com/wilsonvilletoyota/uploads/2023/09/2024camry-1.png",
    description: "Проверенный седан в богатой комплектации: хорошая ликвидность, комфортная подвеска и привычная эргономика."
  }
];

const state = {
  search: "",
  brand: "",
  maxPrice: "",
  minYear: "",
  maxMileage: "",
  body: "",
  drive: "",
  sort: "default",
  favoritesOnly: false,
  favorites: new Set(JSON.parse(sessionStorage.getItem("dealer-auto-favorites") || "[]"))
};

const elements = {
  list: document.querySelector("#car-list"),
  empty: document.querySelector("#empty-state"),
  resultCount: document.querySelector("#result-count"),
  favoriteCount: document.querySelector("#favorite-count"),
  activeFilterCount: document.querySelector("#active-filter-count"),
  search: document.querySelector("#search"),
  brand: document.querySelector("#brand-filter"),
  price: document.querySelector("#price-filter"),
  year: document.querySelector("#year-filter"),
  mileage: document.querySelector("#mileage-filter"),
  body: document.querySelector("#body-filter"),
  drive: document.querySelector("#drive-filter"),
  sort: document.querySelector("#sort"),
  favoriteFilter: document.querySelector("#favorite-filter"),
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
  toast: document.querySelector("#toast")
};

if (telegram) {
  telegram.ready();
  telegram.expand();
  telegram.setHeaderColor?.("#f7f1eb");
  telegram.setBackgroundColor?.("#f8f4ef");

  const user = telegram.initDataUnsafe?.user;
  if (user) {
    const fullName = [user.first_name, user.last_name].filter(Boolean).join(" ");
    elements.leadForm.elements.name.value = fullName;
    elements.leadForm.elements.username.value = user.username ? `@${user.username}` : "";
  }
}

const formatRub = (value) => `${Math.round(value).toLocaleString("ru-RU")} ₽`;
const pluralCars = (count) => {
  const mod10 = count % 10;
  const mod100 = count % 100;
  if (mod10 === 1 && mod100 !== 11) return `${count} автомобиль`;
  if ([2, 3, 4].includes(mod10) && ![12, 13, 14].includes(mod100)) return `${count} автомобиля`;
  return `${count} автомобилей`;
};

let toastTimer;
const showToast = (message) => {
  window.clearTimeout(toastTimer);
  elements.toast.textContent = message;
  elements.toast.classList.add("is-visible");
  toastTimer = window.setTimeout(() => elements.toast.classList.remove("is-visible"), 2800);
};

const persistFavorites = () => {
  sessionStorage.setItem("dealer-auto-favorites", JSON.stringify([...state.favorites]));
};

const filteredCars = () => {
  const query = state.search.trim().toLocaleLowerCase("ru");
  const filtered = cars.filter((car) => {
    const matchesSearch = !query || `${car.brand} ${car.model}`.toLocaleLowerCase("ru").includes(query);
    return matchesSearch
      && (!state.brand || car.brand === state.brand)
      && (!state.maxPrice || car.price <= Number(state.maxPrice))
      && (!state.minYear || car.year >= Number(state.minYear))
      && (!state.maxMileage || car.mileage <= Number(state.maxMileage))
      && (!state.body || car.body === state.body)
      && (!state.drive || car.drive === state.drive)
      && (!state.favoritesOnly || state.favorites.has(car.id));
  });

  return filtered.sort((a, b) => {
    if (state.sort === "price-asc") return a.price - b.price;
    if (state.sort === "price-desc") return b.price - a.price;
    if (state.sort === "year-asc") return a.year - b.year;
    if (state.sort === "year-desc") return b.year - a.year;
    return 0;
  });
};

const carCard = (car) => {
  const article = document.createElement("article");
  article.className = "car-card";
  article.innerHTML = `
    <button class="favorite-button ${state.favorites.has(car.id) ? "is-active" : ""}" type="button" aria-label="Добавить ${car.brand} ${car.model} в избранное" aria-pressed="${state.favorites.has(car.id)}">♡</button>
    <img class="car-card__image" src="${car.image}" alt="${car.brand} ${car.model}, ${car.year}" loading="lazy">
    <button class="car-card__content button-reset" type="button" aria-label="Открыть ${car.brand} ${car.model}">
      <span class="car-card__brand">${car.brand}</span>
      <span class="car-card__title">${car.model}</span>
      <span class="car-card__meta">${car.year} · ${car.mileage.toLocaleString("ru-RU")} км · ${car.drive} привод</span>
      <span class="car-card__price">${formatRub(car.price)}</span>
    </button>
  `;
  article.querySelector(".favorite-button").addEventListener("click", () => toggleFavorite(car.id));
  article.querySelector(".car-card__content").addEventListener("click", () => openCar(car.id));
  article.querySelector("img").addEventListener("error", (event) => {
    event.currentTarget.removeAttribute("src");
    event.currentTarget.alt = `Фотография ${car.brand} ${car.model} временно недоступна`;
  });
  return article;
};

const render = () => {
  const visibleCars = filteredCars();
  elements.list.replaceChildren(...visibleCars.map(carCard));
  elements.empty.hidden = visibleCars.length > 0;
  elements.resultCount.textContent = pluralCars(visibleCars.length);
  elements.favoriteCount.textContent = `${state.favorites.size} в избранном`;
  elements.favoriteFilter.setAttribute("aria-pressed", String(state.favoritesOnly));
  elements.favoriteFilter.textContent = `${state.favoritesOnly ? "♥" : "♡"} Избранное`;
  elements.activeFilterCount.textContent = [
    state.brand, state.maxPrice, state.minYear, state.maxMileage, state.body, state.drive
  ].filter(Boolean).length;
};

const toggleFavorite = (carId) => {
  if (state.favorites.has(carId)) {
    state.favorites.delete(carId);
    showToast("Удалено из избранного");
  } else {
    state.favorites.add(carId);
    showToast("Добавлено в избранное");
  }
  persistFavorites();
  render();
};

const openCar = (carId) => {
  const car = cars.find((item) => item.id === carId);
  if (!car) return;
  elements.carDialogContent.innerHTML = `
    <img class="car-dialog__image" src="${car.image}" alt="${car.brand} ${car.model}">
    <div class="car-dialog__body">
      <p class="kicker">${car.brand} · ${car.year}</p>
      <h2 id="car-dialog-title">${car.model}</h2>
      <p class="car-dialog__price">${formatRub(car.price)}</p>
      <dl class="car-dialog__specs">
        <div><dt>Пробег</dt><dd>${car.mileage.toLocaleString("ru-RU")} км</dd></div>
        <div><dt>Кузов</dt><dd>${car.body}</dd></div>
        <div><dt>Привод</dt><dd>${car.drive}</dd></div>
        <div><dt>Двигатель</dt><dd>${car.engine}</dd></div>
        <div><dt>Мощность</dt><dd>${car.power}</dd></div>
        <div><dt>Год</dt><dd>${car.year}</dd></div>
      </dl>
      <p class="car-dialog__description">${car.description}</p>
      <button class="submit" type="button" data-select-car="${car.id}"><span>Выбрать автомобиль</span><i>↗</i></button>
    </div>
  `;
  elements.carDialogContent.querySelector("[data-select-car]").addEventListener("click", () => openLead("car", car));
  elements.carDialog.showModal();
};

const openLead = (type, car = null) => {
  if (elements.carDialog.open) elements.carDialog.close();
  elements.leadForm.reset();
  const user = telegram?.initDataUnsafe?.user;
  if (user) {
    elements.leadForm.elements.name.value = [user.first_name, user.last_name].filter(Boolean).join(" ");
    elements.leadForm.elements.username.value = user.username ? `@${user.username}` : "";
  }

  elements.leadForm.elements.lead_type.value = type;
  elements.leadForm.elements.car_id.value = car?.id || "";
  const comment = elements.leadForm.elements.comment;
  comment.required = type === "manager";
  comment.placeholder = type === "manager"
    ? "Например: нужен семейный кроссовер до 5 млн ₽"
    : "Ваши пожелания по автомобилю";
  comment.closest(".field").querySelector("small").textContent = type === "manager"
    ? "обязательно"
    : "необязательно";
  elements.carInterest.value = car ? `${car.brand} ${car.model} (${car.year})` : "Нужна помощь с выбором";
  elements.leadKicker.textContent = type === "car" ? "Выбранный автомобиль" : "Персональный подбор";
  elements.leadTitle.innerHTML = type === "car" ? "Получить<br>предложение" : "Менеджер<br>подскажет";
  elements.leadDescription.textContent = type === "car"
    ? `Заявка на ${car.brand} ${car.model}. Оставьте контакты для уточнения деталей.`
    : "Оставьте контакты и опишите задачу — менеджер предложит подходящие варианты.";
  elements.leadDialog.showModal();
};

const resetFilters = () => {
  state.search = "";
  state.brand = "";
  state.maxPrice = "";
  state.minYear = "";
  state.maxMileage = "";
  state.body = "";
  state.drive = "";
  state.favoritesOnly = false;
  elements.search.value = "";
  elements.brand.value = "";
  elements.price.value = "";
  elements.year.value = "";
  elements.mileage.value = "";
  elements.body.value = "";
  elements.drive.value = "";
  render();
};

const engineRate = (engineCc, brackets) => brackets.find(([limit]) => engineCc <= limit)?.[1] ?? brackets.at(-1)[1];
const calculateDutyEur = (priceEur, age, engineCc) => {
  if (age === "under_3") {
    const brackets = [
      [8_500, .54, 2.5], [16_700, .48, 3.5], [42_300, .48, 5.5],
      [84_500, .48, 7.5], [169_000, .48, 15], [Infinity, .48, 20]
    ];
    const [, percent, minPerCc] = brackets.find(([limit]) => priceEur <= limit);
    return Math.max(priceEur * percent, engineCc * minPerCc);
  }
  if (age === "3_to_5") {
    return engineCc * engineRate(engineCc, [[1000, 1.5], [1500, 1.7], [1800, 2.5], [2300, 2.7], [3000, 3], [10000, 3.6]]);
  }
  return engineCc * engineRate(engineCc, [[1000, 3], [1500, 3.2], [1800, 3.5], [2300, 4.8], [3000, 5], [10000, 5.7]]);
};

elements.calculatorForm.addEventListener("submit", (event) => {
  event.preventDefault();
  if (!elements.calculatorForm.reportValidity()) return;
  const values = Object.fromEntries(new FormData(elements.calculatorForm));
  const priceRub = Number(values.price);
  const engineLiters = Number(values.engine);
  const eurRate = 100;
  const dutyRub = calculateDutyEur(priceRub / eurRate, values.age, Math.round(engineLiters * 1000)) * eurRate;
  const delivery = 350_000;
  const other = 100_000;
  const total = priceRub + dutyRub + delivery + other;
  elements.calculationResult.innerHTML = `
    <h3>${formatRub(total)}</h3>
    <dl>
      <dt>Автомобиль</dt><dd>${formatRub(priceRub)}</dd>
      <dt>Таможенная пошлина</dt><dd>${formatRub(dutyRub)}</dd>
      <dt>Доставка</dt><dd>${formatRub(delivery)}</dd>
      <dt>Прочие расходы</dt><dd>${formatRub(other)}</dd>
      <dt class="total">Итого ориентировочно</dt><dd class="total">${formatRub(total)}</dd>
    </dl>
    <p>Курс расчёта: 1 € = ${eurRate} ₽. Итог зависит от курса, характеристик автомобиля, утильсбора и оформления.</p>
  `;
  elements.calculationResult.hidden = false;
  elements.calculationResult.scrollIntoView({ behavior: "smooth", block: "nearest" });
});

elements.leadForm.addEventListener("submit", (event) => {
  event.preventDefault();
  if (!elements.leadForm.reportValidity()) return;
  const lead = Object.fromEntries(new FormData(elements.leadForm));
  lead.name = lead.name.trim();
  lead.phone = lead.phone.trim();
  lead.username = lead.username.trim();
  lead.comment = lead.comment.trim();

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
  submit.querySelector("span").textContent = "Отправляем…";
  telegram.sendData(JSON.stringify(lead));
});

elements.search.addEventListener("input", (event) => { state.search = event.target.value; render(); });
elements.brand.addEventListener("change", (event) => { state.brand = event.target.value; render(); });
elements.price.addEventListener("change", (event) => { state.maxPrice = event.target.value; render(); });
elements.year.addEventListener("change", (event) => { state.minYear = event.target.value; render(); });
elements.mileage.addEventListener("change", (event) => { state.maxMileage = event.target.value; render(); });
elements.body.addEventListener("change", (event) => { state.body = event.target.value; render(); });
elements.drive.addEventListener("change", (event) => { state.drive = event.target.value; render(); });
elements.sort.addEventListener("change", (event) => { state.sort = event.target.value; render(); });
elements.favoriteFilter.addEventListener("click", () => { state.favoritesOnly = !state.favoritesOnly; render(); });
document.querySelector("#reset-filters").addEventListener("click", resetFilters);
document.querySelectorAll("[data-reset-filters]").forEach((button) => button.addEventListener("click", resetFilters));
document.querySelector("[data-close-dialog]").addEventListener("click", () => elements.carDialog.close());
document.querySelector("[data-close-lead]").addEventListener("click", () => elements.leadDialog.close());
document.querySelectorAll("[data-open-manager]").forEach((button) => button.addEventListener("click", () => openLead("manager")));
document.querySelectorAll("[data-placeholder]").forEach((button) => {
  button.addEventListener("click", () => showToast(button.dataset.placeholder));
});
[elements.carDialog, elements.leadDialog].forEach((dialog) => {
  dialog.addEventListener("click", (event) => {
    if (event.target === dialog) dialog.close();
  });
});

[...new Set(cars.map((car) => car.brand))].sort().forEach((brand) => {
  elements.brand.add(new Option(brand, brand));
});

render();
