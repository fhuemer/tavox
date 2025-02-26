
# tavox

`tavox` is a tool for adding (TTS-based) voice-over tracks to your LaTeX beamer presentations and for automatically generating videos out of them.
It consists of two parts: a [LaTeX package](latex/tavox.sty) and a [Python package](tavox).


## Showcase
The LaTeX package introduces a few commands, one of which is `speak`.
This command allows specifying the text to be said in the voice-over track for each individual slide of your presentation.
Consider the example `demo.tex` shown below.

```latex
\documentclass{beamer}
\usepackage{tavox}

\begin{document}

	\begin{frame}
		\speak{Hello! You are viewing an example presentation that shows how tavox is used.}
		Hello World!
	\end{frame}

\end{document}
```

This example is deliberately kept simple to highlight the ease with which `tavox` can be integrated into your presentations.
However, the `speak` command is actually much more powerful and also supports Beamer-style overlay specifications and optional arguments to introduce delays before and after the spoken lines.
Please refer to the `examples` directory for more advanced demonstrations of the capabilities of `tavox`.

Upon compilation of the above presentation, a file named `demo.tavox` will be created by the package.
This file can then be passed on to the accompanying `tavox` CLI tool that comes with the `tavox` Python package to create a video:

```bash
tavox demo.tavox
```

This command automatically synthesizes the required voice samples, renders the PDF file and creates an MLT project, which is then rendered into a video file.
The created MLT project can also be opened in video editors like [Shotcut](https://www.shotcut.org/) or [Kdenlive](https://kdenlive.org/).


## Installation

Run `make install` to install `tavox` Python package using pip and to copy the `tavox` LaTeX package to `~/texmf/tex/latex`.
Note that these two steps can also be run individually via `make install_pip` and `make install_latex`.
In case you don't want the `tavox` latex package installed in your home directory, you can put it at an arbitrary location as long as you ensure that `tavox.sty` is in your LaTeX search path.

## Dependencies

Strict Dependencies:
 * [ffmpeg](https://ffmpeg.org/)
 * [Imagemagick](https://imagemagick.org/) (PDF to image conversion)
 * [MLT Multimedia Framework]( ) (used by many video editors, such as [Shotcut](https://www.shotcut.org/) or [Kdenlive](https://kdenlive.org/))

Optional TTS-Services:
 * [Coqui TTS]( ) (open source TTS Python tool)
 * [OpenAI's Python API](https://github.com/openai/openai-python) (**Note**: using OpenAI's TTS service requires paid API access)

Note that you need at least one working TTS service to run `tavox`.
However, you can also create new ones yourself.

Optional:
 * [Shotcut](https://www.shotcut.org/), [Kdenlive](https://kdenlive.org/en/) (allows to view the generated mlt files)
 * [rubber](https://github.com/petrhosek/rubber) (to build the examples)


Below you will find instructions for installing the dependencies on Fedora (40+) and Ubuntu (tested on 22.04).

### Fedora

```bash
sudo dnf install ffmpeg ImageMagick mlt
sudo dnf install shotcut rubber # optional
pip install openai # optional
```

Note that Coqui TTS Version 0.22.0 requires a specific Python version (3.9):

```bash
sudo dnf install python3.9
python3.9 -m ensurepip
python3.9 -m pip install TTS
```

### Ubuntu

```bash
sudo apt-get install ImageMagick melt
sudo apt-get install shotcut rubber # optional
pip install openai # optional
```

Be aware that this just installs the `melt` CLI tool from MLT and it appears that there does not exist an Ubuntu package for the whole framework.
However, as of writing, a full installation of the MLT framework is not required, the shotcut package comes with its own version and `Tavox` only uses `melt`.

According to its installation guide `Coqui TTS` works on Ubuntu (18.04) with Python versions `>=3.9,<3.12`.
On Ubuntu 22.04 (Jammy) `Coqui TTS` worked out of the box with Python 3.11.4 and 3.11.5.
It can be installed via

```bash
pip3 install TTS
```

Converting PDFs to PNGs using ImageMagick in Ubuntu might produce an error.
An appropriate fix can be found [here](https://stackoverflow.com/questions/52998331).


## Getting Started

To get started go through the examples presentations in the `examples` folder. The examples support the following Makefile targets:

 * `slides`: creates the slides PDF
 * `transcript` creates the transcript PDF (the file [transcript_setup.tex](examples/transcript_setup.tex) configures the style of transcript)
 * `video`: renders the video
 * `video_VOICE`: renders the video using the specified `VOICE` (e.g. `make video_alloy` for the default OpenAI voice).

## Licensing Information


### Python Package

The `tavox` Python package is licensed under the **Lesser General Public License (LGPL) v3.0**.

For full licensing terms, see the included `LICENSE-LGPL.txt` or visit:
[https://www.gnu.org/licenses/lgpl-3.0.html](https://www.gnu.org/licenses/lgpl-3.0.html)

### LaTeX Package

The `tavox` LaTeX package is licensed under the **LaTeX Project Public License (LPPL) v1.3c**.


For full licensing terms, see the included `LICENSE-LPPL.txt` or visit:
[https://www.latex-project.org/lppl/](https://www.latex-project.org/lppl/)


### Additional Notes

** Of course, all content you produce using `tavox` is your own! **


