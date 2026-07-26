"""Web-сервер публичного каталога и закрытой админки."""

import hmac
import re
import secrets
import sqlite3
import time
from collections import defaultdict, deque
from functools import wraps
from pathlib import Path
from typing import Any, Callable

from flask import (
    Flask,
    abort,
    jsonify,
    redirect,
    render_template,
    request,
    send_from_directory,
    session,
    url_for,
)
from werkzeug.security import check_password_hash, generate_password_hash
from werkzeug.utils import secure_filename

from config import (
    ADMIN_PASSWORD,
    ADMIN_USERNAME,
    BASE_DIR,
    MAX_UPLOAD_MB,
    SECRET_KEY,
    SESSION_COOKIE_SECURE,
    UPLOAD_DIR,
    WEB_HOST,
    WEB_PORT,
)
from database import (
    add_car_image,
    create_admin,
    create_initial_owner,
    delete_car,
    delete_car_image,
    get_admin,
    get_admin_by_username,
    get_car,
    init_db,
    list_admins,
    list_cars,
    reorder_car_images,
    save_car,
    update_admin,
)
from logger import logger


WEB_DIR = BASE_DIR / "web"
TEMPLATES_DIR = BASE_DIR / "templates"
ALLOWED_IMAGE_EXTENSIONS = {"jpg", "jpeg", "png", "webp"}
SLUG_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
USERNAME_RE = re.compile(r"^[A-Za-z0-9_.-]{3,50}$")
ROLE_LEVEL = {"manager": 1, "owner": 2}
LOGIN_WINDOW_SECONDS = 300
LOGIN_MAX_ATTEMPTS = 5
login_attempts: dict[str, deque[float]] = defaultdict(deque)

app = Flask(__name__, template_folder=str(TEMPLATES_DIR))
app.config.update(
    SECRET_KEY=SECRET_KEY or secrets.token_hex(32),
    MAX_CONTENT_LENGTH=MAX_UPLOAD_MB * 1024 * 1024,
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE="Lax",
    SESSION_COOKIE_SECURE=SESSION_COOKIE_SECURE,
)

if not SECRET_KEY:
    logger.warning(
        "SECRET_KEY не задан: при перезапуске сервера все сессии админки завершатся"
    )


def _bootstrap() -> None:
    init_db()
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    if ADMIN_USERNAME and ADMIN_PASSWORD:
        if len(ADMIN_PASSWORD) < 12:
            logger.warning("ADMIN_PASSWORD должен содержать не менее 12 символов")
        else:
            created = create_initial_owner(
                ADMIN_USERNAME, generate_password_hash(ADMIN_PASSWORD)
            )
            if created:
                logger.info("Создан первоначальный владелец веб-админки")


def _owner_setup_error() -> str:
    admins = list_admins()
    if any(user["role"] == "owner" and user["is_active"] for user in admins):
        return ""
    if not ADMIN_USERNAME:
        return "Владелец не создан: задайте ADMIN_USERNAME в локальном .env."
    if len(ADMIN_PASSWORD) < 12:
        return (
            "Владелец не создан: ADMIN_PASSWORD должен содержать "
            "не менее 12 символов. После изменения перезапустите сервер."
        )
    return "Владелец не создан. Проверьте журнал запуска и перезапустите сервер."


def _csrf_token() -> str:
    token = session.get("csrf_token")
    if not token:
        token = secrets.token_urlsafe(32)
        session["csrf_token"] = token
    return str(token)


def _require_csrf() -> None:
    supplied = request.headers.get("X-CSRF-Token") or request.form.get("csrf_token")
    expected = session.get("csrf_token")
    if not supplied or not expected or not hmac.compare_digest(str(supplied), str(expected)):
        abort(403)


def _current_admin() -> dict[str, Any] | None:
    admin_id = session.get("admin_id")
    if not isinstance(admin_id, int):
        return None
    admin = get_admin(admin_id)
    if not admin or not admin["is_active"]:
        session.clear()
        return None
    return admin


