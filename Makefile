install_git_hooks:
	@ln -s /Users/axel/Projects/remote-inky/.hooks/pre-push .git/hooks/pre-push

server:
	@SECRET_KEY=s3cr3t \
		TOKEN=t0k3n \
		FLASK_APP="src/remote_inky/app.py:create_app" \
		FLASK_DEBUG=1 \
		flask run --host=0.0.0.0
