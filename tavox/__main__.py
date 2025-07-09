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

import re
import docopt
import os
import tempfile
import subprocess
import shutil
import sys
import logging
import logging.config

from typing import Dict, Any
from pathlib import Path

from tavox import *

logging_cfg = {
	"version": 1,
	"disable_existing_loggers": False,
	"formatters": {
		"simple": {
			"format": "%(message)s"
		}
	},
	"handlers": {
		"console": {
			"class": "logging.StreamHandler",
			"level": "INFO",
			"formatter": "simple",
		}
	},
	"loggers": {
		"tavox": {
			"level": "INFO", "handlers": ["console"], "propagate": False
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
"""
#--------|---------|---------|---------|---------|---------|---------|---------|


def get_ffmpeg_encoders() -> dict[str, dict[str, str]]:
	"""
	Parses the output of `ffmpeg -v 0 -encoders` into a dictionary structure.
	Returns:
		dict: A dictionary where keys are encoder names and values are descriptions.
	"""
	# Run the `ffmpeg` command to get the list of encoders
	try:
		result = subprocess.run(["ffmpeg", "-v", "0", "-encoders"], capture_output=True, text=True, check=True)
	except subprocess.CalledProcessError as e:
		raise RuntimeError(f"Error running ffmpeg: {e}")

	# Split the output into lines
	lines = result.stdout.splitlines()

	# Initialize the encoders dictionary
	encoders = {}

	# Flag to determine when to start processing encoder lines
	start_processing = False

	for line in lines:
		# Detect the line which only contains spaces
		if re.match(r"[\-]+", line.strip()):
			start_processing = True
			continue

		# Skip lines until we reach the encoder list
		if not start_processing:
			continue

		# Parse each encoder line (format: flags name description)
		match = re.match(r"^\s*([A-Z\.]+)\s+([^\s]+)\s+(.+)", line)
		if match:
			flags, name, description = match.groups()
			encoders[name] = {"flags": flags.strip(), "description": description.strip()}

	return encoders


def run_script(script: str | os.PathLike):
	script_path = Path(script)
	with open(script_path) as script_file:
		try:
			code_obj = compile(script_file.read(), script_file.name, "exec")
		except SyntaxError as ex:
			print(f"Failed to comile script '{script_path}'!")
			print(f"Error in line {ex.lineno}: {ex.text}")
			exit(1)
	try:
		old_wd = os.getcwd()
		os.chdir(script_path.parent)
		exec(code_obj)
		os.chdir(old_wd)
	except Exception as ex:
		print(f"Failed to execute script '{script_path}'")
		print(ex)
		exit(1)


def main():
	options: dict[str, Any] = docopt.docopt(usage_msg, version="0.1")

	if options["--list-voices"]:
		for v in available_voices():
			print(v)
		exit()

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
		print("rendering video")

		melt_bin_name = None

		for x in ["mlt-melt", "melt"]:
			if shutil.which(x) is not None:
				melt_bin_name = x
				break

		if melt_bin_name is None:
			print("It seems that the melt command is not installed")
			exit(1)

		out_path = f"{script.name}.mkv"
		if options["--out-path"] is not None:
			out_path = options["--out-path"]

		supported_codecs = get_ffmpeg_encoders()
		if "libx264" in supported_codecs:
			vcodec = "libx264"
		elif "libopenh264" in supported_codecs:
			vcodec = "libopenh264"
		else:
			raise RuntimeError("no video encoder found")

		print(f"using video codec: {vcodec}")
		mlt_cmd = f"{melt_bin_name} -progress -verbose {mlt_project_file} -consumer avformat:{out_path} acodec=flac vcodec={vcodec} preset=slow crf=16"
		print(f"using mlt command: {mlt_cmd}")
		result = subprocess.run(mlt_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
		if result.returncode != 0:
			print(f"error rendering video {result.stderr}")
			exit(1)


if __name__ == "__main__":
	main()
