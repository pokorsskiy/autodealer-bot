---
name: db-migrator
description: Инструкции и паттерны для безопасного редактирования схем таблиц SQLite и добавления колонок без потери данных.
---

# Навык безопасных миграций БД SQLite

При добавлении новых полей или изменении таблиц в боте ИИ обязан использовать безопасные методы, гарантирующие сохранность данных пользователей.

## 1. Безопасное добавление новой колонки (`ALTER TABLE`)
Если нужно добавить новое поле (например, `phone_number TEXT` или `source TEXT`), использовать следующий паттерн:

```python
def migrate_db():
    with sqlite3.connect(DB_NAME) as conn:
        cur = conn.cursor()
        # Получаем текущие колонки
        cur.execute("PRAGMA table_info(instagram_users)")
        columns = [col[1] for col in cur.fetchall()]
        
        # Безопасно добавляем колонку, если её ещё нет
        if 'source' not in columns:
            cur.execute("ALTER TABLE instagram_users ADD COLUMN source TEXT DEFAULT 'INSTA'")
            conn.commit()
```

## 2. Использование `INSERT OR IGNORE` / `INSERT OR REPLACE`
Чтобы предотвратить падения `sqlite3.IntegrityError` при повторном сохранении пользователя:
```python
cur.execute('''
    INSERT INTO instagram_users (user_id, username, first_name, added_at)
    VALUES (?, ?, ?, ?)
    ON CONFLICT(user_id) DO UPDATE SET
        username = excluded.username,
        first_name = excluded.first_name
''', (user_id, username, first_name, now))
```

## 3. Экспорт резервной копии перед миграцией
Перед изменением схемы ИИ подготавливает код с автоматическим созданием бэкапа существующей БД: `shutil.copyfile(DB_NAME, f"{DB_NAME}.bak")`.
