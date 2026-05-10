PYTHON ?= python
PLUGIN ?=

.PHONY: link install uninstall relink status init-config init-config-force test new-plugin clean help

help:
	@echo "Cibles disponibles :"
	@echo "  link [PLUGIN=Nom]        symlinks plugins/* vers <Packages>/ (mode dev)"
	@echo "  install [PLUGIN=Nom]     copie plugins/* vers <Packages>/ (mode utilisateur)"
	@echo "  uninstall [PLUGIN=Nom]   supprime <Packages>/Alfaco*"
	@echo "  relink                   uninstall + link"
	@echo "  status                   liste l'état de chaque plugin"
	@echo "  init-config [PLUGIN=Nom] copie les templates plugins/<X>/templates/User/* vers <Packages>/User/"
	@echo "                           (skip les fichiers déjà présents — safe à relancer)"
	@echo "  init-config-force        comme init-config, mais écrase les fichiers existants"
	@echo "  test                     pytest sur plugins/*/tests/"
	@echo "  new-plugin NAME=Foo      scaffold plugins/AlfacoFoo/"
	@echo "  clean                    supprime __pycache__/, .pytest_cache/"

link:
	$(PYTHON) tools/deploy.py link $(if $(PLUGIN),--plugin $(PLUGIN),)

install:
	$(PYTHON) tools/deploy.py install $(if $(PLUGIN),--plugin $(PLUGIN),)

uninstall:
	$(PYTHON) tools/deploy.py uninstall $(if $(PLUGIN),--plugin $(PLUGIN),)

relink: uninstall link

status:
	$(PYTHON) tools/deploy.py status

init-config:
	$(PYTHON) tools/deploy.py init-config $(if $(PLUGIN),--plugin $(PLUGIN),)

init-config-force:
	$(PYTHON) tools/deploy.py init-config $(if $(PLUGIN),--plugin $(PLUGIN),) --force

test:
	$(PYTHON) -m pytest

new-plugin:
	@if [ -z "$(NAME)" ]; then echo "Usage: make new-plugin NAME=Foo"; exit 1; fi
	$(PYTHON) tools/new_plugin.py $(NAME)

clean:
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .pytest_cache -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name '*.pyc' -delete
