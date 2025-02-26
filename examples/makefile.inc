
slides: $(EXAMPLE_NAME).tex
	rubber -d $(EXAMPLE_NAME).tex

transcript: $(EXAMPLE_NAME).tex
	rm -f $(EXAMPLE_NAME).transcript.rubbercache
	echo "\\def\showtranscript{1} \\input{$(EXAMPLE_NAME).tex}" > $(EXAMPLE_NAME).transcript.tex
	rubber -d $(EXAMPLE_NAME).transcript.tex
	rm $(EXAMPLE_NAME).transcript.tex

video: video_default

define VIDEO_template =
video_$(1): slides
	tavox --voice $(1) $(EXAMPLE_NAME).tavox
endef

$(foreach voice, $(shell tavox --list-voices), $(eval $(call VIDEO_template,$(voice))))

all: video

clean:
	rm -f *.log *.snm *.toc *.aux *.nav *.rubbercache *.pdf *.out *.tavox *.mkv *.vrb