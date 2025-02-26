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

import subprocess
import textwrap
import os
import shutil
import logging
import tempfile

from typing import Optional
from pathlib import Path

logger = logging.getLogger("tavox")


class Voice:
	voice_id: str

	def generate_sample(self, text: str, dir_path: str | os.PathLike):
		pass


class CoquiTTS(Voice):

	def __init__(self, model: str):
		self.voice_id = f"coquiTTS/{model}"
		self._model = model

	def generate_sample(self, text: str, dir_path: str | os.PathLike):
		logger.info(f"[coquiTTS] synthesizing sample: {textwrap.shorten(text, 40)}")
		r = subprocess.run(
			f"""tts --text "{text}" --model_name "{self._model}" --out_path={dir_path}/sample.wav""",
			stdout=subprocess.PIPE,
			stderr=subprocess.PIPE,
			shell=True
		)
		if r.returncode != 0:
			raise Exception(f"[coquiTTS] Unable to generate TTS sample: {r.stderr}")


class OpenAITTS(Voice):

	def __init__(self, voice: str):
		self.voice_id = f"openai/{voice}"
		self._voice = voice

	def generate_sample(self, text: str, dir_path: str | os.PathLike):
		from openai import OpenAI
		logger.info(f"[OpenAI] synthesizing sample: {textwrap.shorten(text, 40)}")
		client = OpenAI()
		r = client.audio.speech.create(model="tts-1", voice=self._voice, response_format="wav", input=text)
		r.write_to_file(f"{dir_path}/sample.wav")


_voice_dict: dict[str, str | Voice] = {}


def available_voices():
	return list(_voice_dict.keys())


def get_voice(voice: str) -> Voice:
	global _voice_dict
	if voice not in _voice_dict:
		raise ValueError(f"Voice {voice} does not exist")
	if isinstance(_voice_dict[voice], str):
		return get_voice(_voice_dict[voice])
	return _voice_dict[voice]


def register_voice(name: str, voice: str | Voice):
	#check voice id for uniqueness
	if name in _voice_dict:
		raise Exception(
			f"There already is a voice with the name '{name}'. Use the function deregister_voice to remove the conflicting voice or choose a different name."
		)

	if isinstance(voice, Voice):
		for k, v in _voice_dict.items():
			if isinstance(v, Voice) and v.voice_id == voice.voice_id:
				raise Exception(
					f"There already exists a voice with the same voice_id: ({k}). Use the function deregister_voice to remove the conflicting voice or make sure to provide Voice instance provides a different 'voice_id'. "
				)

	_voice_dict[name] = voice


def deregister_voice(name: str):
	pass


# register OpenAI voices
for v in ["alloy", "echo", "fable", "onyx", "nova", "shimmer"]:
	register_voice(v, OpenAITTS(v))

# register coqui voices
register_voice("tacotron2-DDC", CoquiTTS("tts_models/en/ljspeech/tacotron2-DDC"))
register_voice("tacotron2", CoquiTTS("tts_models/en/ek1/tacotron2"))

# set the default voice
register_voice("default", "tacotron2-DDC")
