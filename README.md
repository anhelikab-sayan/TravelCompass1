# TravelCompass

TravelCompass — веб-приложение на Django для поиска и отображения туристических мест с использованием картографического сервиса 2GIS.

Проект разработан в рамках учебной практики для изучения работы с Django, Git и внешними API.

---

## Основной функционал

- Регистрация и авторизация пользователей
- Личный профиль пользователя
- Интеграция карты 2GIS
- Отображение туристических объектов на карте
- Разделение проекта на модули (users, core)
- Административная панель Django

---

## Используемые технологии

- Python 3
- Django
- HTML / CSS
- 2GIS Maps API
- SQLite
- Git / GitHub

---

## Структура проекта

TravelCompass/
│
├── manage.py
├── .env
├── requirements.txt
├── .gitignore
├── README.md
│
├── TravelCompass/
│   ├── settings.py
│   ├── urls.py
│   ├── asgi.py
│   └── wsgi.py
│
├── core/
│   ├── migrations/
│   ├── api/
│   │   ├── d2gis.py
│   │   └── route_planner.py
│   │
│   ├── __init__.py
│   ├── admin.py
│   ├── apps.py
│   ├── models.py
│   ├── tests.py
│   ├── urls.py
│   └── views.py
│
├── users/
│   ├── migrations/
│   ├── __init__.py
│   ├── admin.py
│   ├── apps.py
│   ├── models.py
│   ├── tests.py
│   ├── urls.py
│   └── views.py
│
├── templates/
│   ├── base.html
│   ├── core/
│   │   ├── index.html
│   │   └── search.html
│   │
│   └── users/
│       ├── login.html
│       ├── register.html
│       └── profile.html
│
└── static/

---

## Установка и запуск

1. Клонирование репозитория

git clone <ссылка_на_репозиторий>
cd TravelCompass

2. Создание виртуального окружения

python -m venv venv

Активация:

Windows:
venv\Scripts\activate

MacOS / Linux:
source venv/bin/activate

3. Установка зависимостей

pip install -r requirements.txt

4. Применение миграций

python manage.py migrate

5. Создание суперпользователя (по желанию)

python manage.py createsuperuser

6. Запуск сервера

python manage.py runserver

После запуска приложение будет доступно по адресу:
http://127.0.0.1:8000/

---

## Переменные окружения

В файле .env необходимо указать:

SECRET_KEY=your_secret_key
DEBUG=True
2GIS_API_KEY=your_api_key
EMAIL_HOST_USER=your_email_host_user
EMAIL_HOST_PASSWORD=your_email_host_password

---

## Авторы

Проект разработан Белоглазовой Анжеликой и Бондаренко Линой.
