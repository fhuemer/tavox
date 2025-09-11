#!/bin/env python3
#
# This file is part of tavox.
#
# Copyright (C) 2025 Florian Huemer
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with this program. If not, see <https://www.gnu.org/licenses/>.
#
# SPDX-License-Identifier: LGPL-3.0-or-later

import docopt
import os
import tempfile
import subprocess
import shutil
import sys
import pathlib
import logging
import logging.config

from typing import Dict, Any
from pathlib import Path

from tavox import *


red = "\x1b[31;20m"
bold_red = "\x1b[31;1m"
yellow = "\x1b[33;20m"
grey = "\x1b[90;20m"
reset = "\x1b[0m"

logging_cfg = {
	"version": 1,
	"disable_existing_loggers": False,
	"filters": {
		"below_info": {
			"()": "tavox.logging_util.LevelRangeFilter",
			"low": None,
			"high": logging.INFO
		},
		"below_error_downto_info": {
			"()": "tavox.logging_util.LevelRangeFilter",
			"low": logging.INFO,
			"high": logging.ERROR
		},
		"error_and_above": {
			"()": "tavox.logging_util.LevelRangeFilter",
			"low": logging.ERROR,
			"high": None
		},
	},
	"formatters": {
		"simple_info": {
			"format": "%(message)s"
		},
		"simple_error": {
			"format": f"{red}Error: {reset}" + "%(message)s"
		},
		"simple_debug": {
			"format": f"{grey}Debug: {reset}" + "%(message)s"
		}
	},
	"handlers": {
		"console_error": {
			"class": "logging.StreamHandler",
			"level": "ERROR",
			"formatter": "simple_error",
			"filters": ["error_and_above"]
		},
		"console_info": {
			"class": "logging.StreamHandler",
			"level": "DEBUG",
			"formatter": "simple_info",
			"filters": ["below_error_downto_info"]
		},
		"console_debug": {
			"class": "logging.StreamHandler",
			"level": "DEBUG",
			"formatter": "simple_debug",
			"filters": ["below_info"]
		}
	},
	"loggers": {
		"tavox": {
			"level": "INFO",
			"handlers": ["console_debug", "console_info", "console_error"],
			"propagate": False
		}
	}
}
logging.config.dictConfig(config=logging_cfg)

usage_msg = """
Usage:
  tavox [options] <SCRIPT>
  tavox --list-voices

Options:
  --no-video         Don't render the video, just create the mlt project.
  --speak-merge      Merge subsequent speak commands before generating voice
                     samples.
  --mlt-project MLT  The path to the mlt-project file. If ommitted a temporary
                     file will be created.
  --out-path PATH    The path to the output video file.
  --voice VOICE      Set the initial voice [default: default].
  --pre-script PS    A python script that is simply executed (using exec)
                     before the actual SCRIPT is run and the voice is set. This
                     can be used to, e.g., load a custom voice.
  --list-voices      Print the list of available voices.
  --debug            Enable debug output.
  -h --help          Show this help message.
  --version          Show version information.
"""
#--------|---------|---------|---------|---------|---------|---------|---------|


def run_script(script: str | os.PathLike):
	script_path = Path(script)
	try:
		with open(script_path) as script_file:
			try:
				code_obj = compile(script_file.read(), script_file.name, "exec")
			except SyntaxError as ex:
				logger.error(f"Failed to comile script '{script_path}'! Error in line {ex.lineno}: {ex.text}")
				raise ex
	except FileNotFoundError as ex:
		logger.error(f"Script '{script_path}' not found!")
		raise ex

	try:
		old_wd = os.getcwd()
		os.chdir(script_path.parent)
		exec(code_obj)
		os.chdir(old_wd)
	except Exception as ex:
		logger.error(f"Failed to execute script '{script_path}'")
		raise ex

logger = logging.getLogger("tavox")

def run_tavox():
	options: dict[str, Any] = docopt.docopt(usage_msg, version="0.2.5")

	if options["--debug"]:
		logger.setLevel(logging.DEBUG)
		logger.debug("Debug output enabled")

	if options["--list-voices"]:
		for v in available_voices():
			print(v)
		return

	script = Path(options["<SCRIPT>"])

	project = TavoxProject()
	activate_project(project)

	if options["--pre-script"]:
		run_script(options["--pre-script"])

	set_voice(options["--voice"])
	run_script(script)

	if options["--mlt-project"]:
		mlt_project_file = options["--mlt-project"]
	else:
		mlt_dir = tempfile.TemporaryDirectory(prefix="tavox_", delete=False).name
		mlt_project_file = f"{mlt_dir}/{script.name}.mlt"
	create_mlt(project, mlt_project_file, merge_speak_commands=options["--speak-merge"])

	if not options["--no-video"]:
		logger.info("rendering video")

		out_path = f"{script.name}.mkv"
		if options["--out-path"] is not None:
			out_path = options["--out-path"]

		supported_codecs = ffmpeg_get_encoders()
		if "libx264" in supported_codecs:
			vcodec = "libx264"
		elif "libopenh264" in supported_codecs:
			vcodec = "libopenh264"
		else:
			logger.error("No suitable video codec found.")
			raise RuntimeError("no video encoder found")

		logger.info(f"using video codec: {vcodec}")
		run_melt([
			"-progress",
			"-verbose",
			f"{mlt_project_file}",
			"-consumer",
			f"avformat:{out_path}",
			"acodec=flac",
			f"vcodec={vcodec}",
			"preset=slow",
			"crf=16"
		])
		logger.info(f"video rendered to {out_path}")

def main():
	try:
		run_tavox()
	except Exception as ex:
		if logger.getEffectiveLevel() <= logging.DEBUG:
			raise ex
		exit(1)
	