def login_required(role: str = "manager") -> Callable:
    def decorator(handler: Callable) -> Callable:
        @wraps(handler)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            admin = _current_admin()
            if admin is None:
                if request.path.startswith("/api/admin/"):
                    return jsonify({"error": "Требуется авторизация"}), 401
                return redirect(url_for("admin_login"))
            if ROLE_LEVEL[admin["role"]] < ROLE_LEVEL[role]:
                return jsonify({"error": "Недостаточно прав"}), 403
            return handler(*args, **kwargs)

        return wrapper

    return decorator


def _json_object() -> dict[str, Any]:
    payload = request.get_json(silent=True)
    if not isinstance(payload, dict):
        abort(400)
    return payload


def _clean_text(
    payload: dict[str, Any], name: str, *, max_length: int, required: bool = True
) -> str:
    value = str(payload.get(name, "")).strip()
    if required and not value:
        raise ValueError(f"Поле «{name}» обязательно")
    if len(value) > max_length:
        raise ValueError(f"Поле «{name}» слишком длинное")
    return value


def _clean_int(
    payload: dict[str, Any], name: str, *, minimum: int, maximum: int
) -> int:
    try:
        value = int(payload.get(name))
    except (TypeError, ValueError) as error:
        raise ValueError(f"Поле «{name}» должно быть числом") from error
    if not minimum <= value <= maximum:
        raise ValueError(f"Некорректное значение поля «{name}»")
    return value


def _validate_car(payload: dict[str, Any], *, creating: bool) -> dict[str, Any]:
    car_id = _clean_text(payload, "id", max_length=80) if creating else ""
    if creating and not SLUG_RE.fullmatch(car_id):
        raise ValueError("ID: только латиница, цифры и дефисы")
    location = _clean_text(payload, "location", max_length=10)
    if location not in {"city", "port"}:
        raise ValueError("Некорректный статус автомобиля")
    return {
        "id": car_id,
        "brand": _clean_text(payload, "brand", max_length=60),
        "model": _clean_text(payload, "model", max_length=80),
        "year": _clean_int(payload, "year", minimum=1950, maximum=2100),
        "price": _clean_int(payload, "price", minimum=0, maximum=1_000_000_000),
        "mileage": _clean_int(payload, "mileage", minimum=0, maximum=10_000_000),
        "body": _clean_text(payload, "body", max_length=60),
        "drive": _clean_text(payload, "drive", max_length=60),
        "engine": _clean_text(payload, "engine", max_length=100),
        "power": _clean_text(payload, "power", max_length=60),
        "description": _clean_text(
            payload, "description", max_length=2000, required=False
        ),
        "location": location,
        "is_visible": bool(payload.get("is_visible", True)),
        "sort_order": _clean_int(
            {"sort_order": payload.get("sort_order", 0)},
            "sort_order",
            minimum=-10000,
            maximum=10000,
        ),
    }


def _remove_local_upload(url: str | None) -> None:
    if not url or not url.startswith("/uploads/"):
        return
    filename = Path(url).name
    target = (UPLOAD_DIR / filename).resolve()
    if target.parent == UPLOAD_DIR.resolve() and target.exists():
        target.unlink()


def _login_is_limited(client_key: str) -> bool:
    now = time.monotonic()
    attempts = login_attempts[client_key]
    while attempts and now - attempts[0] > LOGIN_WINDOW_SECONDS:
        attempts.popleft()
    return len(attempts) >= LOGIN_MAX_ATTEMPTS


def _record_failed_login(client_key: str) -> None:
    login_attempts[client_key].append(time.monotonic())


def _valid_image_signature(image) -> bool:
    header = image.stream.read(16)
    image.stream.seek(0)
    return (
        header.startswith(b"\xff\xd8\xff")
        or header.startswith(b"\x89PNG\r\n\x1a\n")
        or (header.startswith(b"RIFF") and header[8:12] == b"WEBP")
    )


@app.after_request
def security_headers(response):
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "SAMEORIGIN"
    response.headers["Referrer-Policy"] = "same-origin"
    response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
    response.headers["Content-Security-Policy"] = (
        "default-src 'self'; "
        "script-src 'self' https://telegram.org; "
        "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
        "font-src https://fonts.gstatic.com; "
        "img-src 'self' https: data:; "
        "connect-src 'self'; "
        "object-src 'none'; base-uri 'self'; form-action 'self'"
    )
    if request.path.startswith("/api/") or request.path.startswith("/admin"):
        response.headers["Cache-Control"] = "no-store"
    elif request.path.endswith((".html", ".css", ".js")) or request.path == "/":
        response.headers["Cache-Control"] = "no-cache"
    return response


