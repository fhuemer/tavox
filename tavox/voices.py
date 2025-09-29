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
import logging
import hashlib
import base64
import json
import time

from abc import ABC, abstractmethod
from typing import Optional
from urllib.parse import urlparse

logger = logging.getLogger("tavox")


class Voice(ABC):

	@abstractmethod
	def generate_sample(self, text: str, dir_path: str | os.PathLike):
		pass

	@property
	@abstractmethod
	def voice_id(self) -> str:
		pass

	@property
	def info(self) -> str | None:
		return None


class CoquiTTS(Voice):

	def __init__(self, model: str):
		self._voice_id = f"coquiTTS/{model}"
		self._model = model

	def generate_sample(self, text: str, dir_path: str | os.PathLike):
		logger.info(f"[coquiTTS] generating: {textwrap.shorten(text, 40)}")
		r = subprocess.run(
			f"""tts --text "{text}" --model_name "{self._model}" --out_path={dir_path}/sample.wav""",
			stdout=subprocess.PIPE,
			stderr=subprocess.PIPE,
			shell=True
		)
		if r.returncode != 0:
			raise RuntimeError(f"[coquiTTS] Unable to generate TTS sample: {r.stderr}")

	@property
	def voice_id(self) -> str:
		return self._voice_id


class OpenAIAPIVoice(Voice):

	def __init__(self, voice: str, model: str, *, instructions: Optional[str] = None, base_url: Optional[str] = None, api_key: Optional[str] = None):
		self._voice = voice
		self._model = model
		self._base_url = base_url
		self._api_key = api_key

		instructions = instructions.strip() if instructions is not None else ""
		self._instructions = instructions

		self.service_name = "OpenAI"
		voice_id_base = "openai"
		if base_url is not None:
			p = urlparse(base_url)
			if p.netloc == "":
				raise ValueError("Invalid base_url")
			voice_id_base = f"{p.hostname}{p.path}"
			voice_id_base = voice_id_base.strip('/')
			self.service_name = f"{p.hostname}"

		voice_suffix = ""
		if instructions != "":
			instructions_hash = base64.urlsafe_b64encode(hashlib.sha256(instructions.encode("utf-8")).digest())[:24] # should be enough
			voice_suffix = f"_{instructions_hash.decode("utf-8")}"

		self._voice_id = f"{voice_id_base}/{model}/{voice}{voice_suffix}"
		self._client = None

	def _get_client(self):
		from openai import OpenAI
		if self._client is None:
			if self._base_url is None:
				# use the "offical" OpenAI API
				if self._api_key is not None:
					api_key = os.environ["OPENAI_API_KEY"]
				else:
					api_key = self._api_key
				self._client = OpenAI(api_key=api_key)
			else:
				self._client = OpenAI(api_key=self._api_key, base_url=self._base_url)
		return self._client

	def generate_sample(self, text: str, dir_path: str | os.PathLike):
		from openai import RateLimitError
		while True:
			try:
				logger.info(f"[{self.service_name}] generating: {textwrap.shorten(text, 40)}")
				r = self._get_client().audio.speech.create(model=self._model, voice=self._voice, instructions=self._instructions, response_format="wav", input=text)
				break
			except RateLimitError as e:
				logger.warning(f"[{self.service_name}] Rate limit exceeded, waiting 10 seconds...")
				time.sleep(10)
		r.write_to_file(f"{dir_path}/sample.wav")

	@property
	def voice_id(self) -> str:
		return self._voice_id
	
	@property
	def info(self) -> str | None:
		if self._instructions == "":
			return None
		return json.dumps({"instructions": self._instructions})


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
		raise ValueError(
			f"There already is a voice with the name '{name}'. Use the function deregister_voice to remove the conflicting voice or choose a different name."
		)

	if isinstance(voice, Voice):
		for k, v in _voice_dict.items():
			if isinstance(v, Voice) and v.voice_id == voice.voice_id:
				raise ValueError(
					f"There already exists a voice with the same voice_id: ({k}). Use the function deregister_voice to remove the conflicting voice or make sure your Voice instance provides a different 'voice_id'."
				)
	elif isinstance(voice, str):
		if voice == name:
			raise ValueError("A voice cannot reference itself.")
		if voice not in _voice_dict:
			raise ValueError(f"There is no voice with the name '{voice}'")
	else:
		raise TypeError("voice must be either a string or a Voice instance")

	_voice_dict[name] = voice


def deregister_voice(name: str):
	if name not in _voice_dict:
		raise ValueError(f"There is no voice with the name '{name}'")
	del _voice_dict[name]


# register OpenAI voices
for v in ["alloy", "ash", "coral", "echo", "fable", "nova", "onyx", "sage", "shimmer"]:
	register_voice(f"{v}_tts-1", OpenAIAPIVoice(v, "tts-1"))
	register_voice(f"{v}_tts-1-hd", OpenAIAPIVoice(v, "tts-1-hd"))
	register_voice(f"{v}_gpt-4o-mini-tts", OpenAIAPIVoice(v, "gpt-4o-mini-tts"))
	register_voice(f"{v}", f"{v}_tts-1")

# register coqui voices
register_voice("tacotron2-DDC", CoquiTTS("tts_models/en/ljspeech/tacotron2-DDC"))
register_voice("tacotron2", CoquiTTS("tts_models/en/ek1/tacotron2"))

# set the default voice
register_voice("default", "tacotron2-DDC")
