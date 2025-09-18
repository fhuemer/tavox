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

from ._version import __version__
from .project import TavoxProject
from .script import speak, show_slide, show_slide_range, show_next_slide, set_pdf, delay, set_voice, activate_project
from .mlt import create_mlt
from .voices import available_voices, register_voice, Voice
from .external_tools import run_pdftoppm, run_melt, ffprobe_get_audio_length, ffmpeg_get_encoders