@app.get("/")
def webapp_index():
    return send_from_directory(WEB_DIR, "index.html")


@app.get("/<path:filename>")
def webapp_asset(filename: str):
    if filename.startswith(("admin", "api/", "uploads/")):
        abort(404)
    return send_from_directory(WEB_DIR, filename)


@app.get("/uploads/<path:filename>")
def uploaded_image(filename: str):
    return send_from_directory(UPLOAD_DIR, filename)


@app.get("/api/cars")
def public_cars():
    return jsonify({"cars": list_cars(include_hidden=False)})


@app.route("/admin/login", methods=["GET", "POST"])
def admin_login():
    if _current_admin():
        return redirect(url_for("admin_panel"))
    error = ""
    if request.method == "POST":
        _require_csrf()
        client_key = request.remote_addr or "unknown"
        if _login_is_limited(client_key):
            return render_template(
                "login.html",
                csrf_token=_csrf_token(),
                error="Слишком много попыток. Попробуйте через 5 минут.",
                setup_error=_owner_setup_error(),
            ), 429
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        admin = get_admin_by_username(username)
        if (
            admin
            and admin["is_active"]
            and check_password_hash(admin["password_hash"], password)
        ):
            session.clear()
            session["admin_id"] = int(admin["id"])
            session["csrf_token"] = secrets.token_urlsafe(32)
            login_attempts.pop(client_key, None)
            return redirect(url_for("admin_panel"))
        _record_failed_login(client_key)
        error = "Неверный логин или пароль"
    return render_template(
        "login.html",
        csrf_token=_csrf_token(),
        error=error,
        setup_error=_owner_setup_error(),
    )


@app.post("/admin/logout")
@login_required()
def admin_logout():
    _require_csrf()
    session.clear()
    return redirect(url_for("admin_login"))


@app.get("/admin")
@login_required()
def admin_panel():
    return render_template(
        "admin.html", admin=_current_admin(), csrf_token=_csrf_token()
    )


@app.get("/admin/<path:filename>")
def admin_asset(filename: str):
    return send_from_directory(WEB_DIR / "admin", filename)


@app.get("/api/admin/session")
@login_required()
def admin_session():
    admin = _current_admin()
    return jsonify(
        {
            "user": {
                "id": admin["id"],
                "username": admin["username"],
                "role": admin["role"],
            },
            "csrf_token": _csrf_token(),
        }
    )


@app.get("/api/admin/cars")
@login_required()
def admin_cars():
    return jsonify({"cars": list_cars(include_hidden=True)})


@app.post("/api/admin/cars")
@login_required()
def admin_create_car():
    _require_csrf()
    try:
        car = _validate_car(_json_object(), creating=True)
        save_car(car)
    except (ValueError, sqlite3.IntegrityError) as error:
        return jsonify({"error": str(error)}), 400
    return jsonify({"car": get_car(car["id"])}), 201


@app.put("/api/admin/cars/<car_id>")
@login_required()
def admin_update_car(car_id: str):
    _require_csrf()
    if get_car(car_id) is None:
        return jsonify({"error": "Автомобиль не найден"}), 404
    try:
        car = _validate_car(_json_object(), creating=False)
        save_car(car, original_id=car_id)
    except ValueError as error:
        return jsonify({"error": str(error)}), 400
    return jsonify({"car": get_car(car_id)})


@app.delete("/api/admin/cars/<car_id>")
@login_required("owner")
def admin_delete_car(car_id: str):
    _require_csrf()
    if get_car(car_id) is None:
        return jsonify({"error": "Автомобиль не найден"}), 404
    local_urls = delete_car(car_id)
    for url in local_urls:
        _remove_local_upload(url)
    return "", 204


