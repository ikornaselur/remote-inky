mypy:
	@poetry run mypy src/remote_inky/* tests/*

flake8:
	@poetry run flake8 src/remote_inky/* tests/*

lint: mypy flake8

test: unit_test

unit_test:
	@poetry run pytest tests/unit -xvvs

shell:
	@poetry run ipython

install_git_hooks:
	@ln -s /Users/axel/Projects/remote-inky/.hooks/pre-push .git/hooks/pre-push
