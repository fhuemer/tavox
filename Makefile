

ifeq ($(OS),Windows_NT)
	DETECTED_OS := Windows
else
	UNAME_S := $(shell uname -s)
	ifeq ($(UNAME_S),Linux)
		DETECTED_OS := Linux
	else
		DETECTED_OS := Unknown
	endif
endif

install: install_pip install_latex

install_pip:
	@echo ===== Installing Python package =====
	python -m pip install .

install_latex:
	@echo ===== Installing LaTeX package =====
ifeq ($(DETECTED_OS),Linux)
	mkdir -p ~/texmf/tex/latex/
	cp latex/tavox.sty ~/texmf/tex/latex/
else ifeq ($(DETECTED_OS),Windows)
	@cmd /c install.bat
else
	echo "Unsupported OS"
endif

clean:
	rm -fr build
	rm -fr tavox.egg-info