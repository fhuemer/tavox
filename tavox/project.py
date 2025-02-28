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

import os
from pathlib import Path
from typing import Optional
from datetime import timedelta

from .voices import Voice, get_voice
from .events import TimelineEvent, SpeakEvent, DelayEvent, ShowSlideRangeEvent, ShowSlideEvent, PlayAudioEvent


class TavoxProject:
	_current_slide: int
	_current_pdf: Optional[Path]
	_current_voice: Optional[Voice]
	timeline: list[TimelineEvent]
	resolution: tuple[int, int]

	def __init__(self):
		self._current_slide = 1
		self._current_pdf = None
		self._current_voice = get_voice("default")
		self.timeline = []
		self.resolution = (1920, 1080)

	def set_pdf(self, path: str | os.PathLike):
		abs_path = Path(path).absolute()
		if not abs_path.exists():
			raise FileNotFoundError(f"PDF file {path} does not exist!")
		self._current_pdf = abs_path

	def show_slide(self, slide: int):
		self._check_current_pdf()

		self._current_slide = slide
		self.timeline.append(ShowSlideEvent(pdf=self._current_pdf, slide=slide))

	def set_voice(self, voice: str | Voice):
		if isinstance(voice, str):
			self._current_voice = get_voice(voice)
		else:
			self._current_voice = voice

	def show_slide_range(self, start_slide: int, end_slide: int):
		self._check_current_pdf()

		self._current_slide = end_slide
		self.timeline.append(ShowSlideRangeEvent(pdf=self._current_pdf, start_slide=start_slide, end_slide=end_slide))

	def show_next_slide(self):
		self._check_current_pdf()

		self._current_slide += 1
		self.timeline.append(ShowSlideEvent(pdf=self._current_pdf, slide=self._current_slide))

	def speak(self, text: str):
		self.timeline.append(SpeakEvent(text=text, voice=self._current_voice))

	def delay(self, seconds: float):
		if seconds == 0:
			return
		self.timeline.append(DelayEvent(length=timedelta(seconds=seconds)))

	def play_audio(self, path: str | os.PathLike):
		path = Path(path).absolute()
		if not path.exists():
			raise FileNotFoundError(f"Tha audio file {path} does not exist!")
		self.timeline.append(PlayAudioEvent(audio_file=path))

	def get_all_pdfs(self):
		pdfs = set()
		for event in self.timeline:
			match event:
				case ShowSlideEvent() | ShowSlideRangeEvent():
					pdfs.add(event.pdf)

		return list(pdfs)

	def _check_current_pdf(self):
		if self._current_pdf is None:
			raise ValueError("No PDF set!")
