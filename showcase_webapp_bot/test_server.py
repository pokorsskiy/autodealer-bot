"""Проверки каталога и закрытой веб-админки."""

import io
import sqlite3
import tempfile
import unittest
from contextlib import closing
from pathlib import Path
from unittest.mock import patch

from werkzeug.security import generate_password_hash

import database as database_module
import server as server_module


class AdminServerTest(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        temp_path = Path(self.temp_dir.name)
        self.db_patcher = patch.object(
            database_module, "DB_NAME", str(temp_path / "test.db")
        )
        self.upload_patcher = patch.object(
            server_module, "UPLOAD_DIR", temp_path / "uploads"
        )
        self.db_patcher.start()
        self.upload_patcher.start()
        server_module.UPLOAD_DIR.mkdir()
        database_module.init_db()
        database_module.create_initial_owner(
            "owner", generate_password_hash("very-long-test-password")
        )
        server_module.app.config.update(
            TESTING=True, SECRET_KEY="test-secret", SESSION_COOKIE_SECURE=False
        )
        self.client = server_module.app.test_client()

    def tearDown(self) -> None:
        self.upload_patcher.stop()
        self.db_patcher.stop()
        self.temp_dir.cleanup()

    def login_owner(self) -> None:
        owner = database_module.get_admin_by_username("owner")
        with self.client.session_transaction() as session:
            session["admin_id"] = owner["id"]
            session["csrf_token"] = "csrf-test"

    def test_public_catalog_does_not_return_hidden_car(self) -> None:
        car = database_module.get_car("toyota-camry-2024")
        car["is_visible"] = False
        database_module.save_car(car, original_id=car["id"])
        response = self.client.get("/api/cars")
        self.assertEqual(response.status_code, 200)
        ids = {item["id"] for item in response.get_json()["cars"]}
        self.assertNotIn("toyota-camry-2024", ids)
        self.assertEqual(response.headers["Cache-Control"], "no-store")

    def test_admin_api_requires_login_and_csrf(self) -> None:
        self.assertEqual(self.client.get("/api/admin/cars").status_code, 401)
        self.login_owner()
        response = self.client.post("/api/admin/cars", json={})
        self.assertEqual(response.status_code, 403)

    def test_owner_can_login_and_login_assets_are_public(self) -> None:
        page = self.client.get("/admin/login")
        self.assertEqual(page.status_code, 200)
        asset_response = self.client.get("/admin/admin.css")
        self.assertEqual(asset_response.status_code, 200)
        asset_response.close()
        with self.client.session_transaction() as session:
            csrf_token = session["csrf_token"]
        response = self.client.post(
            "/admin/login",
            data={
                "csrf_token": csrf_token,
                "username": "owner",
                "password": "very-long-test-password",
            },
        )
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.headers["Location"].endswith("/admin"))

    def test_login_explains_when_owner_is_not_created(self) -> None:
        with closing(sqlite3.connect(database_module.DB_NAME)) as connection:
            with connection:
                connection.execute("DELETE FROM admin_users")
        with patch.object(server_module, "ADMIN_PASSWORD", "short"):
            response = self.client.get("/admin/login")
        self.assertEqual(response.status_code, 200)
        self.assertIn(
            "ADMIN_PASSWORD должен содержать".encode(),
            response.data,
        )

    def test_owner_can_create_update_and_delete_car(self) -> None:
        self.login_owner()
        payload = {
            "id": "test-car-2026",
            "brand": "Test",
            "model": "Car",
            "year": 2026,
            "price": 5_000_000,
            "mileage": 0,
            "body": "Седан",
            "drive": "Полный",
            "engine": "2.0 л",
            "power": "200 л.с.",
            "description": "Тестовый автомобиль",
            "location": "port",
            "is_visible": True,
            "sort_order": 0,
        }
        headers = {"X-CSRF-Token": "csrf-test"}
        created = self.client.post(
            "/api/admin/cars", json=payload, headers=headers
        )
        self.assertEqual(created.status_code, 201)

        payload["price"] = 5_500_000
        payload["is_visible"] = False
        updated = self.client.put(
            "/api/admin/cars/test-car-2026", json=payload, headers=headers
        )
        self.assertEqual(updated.status_code, 200)
        self.assertEqual(updated.get_json()["car"]["price"], 5_500_000)
        self.assertFalse(updated.get_json()["car"]["is_visible"])

        deleted = self.client.delete(
            "/api/admin/cars/test-car-2026", headers=headers
        )
        self.assertEqual(deleted.status_code, 204)
        self.assertIsNone(database_module.get_car("test-car-2026"))

    def test_manager_cannot_delete_car(self) -> None:
        manager_id = database_module.create_admin(
            "manager", generate_password_hash("very-long-test-password"), "manager"
        )
        with self.client.session_transaction() as session:
            session["admin_id"] = manager_id
            session["csrf_token"] = "csrf-test"
        response = self.client.delete(
            "/api/admin/cars/toyota-camry-2024",
            headers={"X-CSRF-Token": "csrf-test"},
        )
        self.assertEqual(response.status_code, 403)

    def test_owner_can_upload_and_delete_image(self) -> None:
        self.login_owner()
        response = self.client.post(
            "/api/admin/cars/toyota-camry-2024/images",
            data={"image": (io.BytesIO(b"RIFF\x00\x00\x00\x00WEBPdata"), "car.webp")},
            headers={"X-CSRF-Token": "csrf-test"},
            content_type="multipart/form-data",
        )
        self.assertEqual(response.status_code, 201)
        body = response.get_json()
        uploaded = server_module.UPLOAD_DIR / Path(body["url"]).name
        self.assertTrue(uploaded.exists())

        deleted = self.client.delete(
            f"/api/admin/images/{body['image_id']}",
            headers={"X-CSRF-Token": "csrf-test"},
        )
        self.assertEqual(deleted.status_code, 204)
        self.assertFalse(uploaded.exists())


if __name__ == "__main__":
    unittest.main()
