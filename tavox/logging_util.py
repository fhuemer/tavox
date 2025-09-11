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

import logging

class LevelFilter(logging.Filter):
	def __init__(self, level):
		super().__init__()
		self.level = level

	def filter(self, record):
		return record.levelno == self.level


class LevelRangeFilter(logging.Filter):
	def __init__(self, low, high):
		super().__init__()
		self.low = low
		self.high = high

	def filter(self, record):
		if self.low is None and self.high is None:
			return True
		elif self.high is None:
			return record.levelno >= self.low
		elif self.low is None:
			return record.levelno < self.high
		
		return self.low <= record.levelno < self.high