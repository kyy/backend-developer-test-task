#### Тестовое задание https://docs.google.com/document/d/12gInWY59dER0ditkcUOawdDYpfOdaxigMDG62Hmtyrc/edit?tab=t.0#heading=h.qkagjwa413gb

### Рекомендуемы запуск

Запуск "одной командой" (Celery+Postgres+Nginx+Django+Redis >> Docker) 
Swagger UI будет доступен по адресу http://localhost/api/docs/

  ```sh
  make dbr
  ```
Запуск тестов в Docker
  ```sh
  make dt
  ```
---
### Ручной запуск Windows
Для запуска необходим: Redis, python 3.10<=
1. Создание .env файла, запуск Celery, создание виртуального окружения, установка зависимостей из pip, выполнение миграций >> sqlite. 
   ```sh
   make run_prepare
   ```
2. Запуск Django
   ```sh
   make run_api
   ```
3. Запуск тестов:
   ```sh
   make test 
   ```
------

### Рекомендации по запуску в prod:
1. Вынести все чувствительные данные в .env;
2. Создать конфигурацию для Django - settings_prod.py;
3. Настроить CI/DI пайплайн для обновления/перезапуска сервисов;
4. Подготовить конфигурацию Docker-файлов для prod или установить Linux server необходимые сервисы вручную (или через скрипты автоматизации) управляя supervisor;
5. Установка-настройка сервисов для мониторинга/сбора метрик логов Prometheus+Grafana+Loki, настройка алертов в Grafana;
6. Настройка бекапов;
...