PROJECT_FOLDER = backend
MANAGE = python ${PROJECT_FOLDER}/manage.py
VENV_DIR = .venv
VENV_ACTIVATE = .\$(VENV_DIR)\Scripts\activate
VENV_PYTHON = .\$(VENV_DIR)\bin\python
REQUIREMENTS = requirements.txt
REQUIREMENTS_DEV = requirements_dev.txt
ENV_FILE = .env


venv:
	@if not exist "$(VENV_DIR)" $(PYTHON) -m venv $(VENV_DIR)
	$(VENV_ACTIVATE)

env-prepare: # создать .env-файл для секретов
	@if not exist .\backend\.env copy .env.example .\backend\.env && echo .env created || echo .env already exists

insall_req:
	@echo "Installing requirements..."
	cd backend && pip install -r requirements.txt -r requirements_dev.txt

migrate:
	@echo "Running migrations..."
	${MANAGE} migrate

test:
	@echo "Running tests with pytest..."
	pytest ${PROJECT_FOLDER} -v
	@echo "Calculating test-coverage..."
	pytest --cov=${PROJECT_FOLDER}/api_payouts

celery:
	@echo "Running Celery..."
	$(VENV_ACTIVATE) && cd backend && celery -A backend worker --loglevel=info --pool=solo --concurrency=4


run_api:
	@echo "Running Django..."
	$(VENV_ACTIVATE) && ${MANAGE} runserver --settings=backend.settings


run_prepare: env-prepare venv insall_req migrate celery

dbr: env-prepare
	@echo "Building docker"
	docker compose up --build -d

dt:
	@echo "Running tests"
	docker-compose exec backend python manage.py test