const state = {
  cars: [],
  selectedId: null,
  role: document.querySelector(".admin-shell").dataset.role,
  csrf: document.querySelector('meta[name="csrf-token"]').content,
};

const elements = {
  list: document.querySelector("#admin-car-list"),
  search: document.querySelector("#admin-search"),
  empty: document.querySelector("#editor-empty"),
  form: document.querySelector("#car-form"),
  title: document.querySelector("#editor-title"),
  kicker: document.querySelector("#editor-kicker"),
  deleteCar: document.querySelector("#delete-car"),
  photosSection: document.querySelector("#photos-section"),
  photoList: document.querySelector("#photo-list"),
  photoUpload: document.querySelector("#photo-upload"),
  usersDialog: document.querySelector("#users-dialog"),
  usersList: document.querySelector("#users-list"),
  userForm: document.querySelector("#user-form"),
  toast: document.querySelector("#admin-toast"),
};

let toastTimer;
function showToast(message) {
  clearTimeout(toastTimer);
  elements.toast.textContent = message;
  elements.toast.classList.add("is-visible");
  toastTimer = setTimeout(() => elements.toast.classList.remove("is-visible"), 3000);
}

async function api(url, options = {}) {
  const headers = new Headers(options.headers || {});
  headers.set("Accept", "application/json");
  if (options.method && options.method !== "GET") headers.set("X-CSRF-Token", state.csrf);
  if (options.body && !(options.body instanceof FormData)) headers.set("Content-Type", "application/json");
  const response = await fetch(url, { ...options, headers });
  if (response.status === 401) {
    window.location.assign("/admin/login");
    throw new Error("Сессия завершена");
  }
  if (!response.ok) {
    const body = await response.json().catch(() => ({}));
    throw new Error(body.error || "Не удалось выполнить действие");
  }
  return response.status === 204 ? null : response.json();
}

function currentCar() {
  return state.cars.find((car) => car.id === state.selectedId);
}

function renderList() {
  const query = elements.search.value.trim().toLowerCase();
  const cars = state.cars.filter((car) => `${car.brand} ${car.model}`.toLowerCase().includes(query));
  elements.list.replaceChildren(...cars.map((car) => {
    const button = document.createElement("button");
    button.type = "button";
    button.className = `admin-car ${car.id === state.selectedId ? "is-active" : ""}`;
    const image = document.createElement("img");
    image.src = car.images[0]?.url || "";
    image.alt = "";
    const text = document.createElement("span");
    const title = document.createElement("b");
    title.textContent = `${car.brand} ${car.model}`;
    const meta = document.createElement("small");
    meta.textContent = `${car.year} · ${car.location === "port" ? "В порту" : "В городе"}`;
    text.append(title, meta);
    const visibility = document.createElement("i");
    visibility.className = `visibility ${car.is_visible ? "is-visible" : ""}`;
    button.append(image, text, visibility);
    button.addEventListener("click", () => selectCar(car.id));
    return button;
  }));
}

function formData() {
  const data = Object.fromEntries(new FormData(elements.form));
  return {
    ...data,
    year: Number(data.year),
    price: Number(data.price),
    mileage: Number(data.mileage),
    sort_order: Number(data.sort_order),
    is_visible: elements.form.elements.is_visible.checked,
  };
}

function showEditor() {
  elements.empty.hidden = true;
  elements.form.hidden = false;
}

function newCar() {
  state.selectedId = null;
  showEditor();
  elements.form.reset();
  elements.form.elements.original_id.value = "";
  elements.form.elements.sort_order.value = "0";
  elements.form.elements.is_visible.checked = true;
  elements.form.elements.id.disabled = false;
  elements.title.textContent = "Новый автомобиль";
  elements.kicker.textContent = "Создание карточки";
  elements.photosSection.hidden = true;
  elements.deleteCar.hidden = true;
  renderList();
  elements.form.elements.id.focus();
}

function selectCar(carId) {
  const car = state.cars.find((item) => item.id === carId);
  if (!car) return;
  state.selectedId = carId;
  showEditor();
  elements.form.reset();
  Object.entries(car).forEach(([key, value]) => {
    if (elements.form.elements[key] && key !== "is_visible") elements.form.elements[key].value = value;
  });
  elements.form.elements.original_id.value = car.id;
  elements.form.elements.id.value = car.id;
  elements.form.elements.id.disabled = true;
  elements.form.elements.is_visible.checked = car.is_visible;
  elements.title.textContent = `${car.brand} ${car.model}`;
  elements.kicker.textContent = car.location === "port" ? "В порту" : "В городе";
  elements.photosSection.hidden = false;
  elements.deleteCar.hidden = state.role !== "owner";
  renderPhotos(car);
  renderList();
}

