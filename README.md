## Проект **Foodgram**
**Foodgram** - портал, где каждый может делиться своими рецептами.
stepan2204.ddns.net

### Как развернуть проект:

#### Локальный запуск с использованием Docker:

1. **Клонировать репозиторий:**
2. **Создать файл `.env` в таком формате:**
   ```bash
   POSTGRES_DB=
   POSTGRES_USER=
   POSTGRES_PASSWORD=
   DB_NAME=
   SECRET_KEY=
   ALLOWED_HOSTS=
   DEBUG=False
   ```
3. **Запустить контейнеры Docker:**
   ```bash
   docker-compose -f docker-compose-local.yml up -d
   ```

4. **Выполнить миграции:**
   ```bash
   docker exec -it foodgram-backend python manage.py makemigrations
   docker exec -it foodgram-backend python manage.py migrate
   ```

   
   
