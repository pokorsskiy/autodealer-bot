// Инициализация Telegram Web App SDK
const tg = window.Telegram.WebApp;
tg.ready();
tg.expand();

// Настройка стилей в соответствии с Telegram-темой
document.documentElement.style.setProperty('--bg-color', tg.themeParams.bg_color || '#0b0f19');
document.documentElement.style.setProperty('--text-color', tg.themeParams.text_color || '#f3f4f6');
document.documentElement.style.setProperty('--hint-color', tg.themeParams.hint_color || '#9ca3af');
document.documentElement.style.setProperty('--link-color', tg.themeParams.link_color || '#60a5fa');
document.documentElement.style.setProperty('--button-color', tg.themeParams.button_color || '#3b82f6');
document.documentElement.style.setProperty('--button-text-color', tg.themeParams.button_text_color || '#ffffff');
document.documentElement.style.setProperty('--secondary-bg-color', tg.themeParams.secondary_bg_color || '#1e293b');

// Константы для расчета калькулятора (презентационные данные)
const EXCHANGE_RATE_USD = 92.5; // Курс USD/RUB
const EXCHANGE_RATE_EUR = 100.2; // Курс EUR/RUB

const LOGISTICS_COSTS = {
    kr: 2200, // Доставка из Кореи в USD
    cn: 2500, // Доставка из Китая в USD
    ae: 2800  // Доставка из ОАЭ в USD
};

const OUR_COMMISSION = 120000; // Наша комиссия в рублях

// Функция переключения вкладок
function switchTab(tabId) {
    // Скрываем все вкладки
    document.querySelectorAll('.tab-panel').forEach(panel => {
        panel.classList.remove('active');
    });
    
    // Показываем нужную вкладку
    const activePanel = document.getElementById(`tab-${tabId}`);
    if (activePanel) {
        activePanel.classList.add('active');
        // Прокручиваем наверх при смене вкладки
        window.scrollTo({ top: 0, behavior: 'smooth' });
    }

    // Обновляем активный элемент навигации
    document.querySelectorAll('.nav-item').forEach(item => {
        item.classList.remove('active');
    });

    const activeNavItem = document.getElementById(`nav-${tabId}`);
    if (activeNavItem) {
        activeNavItem.classList.add('active');
    }

    // Если переключились на калькулятор, пересчитываем
    if (tabId === 'calculator') {
        calculate();
    }
}

// Выбор автомобиля из каталога
function selectCarForCalc(carName, priceUsd, countryCode) {
    document.getElementById('calc-country').value = countryCode;
    document.getElementById('calc-price-foreign').value = priceUsd;
    
    // Задаем примерный объем двигателя в зависимости от авто
    if (carName.includes('BMW X5')) {
        document.getElementById('calc-engine').value = 3000;
    } else if (carName.includes('Palisade')) {
        document.getElementById('calc-engine').value = 2200;
    } else {
        document.getElementById('calc-engine').value = 2000;
    }
    
    // Переключаемся на калькулятор и рассчитываем
    switchTab('calculator');
}