function renderPhotos(car) {
  elements.photoList.replaceChildren(...car.images.map((photo, index) => {
    const card = document.createElement("div");
    card.className = "photo";
    const image = document.createElement("img");
    image.src = photo.url;
    image.alt = photo.alt_text || `${car.brand} ${car.model}`;
    const order = document.createElement("span");
    order.className = "photo-order";
    order.textContent = `Фото ${index + 1}`;
    const remove = document.createElement("button");
    remove.type = "button";
    remove.textContent = "×";
    remove.setAttribute("aria-label", "Удалить фотографию");
    remove.addEventListener("click", async () => {
      if (!confirm("Удалить эту фотографию?")) return;
      try {
        await api(`/api/admin/images/${photo.id}`, { method: "DELETE" });
        await loadCars(car.id);
        showToast("Фотография удалена");
      } catch (error) { showToast(error.message); }
    });
    card.append(image, order, remove);
    return card;
  }));
}

async function loadCars(selectId = state.selectedId) {
  const data = await api("/api/admin/cars");
  state.cars = data.cars;
  renderList();
  if (selectId && state.cars.some((car) => car.id === selectId)) selectCar(selectId);
}

elements.form.addEventListener("submit", async (event) => {
  event.preventDefault();
  if (!elements.form.reportValidity()) return;
  const data = formData();
  const originalId = elements.form.elements.original_id.value;
  try {
    const result = await api(
      originalId ? `/api/admin/cars/${encodeURIComponent(originalId)}` : "/api/admin/cars",
      { method: originalId ? "PUT" : "POST", body: JSON.stringify(data) },
    );
    const carId = result.car.id;
    await loadCars(carId);
    showToast("Карточка сохранена");
  } catch (error) { showToast(error.message); }
});

elements.deleteCar.addEventListener("click", async () => {
  const car = currentCar();
  if (!car || !confirm(`Удалить ${car.brand} ${car.model} без возможности восстановления?`)) return;
  try {
    await api(`/api/admin/cars/${encodeURIComponent(car.id)}`, { method: "DELETE" });
    state.selectedId = null;
    elements.form.hidden = true;
    elements.empty.hidden = false;
    await loadCars();
    showToast("Автомобиль удалён");
  } catch (error) { showToast(error.message); }
});

elements.photoUpload.addEventListener("change", async () => {
  const car = currentCar();
  const file = elements.photoUpload.files[0];
  if (!car || !file) return;
  const data = new FormData();
  data.append("image", file);
  try {
    await api(`/api/admin/cars/${encodeURIComponent(car.id)}/images`, { method: "POST", body: data });
    elements.photoUpload.value = "";
    await loadCars(car.id);
    showToast("Фотография загружена");
  } catch (error) { showToast(error.message); }
});

async function loadUsers() {
  const data = await api("/api/admin/users");
  elements.usersList.replaceChildren(...data.users.map((user) => {
    const row = document.createElement("div");
    row.className = "user-row";
    const text = document.createElement("span");
    const name = document.createElement("b");
    name.textContent = user.username;
    const status = document.createElement("small");
    status.textContent = user.is_active ? "Доступ активен" : "Доступ отключён";
    text.append(name, status);
    const role = document.createElement("select");
    role.add(new Option("Менеджер", "manager"));
    role.add(new Option("Владелец", "owner"));
    role.value = user.role;
    const toggle = document.createElement("button");
    toggle.type = "button";
    toggle.textContent = user.is_active ? "Отключить" : "Включить";
    toggle.addEventListener("click", async () => {
      try {
        await api(`/api/admin/users/${user.id}`, {
          method: "PUT",
          body: JSON.stringify({ role: role.value, is_active: !user.is_active }),
        });
        await loadUsers();
      } catch (error) { showToast(error.message); }
    });
    role.addEventListener("change", async () => {
      try {
        await api(`/api/admin/users/${user.id}`, {
          method: "PUT",
          body: JSON.stringify({ role: role.value, is_active: user.is_active }),
        });
        await loadUsers();
      } catch (error) { showToast(error.message); }
    });
    row.append(text, role, toggle);
    return row;
  }));
}

document.querySelector("#new-car").addEventListener("click", newCar);
elements.search.addEventListener("input", renderList);
document.querySelector("#open-users")?.addEventListener("click", async () => {
  try {
    await loadUsers();
    elements.usersDialog.showModal();
  } catch (error) { showToast(error.message); }
});
document.querySelector("[data-close-users]")?.addEventListener("click", () => elements.usersDialog.close());
elements.userForm?.addEventListener("submit", async (event) => {
  event.preventDefault();
  if (!elements.userForm.reportValidity()) return;
  const data = Object.fromEntries(new FormData(elements.userForm));
  try {
    await api("/api/admin/users", { method: "POST", body: JSON.stringify(data) });
    elements.userForm.reset();
    await loadUsers();
    showToast("Пользователь создан");
  } catch (error) { showToast(error.message); }
});

loadCars().catch((error) => showToast(error.message));
