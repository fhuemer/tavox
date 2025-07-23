

import subprocess
import platform
import shutil
import re
import pathlib
import os
import logging

logger = logging.getLogger("tavox")

_shotcut_windows_search_paths = [
	r"%LOCALAPPDATA%/Programs/Shotcut",
	r"%PROGRAMFILES%/Shotcut",
	r"%PROGRAMFILES(X86)%/Shotcut"
]

_melt_bin_name = None
_ffmpeg_bin_name = None
_ffprobe_bin_name = None

def _get_melt_bin() -> str:
	global _melt_bin_name
	if _melt_bin_name is not None:
		return _melt_bin_name

	if platform.system() == "Linux":
		for x in ["mlt-melt", "melt"]:
			if shutil.which(x) is not None:
				_melt_bin_name = x
				break
		if _melt_bin_name is None:
			logger.error("melt command not found! Please make sure the mlt framework is installed.")
			raise RuntimeError("melt command not found!")
	elif platform.system() == "Windows":
		for x in _shotcut_windows_search_paths:
			melt_exe = pathlib.Path(f"{os.path.expandvars(x)}/melt.exe")
			if melt_exe.exists():
				_melt_bin_name = melt_exe
		if _melt_bin_name is None:
			raise RuntimeError("melt.exe not found!")

	logger.debug(f"Using melt binary: {_melt_bin_name}")

	return _melt_bin_name

def _search_for_fftool(tool_name: str) -> str:
	if platform.system() == "Linux":
		if shutil.which(tool_name) is not None:
			return tool_name
	elif platform.system() == "Windows":
		# On Windows we use the ffmpeg tools included with shotcut, since this version will be used to render the video
		for x in _shotcut_windows_search_paths:
			tool_exe = pathlib.Path(f"{os.path.expandvars(x)}/{tool_name}.exe")
			if tool_exe.exists():
				return tool_exe
	return None
	
def _get_ffmpeg_bin() -> str:
	global _ffmpeg_bin_name
	if _ffmpeg_bin_name is None:
		_ffmpeg_bin_name = _search_for_fftool("ffmpeg")
		if _ffmpeg_bin_name is None:
			raise RuntimeError("ffmpeg command not found!")
	return _ffmpeg_bin_name
	
def _get_ffprobe_bin() -> str:
	global _ffprobe_bin_name
	if _ffprobe_bin_name is None:
		_ffprobe_bin_name = _search_for_fftool("ffprobe")
		if _ffprobe_bin_name is None:
			raise RuntimeError("ffprobe command not found!")
	return _ffprobe_bin_name


def run_pdftoppm(arguments):
	"""
	Run the pdftoppm command with the given arguments.
	"""
	r = subprocess.run(
		["pdftoppm"] + arguments,
		stdout=subprocess.PIPE,
		stderr=subprocess.PIPE,
		text=True
	)
	if r.returncode != 0:
		raise Exception(f"Unable to render PDF. pdftoppm exited with return code {r.returncode}. stderr: {r.stderr.decode("utf-8")}")

def run_melt(arguments):
	r = subprocess.run(
		[_get_melt_bin()] + arguments,
		stdout=subprocess.PIPE,
		stderr=subprocess.PIPE,
		text=True
	)
	if r.returncode != 0:
		raise Exception(f"Unable to run MLT. melt exited with return code {r.returncode}. stderr: {r.stderr.decode('utf-8')}")

def ffprobe_get_audio_length(audio_file : str) -> float:
	"""
	Uses ffprobe to get the length of an audio file in seconds.
	"""
	ffprobe_cmd = [
		_get_ffprobe_bin(),
		"-i",
		f"{audio_file}",
		"-show_entries",
		"format=duration",
		"-v",
		"quiet",
		"-of", 
		"csv=p=0"
	]
	return float(subprocess.check_output(ffprobe_cmd).decode("utf-8"))

def ffmpeg_get_encoders() -> dict[str, dict[str, str]]:
	"""
	Parses the output of `ffmpeg -v 0 -encoders` into a dictionary structure.
	Returns:
		dict: A dictionary where keys are encoder names and values are descriptions.
	"""
	# Run the `ffmpeg` command to get the list of encoders
	try:
		result = subprocess.run([_get_ffmpeg_bin(), "-v", "0", "-encoders"], capture_output=True, text=True, check=True)
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