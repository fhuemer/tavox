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

_project = None


def activate_project(p):
	global _project
	_project = p


def set_voice(voice):
	_project.set_voice(voice)


def set_pdf(path: str | os.PathLike):
	_project.set_pdf(path)


def show_slide(slide: int):
	_project.show_slide(slide)


def show_slide_range(start_slide: int, end_slide: int):
	_project.show_slide_range(start_slide, end_slide)


def show_next_slide():
	_project.show_next_slide()


def speak(text: str):
	_project.speak(text)


def delay(seconds: float):
	_project.delay(seconds)


def play_audio(path: str | os.PathLike):
	_project.play_audio(path)