@app.post("/api/admin/cars/<car_id>/images")
@login_required()
def admin_upload_image(car_id: str):
    _require_csrf()
    car = get_car(car_id)
    if car is None:
        return jsonify({"error": "Автомобиль не найден"}), 404
    image = request.files.get("image")
    if image is None or not image.filename:
        return jsonify({"error": "Выберите изображение"}), 400
    extension = image.filename.rsplit(".", 1)[-1].lower()
    if (
        extension not in ALLOWED_IMAGE_EXTENSIONS
        or not image.mimetype.startswith("image/")
        or not _valid_image_signature(image)
    ):
        return jsonify({"error": "Файл не является корректным JPG, PNG или WEBP"}), 400
    safe_stem = secure_filename(Path(image.filename).stem)[:40] or "car"
    filename = f"{safe_stem}-{secrets.token_hex(8)}.{extension}"
    image.save(UPLOAD_DIR / filename)
    image_id = add_car_image(
        car_id, f"/uploads/{filename}", f"{car['brand']} {car['model']}"
    )
    return jsonify({"image_id": image_id, "url": f"/uploads/{filename}"}), 201


@app.delete("/api/admin/images/<int:image_id>")
@login_required()
def admin_delete_image(image_id: int):
    _require_csrf()
    url = delete_car_image(image_id)
    if url is None:
        return jsonify({"error": "Фотография не найдена"}), 404
    _remove_local_upload(url)
    return "", 204


@app.put("/api/admin/cars/<car_id>/images/order")
@login_required()
def admin_reorder_images(car_id: str):
    _require_csrf()
    payload = _json_object()
    try:
        image_ids = [int(value) for value in payload.get("image_ids", [])]
        reorder_car_images(car_id, image_ids)
    except (TypeError, ValueError):
        return jsonify({"error": "Некорректный порядок фотографий"}), 400
    return "", 204


@app.get("/api/admin/users")
@login_required("owner")
def admin_users():
    return jsonify({"users": list_admins()})


@app.post("/api/admin/users")
@login_required("owner")
def admin_create_user():
    _require_csrf()
    payload = _json_object()
    username = str(payload.get("username", "")).strip()
    password = str(payload.get("password", ""))
    role = str(payload.get("role", "manager"))
    if not USERNAME_RE.fullmatch(username):
        return jsonify({"error": "Некорректный логин"}), 400
    if len(password) < 12:
        return jsonify({"error": "Пароль должен содержать не менее 12 символов"}), 400
    if role not in ROLE_LEVEL:
        return jsonify({"error": "Некорректная роль"}), 400
    try:
        admin_id = create_admin(username, generate_password_hash(password), role)
    except sqlite3.IntegrityError:
        return jsonify({"error": "Такой логин уже существует"}), 400
    return jsonify({"id": admin_id}), 201


@app.put("/api/admin/users/<int:admin_id>")
@login_required("owner")
def admin_update_user(admin_id: int):
    _require_csrf()
    current = _current_admin()
    target = get_admin(admin_id)
    if target is None:
        return jsonify({"error": "Пользователь не найден"}), 404
    payload = _json_object()
    password = str(payload.get("password", ""))
    role = str(payload.get("role", target["role"]))
    is_active = bool(payload.get("is_active", target["is_active"]))
    if role not in ROLE_LEVEL:
        return jsonify({"error": "Некорректная роль"}), 400
    if password and len(password) < 12:
        return jsonify({"error": "Пароль должен содержать не менее 12 символов"}), 400
    if admin_id == current["id"] and (not is_active or role != "owner"):
        return jsonify({"error": "Нельзя лишить себя доступа владельца"}), 400
    update_admin(
        admin_id,
        password_hash=generate_password_hash(password) if password else None,
        role=role,
        is_active=is_active,
    )
    return "", 204


@app.errorhandler(413)
def upload_too_large(_error):
    return jsonify({"error": f"Файл больше {MAX_UPLOAD_MB} МБ"}), 413


@app.errorhandler(500)
def internal_error(_error):
    logger.exception("Внутренняя ошибка Web-сервера")
    return jsonify({"error": "Внутренняя ошибка сервера"}), 500


_bootstrap()


if __name__ == "__main__":
    app.run(host=WEB_HOST, port=WEB_PORT, debug=False)
