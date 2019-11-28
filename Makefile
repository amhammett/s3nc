.PHONY: build deploy guard-% help run test

# tasks with double #'s will be displayed in help

help: ## this help text
	@echo 'Available targets'
	@grep -E '^[a-zA-Z0-9_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}'

# pathing

pip_path := ./venv/bin/pip
pip_flake8_path := ./venv/bin/flake8
pip_isort_path := ./venv/bin/isort
pip_pytest_path := ./venv/bin/pytest
pip_python_path := ./venv/bin/python
pip_watch_path := ./venv/bin/watchmedo
pip_lib_path := ./venv/lib/python3.7/site-packages/

# environment
install: venv install_python_packages ## install all the things

venv: # install virtual environment
	python3 -m virtualenv venv

install_python_packages: ## install python packages
	${pip_path} install -r requirements/dev.txt --no-warn-script-location

# testing
test: test_flake8 test_isort test_pytest ## test all the things

test_flake8: # 
	PYTHONPATH=${pip_lib_path} ${pip_flake8_path} src/ tests/
test_isort: # 
	PYTHONPATH=${pip_lib_path} ${pip_isort_path} --skip venv --skip node_modules --recursive --check-only --quiet src
test_pytest: # 
	PYTHONPATH=${pip_lib_path} ${pip_pytest_path} tests/ --cov src/ --cov-branch

# development
watch_command := make test
watch_pattern := *.py;*.txt

watch: guard-watch_command guard-watch_pattern ## watch all the things <watch_command> <watch_pattern>
	PYTHONPATH=${pip_lib_path} ${pip_watch_path} shell-command  --patterns="${watch_pattern}" --recursive  --command='echo "---" & ${watch_command}' .

run: ## run all the things
	${pip_python_path} src/sync.py

# system
guard-%: # ensure required vars are set
	@ if [ "${${*}}" = "" ]; then \
		echo "Variable $* not set. Specify via $*=<value>"; \
		exit 1; \
	fi
