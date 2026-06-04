.PHONY: install run dev test clean build

install: ; pip install -r requirements.txt
run: ; python -m taq.main --host 0.0.0.0 --port 8400
dev: ; python -m taq.main --host 0.0.0.0 --port 8400 --reload
test: ; python -m pytest tests/ -v
clean: ; find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true; find . -type f -name "*.pyc" -delete; rm -rf build/ dist/ *.spec
build:
	pip install nuitka
	python -m nuitka --standalone --onefile --output-dir=dist taq/main.py
	mv dist/main dist/taq
docker-build: ; docker build -t taq-engine .
docker-run: ; docker run -p 8400:8400 taq-engine
