mypy:
	@poetry run mypy src/remote_inky/* tests/*

flake8:
	@poetry run flake8 src/remote_inky/* tests/*

lint: mypy flake8

test: unit_test

shell:
	@poetry run ipython

install_git_hooks:
	@ln -s /Users/axel/Projects/remote-inky/.hooks/pre-push .git/hooks/pre-push

server:
	@SECRET_KEY=s3cr3t \
		TOKEN=t0k3n \
		FLASK_APP="src/remote_inky/app.py:create_app" \
		FLASK_DEBUG=1 \
		poetry run flask run
