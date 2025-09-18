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

from setuptools import setup

exec(open("tavox/_version.py").read())

setup(
	name="tavox",
	version=__version__,
	description="Text-to-speech tool for presentations",
	author="Florian Huemer",
	license="LGPLv3",
	packages=["tavox"],
	install_requires=["docopt"],
	entry_points={
		"console_scripts": [
			'tavox=tavox.cli:main',
		],
	},
	zip_safe=False
)

