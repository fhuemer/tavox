
LATEX_MK=TEXINPUTS="../../latex//;" latexmk -pdf -quiet
TAVOX=PYTHONPATH=../.. python -m tavox

slides: $(EXAMPLE_NAME).pdf

$(EXAMPLE_NAME).pdf: $(EXAMPLE_NAME).tex
	$(LATEX_MK) $(EXAMPLE_NAME).tex

transcript: $(EXAMPLE_NAME).tex
	echo "\\def\showtranscript{1} \\input{$(EXAMPLE_NAME).tex}" > $(EXAMPLE_NAME).transcript.tex
	$(LATEX_MK) $(EXAMPLE_NAME).transcript.tex
	rm $(EXAMPLE_NAME).transcript.tex

video: video_default

define VIDEO_template =
video_$(1): slides
	$(TAVOX) --voice $(1) $(EXAMPLE_NAME).tavox
endef

$(foreach voice, $(shell $(TAVOX) --list-voices), $(eval $(call VIDEO_template,$(voice))))

all: video

clean:
	rm -f *.log *.snm *.toc *.aux *.nav *.pdf *.out *.tavox *.mkv *.vrb *.fls *.fdb_latexmk