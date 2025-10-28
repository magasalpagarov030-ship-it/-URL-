# 🔗 URL Shortener API (FastAPI + JWT + SQLite)

Простой и мощный бэкенд для сокращения ссылок, написанный на **FastAPI**.  
Поддерживает регистрацию пользователей, авторизацию через JWT, счётчик переходов и хранение данных в SQLite.

---

## 🚀 Возможности

✅ Регистрация и авторизация пользователей  
✅ Создание коротких ссылок  
✅ Перенаправление по коротким ссылкам  
✅ Подсчёт количества кликов  
✅ Защищённый доступ к данным (каждый пользователь видит только свои ссылки)  
✅ Простая установка и запуск

---

## 📦 Технологии

- [FastAPI](https://fastapi.tiangolo.com/)
- [SQLite](https://www.sqlite.org/)
- [SQLAlchemy](https://www.sqlalchemy.org/)
- [JWT (python-jose)](https://python-jose.readthedocs.io/)
- [Passlib (bcrypt)](https://passlib.readthedocs.io/)

---

## 🛠 Установка и запуск

### 1️⃣ Клонируй репозиторий
```bash
git clone https://github.com/yourusername/link-shortener.git
cd link-shortener

pip install -r requirements.txt


uvicorn main:app --reload
