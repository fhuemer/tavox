
# Tavox

Tavox is a tool for adding (TTS-based) voice-over tracks to your LaTeX beamer presentations and for automatically generating videos out of them.
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

This example is deliberately kept simple to highlight the ease with which Tavox can be integrated into your presentations.
However, the `speak` command is actually much more powerful and also supports Beamer-style overlay specifications and optional arguments to introduce delays before and after the spoken lines.
Please refer to the `examples` directory for more advanced demonstrations of the capabilities of Tavox.

Upon compilation of the above presentation, a file named `demo.tavox` will be created by the package.
This file can then be passed on to the accompanying Tavox CLI tool that comes with the `tavox` Python package to create a video:

```bash
python -m tavox demo.tavox
```

This command automatically synthesizes the required voice samples, renders the PDF file and creates an MLT project, which is then rendered into a video file.
The created MLT project can also be opened in video editors like [Shotcut](https://www.shotcut.org/) or [Kdenlive](https://kdenlive.org/).


## Dependencies

Strict Dependencies:
 * [ffmpeg](https://ffmpeg.org/)
 * [poppler](https://poppler.freedesktop.org/) (PDF to image conversion)
 * [MLT Multimedia Framework](https://www.mltframework.org/) (used by many video editors, such as [Shotcut](https://www.shotcut.org/) or [Kdenlive](https://kdenlive.org/))

Optional TTS-Services:
 * [Coqui TTS](https://github.com/coqui-ai/TTS) (open source TTS Python tool)
 * [OpenAI's Python API](https://github.com/openai/openai-python) (**Note**: using OpenAI's TTS service requires paid API access)

Note that you need at least one working TTS service to use Tavox.
However, you can also create new ones yourself.

Optional:
 * [Shotcut](https://www.shotcut.org/), [Kdenlive](https://kdenlive.org/en/) (allows to view the generated `mlt` project files)
 * [latexmk](https://mgeier.github.io/latexmk.html) (to build the examples)


Below you will find instructions for installing the dependencies on Fedora (41+), Ubuntu (tested on 22.04) and Windows 11.

### Fedora (41+)

```bash
sudo dnf install ffmpeg poppler mlt
sudo dnf install shotcut latexmk # optional
pip install openai # optional
```

Note that Coqui TTS Version 0.22.0 requires a specific Python version (3.9):

```bash
sudo dnf install python3.9
python3.9 -m ensurepip
python3.9 -m pip install TTS
```

### Ubuntu (22.04)

```bash
sudo apt-get install poppler melt
sudo apt-get install latexmk # to build the examples
sudo apt-get install shotcut # optional
pip install openai # optional
```

According to its installation guide `Coqui TTS` works on Ubuntu (18.04) with Python versions `>=3.9,<3.12`.
On Ubuntu 22.04 (Jammy) `Coqui TTS` worked out of the box with Python 3.11.4 and 3.11.5.
It can be installed via

```bash
pip3 install TTS
```


### Windows 11

```powershell
winget install poppler shotcut
winget install python # if not already installed via different means
winget install git.git ezwinports.make # optional, to clone the repository and build the examples
pip install openai # optional, to use OpenAI's TTS service
```

## Installation

To install Tavox you need to clone the repository and install the Python package as well as the LaTeX package.
The provided Makefile in the root directory of the repository provides a convenient way to do this.

```bash
git clone https://github.com/fhuemer/tavox
cd tavox
make install
```

### Details

The `install` target of the Makefile installs the `tavox` Python package using `pip` (i.e., `python -m pip install .`).
To make the `tavox` LaTeX package available to your documents, the `tavox.sty` file must be in your LaTeX search path.
Hence, one of the following things happens.

* Linux: `latex/tavox.sty` is copied to `~/texmf/tex/latex/`
* Windows: The installation script detects your TeX distribution and performs the following operations:
  * MiKTeX: A new root path is added to the MiKTeX configuration, pointing to the `latex` directory of the `tavox` repository.
  * TeX Live: The `latex/tavox.sty` file is copied to where ever `TEXMFHOME` points to (usually `~/texmf/tex/latex/`).

If you don't want to use the Makefile, you can also install the LaTeX package manually by, e.g., copying the `tavox.sty` file to the same directory as your LaTeX document, or set the `TEXINPUTS` environment variable to include the `latex` directory of the `tavox` repository.

**Important**: Whenever you update to a new version of `tavox` make sure you update both the Python and the LaTeX package.

### OpenAI API Key

If you want to use OpenAI's TTS service, you also need to set the `OPENAI_API_KEY` environment variable to your OpenAI API key.

You can do this by adding the following line to your `.bashrc`:

```bash
export OPENAI_API_KEY="your_openai_api_key"
```

On Windows, you can set the environment variable in the System Properties dialog or by using PowerShell:

```powershell
[Environment]::SetEnvironmentVariable("OPENAI_API_KEY", "your_openai_api_key", "User")
```


## Getting Started

To get started go through the examples presentations in the `examples` folder. The examples support the following Makefile targets:

 * `slides`: creates the slides PDF
 * `transcript` creates the transcript PDF (the file [transcript_setup.tex](examples/transcript_setup.tex) configures the style of transcript)
 * `video`: renders the video
 * `video_VOICE`: renders the video using the specified `VOICE` (e.g., use `make video_alloy` for the default OpenAI voice).

Note that you don't need to install `tavox` in order to compile the examples.
The build script always uses the current Tavox version of the repository.
However, if Tavox was not installed via pip, you might have to install some Python dependencies such as `docopt` manually if you don't have them already installed (e.g., `pip install docopt`).
If you are running Windows be sure to use the *Git Bash* and not CMD or PowerShell to run the Makefile targets.

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

**Of course, all content you produce using `tavox` is your own!**


