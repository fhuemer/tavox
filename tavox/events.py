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


from dataclasses import dataclass
from pathlib import Path
from datetime import timedelta

from .voices import Voice


class TimelineEvent:
	pass


@dataclass
class ShowSlideEvent(TimelineEvent):
	pdf: Path
	slide: int


@dataclass
class ShowSlideRangeEvent(TimelineEvent):
	pdf: Path
	start_slide: int
	end_slide: int


@dataclass
class SpeakEvent(TimelineEvent):
	text: str
	voice: Voice


@dataclass
class DelayEvent(TimelineEvent):
	length: timedelta


@dataclass
class PlayAudioEvent(TimelineEvent):
	audio_file: Path


@dataclass
class ShowImageEvent(TimelineEvent):
	image_file: Path


@dataclass
class StillFrame:
	image_file: Path
	duration: timedelta


@dataclass
class ShowImageRangeEvent(TimelineEvent):
	frames: list[StillFrame]
