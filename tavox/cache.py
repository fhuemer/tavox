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

import hashlib
import datetime
import os
import shutil
import glob
import tempfile
import logging
import textwrap

from pathlib import Path

from .voices import Voice

logger = logging.getLogger("tavox")

def hash_text(text: str) -> str:
	return hashlib.sha256(text.encode("utf-8")).hexdigest()


class SampleDB:

	def __init__(self, path):
		self._path = path
		os.makedirs(self._path, exist_ok=True)

	def _add_sample_to_db(self, text: str, voice: Voice):
		sample_dir = tempfile.TemporaryDirectory(prefix="tavox_", delete=False)
		try:
			voice.generate_sample(text, sample_dir.name)
		except Exception as e:
			logger.error(f"Unable to synthesize sample \"{textwrap.shorten(text, 40)}\" with voice {voice.voice_id}")
			raise e

		sample_path = glob.glob(f"{sample_dir.name}/*")
		if len(sample_path) != 1:
			raise Exception("The Voice instance created an unexpected number of files.")
		sample_path = Path(sample_path[0])

		base_path = Path(f"{self._path}/{voice.voice_id}")
		os.makedirs(base_path, exist_ok=True)

		voice_info = voice.info
		if voice_info is not None:
			with open(f"{base_path}.info", "w") as info_file:
				info_file.write(voice_info)

		h = hash_text(text)

		extension = "".join(sample_path.suffixes)
		dest = Path(f"{base_path}/{h}{extension}")
		shutil.move(sample_path, dest)

		with open(f"{base_path}/{h}.text", "w") as text_file:
			text_file.write(text)

		sample_dir.cleanup()

	def _find_sample(self, text: str, voice: Voice) -> None | Path:
		h = hash_text(text)
		base_path = Path(f"{self._path}/{voice.voice_id}")
		text_file_path = Path(f"{base_path}/{h}.text")
		if text_file_path.exists():
			with open(text_file_path, "r") as text_file:
				if text_file.read() != text:  # hash collision?
					return None
				audio_file_candidates = [x for x in base_path.glob(f"{h}*") if x.suffix in (".wav", ".flac", ".mp3")]
				# mark the entry as used
				with open(f"{base_path}/{h}.last_used", "w") as f:
					f.write(f"{datetime.datetime.now()}")
				return audio_file_candidates[0]
		else:
			return None

	def get_sample(self, text: str, voice: Voice) -> Path:
		s = self._find_sample(text, voice)
		if s is None:
			self._add_sample_to_db(text, voice)
		return self._find_sample(text, voice)