// Интерактивный расчет в калькуляторе
function calculate() {
    const country = document.getElementById('calc-country').value;
    const priceUsd = parseFloat(document.getElementById('calc-price-foreign').value) || 0;
    const engineVolume = parseFloat(document.getElementById('calc-engine').value) || 0;
    const engineType = document.getElementById('calc-type').value;

    // 1. Перевод стоимости авто в рубли
    const carRub = priceUsd * EXCHANGE_RATE_USD;

    // 2. Расчет логистики и доставки в рублях
    const logisticsUsd = LOGISTICS_COSTS[country] || 2500;
    const logisticsRub = logisticsUsd * EXCHANGE_RATE_USD;

    // 3. Расчет таможенной пошлины (упрощенная единая формула для физлиц на авто 3-5 лет)
    // Ставка зависит от объема двигателя
    let dutyPerCc = 2.5; // по умолчанию в EUR
    if (engineVolume < 1000) dutyPerCc = 1.5;
    else if (engineVolume >= 1000 && engineVolume < 1500) dutyPerCc = 1.7;
    else if (engineVolume >= 1500 && engineVolume < 1800) dutyPerCc = 2.5;
    else if (engineVolume >= 1800 && engineVolume < 2300) dutyPerCc = 2.7;
    else if (engineVolume >= 2300 && engineVolume < 3000) dutyPerCc = 3.0;
    else dutyPerCc = 5.5;

    // Если электромобиль, пошлина считается от стоимости (15% от стоимости)
    let customsDutyRub = 0;
    if (engineType === 'electric') {
        customsDutyRub = carRub * 0.15;
    } else {
        customsDutyRub = (engineVolume * dutyPerCc) * EXCHANGE_RATE_EUR;
    }

    // Утильсбор для физлиц (3 400 руб) + таможенные сборы (~8 000 руб)
    const extraCustomsFees = 3400 + 8000;
    const totalDutyAndFeesRub = customsDutyRub + extraCustomsFees;

    // 4. Итоговая стоимость
    const totalPriceRub = carRub + logisticsRub + totalDutyAndFeesRub + OUR_COMMISSION;

    // Вывод результатов на страницу
    document.getElementById('total-price').innerText = Math.round(totalPriceRub).toLocaleString('ru-RU') + ' ₽';
    document.getElementById('val-car-usd').innerText = '$' + priceUsd.toLocaleString('en-US');
    document.getElementById('val-car-rub').innerText = Math.round(carRub).toLocaleString('ru-RU') + ' ₽';
    document.getElementById('val-delivery').innerText = Math.round(logisticsRub).toLocaleString('ru-RU') + ' ₽';
    document.getElementById('val-duty').innerText = Math.round(totalDutyAndFeesRub).toLocaleString('ru-RU') + ' ₽';
    document.getElementById('val-commission').innerText = OUR_COMMISSION.toLocaleString('ru-RU') + ' ₽';
}

// Применить расчет и перейти на форму заявки
function applyFromCalc() {
    const countryText = document.getElementById('calc-country').options[document.getElementById('calc-country').selectedIndex].text;
    const priceUsd = document.getElementById('calc-price-foreign').value;
    const engineVolume = document.getElementById('calc-engine').value;
    
    const interestText = `Расчет: Авто ${priceUsd}$ (${countryText}, ${engineVolume}cc)`;
    
    document.getElementById('lead-interest').value = interestText;
    
    // Переключаемся на форму лида
    switchTab('lead');
}

// Выбор конкретного тарифа
function selectTariff(tariffName, cardId) {
    // Подсвечиваем карточку тарифа
    document.querySelectorAll('.tariff-card').forEach(card => {
        card.classList.remove('selected-active');
    });
    const selectedCard = document.getElementById(cardId);
    if (selectedCard) {
        selectedCard.classList.add('selected-active');
    }

    // Записываем тариф в форму
    document.getElementById('lead-interest').value = `Тариф «${tariffName}»`;

    // Переключаемся на форму лида через 300мс для плавности
    setTimeout(() => {
        switchTab('lead');
    }, 300);
}

// Отправка формы в Telegram бот
function submitForm(event) {
    event.preventDefault();

    const name = document.getElementById('lead-name').value.trim();
    const phone = document.getElementById('lead-phone').value.trim();
    const interest = document.getElementById('lead-interest').value || 'Общий интерес к боту';
    const notes = document.getElementById('lead-notes').value.trim();

    // Простая валидация номера телефона
    const phoneDigits = phone.replace(/\D/g, '');
    if (phoneDigits.length < 7) {
        tg.showAlert("Пожалуйста, введите корректный номер телефона.");
        return;
    }

    const payload = {
        name: name,
        phone: phone,
        interest: interest,
        notes: notes
    };

    // Отправляем данные обратно в Telegram-бот
    tg.sendData(JSON.stringify(payload));
}

// Инициализация при загрузке страницы
window.addEventListener('DOMContentLoaded', () => {
    // Запускаем расчет при открытии страницы
    calculate();
});
