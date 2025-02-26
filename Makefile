

install: install_pip install_latex

install_pip:
	pip3 install .

install_latex:
	mkdir -p ~/texmf/tex/latex/
	cp latex/tavox.sty ~/texmf/tex/latex/

clean:
	rm -fr build
	rm -fr tavox.egg-info