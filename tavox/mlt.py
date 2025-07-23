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
import uuid
import textwrap
import math
import logging
import platform
import glob
import shutil

from pathlib import Path
from dataclasses import dataclass
from datetime import timedelta

from .cache import SampleDB
from .project import TavoxProject
from .events import *
from .external_tools import run_pdftoppm, ffprobe_get_audio_length

logger = logging.getLogger("tavox")


@dataclass
class _MLTProject:
	project_file_path: Path
	fps: int
	width: int
	height: int
	pdf_image_dict: dict[Path, Path]
	producers_xml: str
	producers_dict: dict[Path, str]
	audio_playlist_xml: str
	video_playlist_xml: str
	total_length: int
	timeline: list[TimelineEvent]
	sample_db: SampleDB

	def get_frame_time(self) -> timedelta:
		return timedelta(microseconds=1000000 / self.fps)

	def get_aspect_ratio(self) -> tuple[int, int]:
		if self.width <= 0 or self.height <= 0:
			raise ValueError("Width and height must be positive integers")

		divisor = math.gcd(self.width, self.height)
		ratio = (self.width // divisor, self.height // divisor)

		if ratio == (8, 5):
			ratio = (16, 10)

		return ratio

	def print_timeline(self):
		for event in self.timeline:
			print(event)


# shotcut is very particular about how time periods are specified
def strfdelta(td: timedelta) -> str:
	secs = int(abs(td).total_seconds())

	hours, rem = divmod(secs, 3600)  # Seconds per hour: 60 * 60
	mins, secs = divmod(rem, 60)

	return f"{hours}:{mins:02d}:{secs:02d}.{td.microseconds:06d}"


def _render_pdfs(pdf_files: list[Path], mlt: _MLTProject) -> dict[Path, Path]:
	logger.info(f"project contains {len(pdf_files)} PDF(s)")

	unique_paths = []
	for pdf in pdf_files:
		logger.debug(f"processing {pdf}")
		dest_path = f"{mlt.project_file_path.parent}/{pdf.name}"
		while dest_path in unique_paths:
			dest_path = f"{mlt.project_file_path.parent}/{pdf.name}_{uuid.uuid4().hex}"
		unique_paths.append(dest_path)
		mlt.pdf_image_dict[pdf] = Path(dest_path).absolute()

		if mlt.pdf_image_dict[pdf].exists():
			raise Exception(
				f"file or directory {mlt.pdf_image_dict[pdf]} already exists in mlt project directory. Try to put the mlt project file in an empty directory!"
			)
		os.makedirs(mlt.pdf_image_dict[pdf])

	for pdf, dest in mlt.pdf_image_dict.items():
		logger.info(f"rendering {pdf.name} to {dest}/*.png")
		run_pdftoppm(["-png", "-r", "600", "-scale-to-y", f"{mlt.height}", "-scale-to-x", f"{mlt.width}", f"{pdf}", f"{dest}/slide"])


def _process_slide_events(mlt: _MLTProject):
	logger.info("processing show slide events")
	new_timeline = []
	for event in mlt.timeline:
		match event:
			case ShowSlideEvent():
				new_event = ShowImageEvent(
					image_file=Path(f"{mlt.pdf_image_dict[event.pdf]}/slide-{event.slide}.png").absolute()
				)
				new_timeline.append(new_event)
			case ShowSlideRangeEvent():
				frames = []
				for slide in range(event.start_slide, event.end_slide + 1):
					frames.append(
						StillFrame(
						image_file=Path(f"{mlt.pdf_image_dict[event.pdf]}/slide-{slide}.png").absolute(),
						duration=timedelta(0)
						)
					)
				new_timeline.append(ShowImageRangeEvent(frames=frames))
			case _:
				new_timeline.append(event)

	mlt.timeline = new_timeline


def _remove_unnecessary_cuts(mlt: _MLTProject):
	logger.info("removing unnecessary video cuts")
	new_timeline = []
	last_show_image_event = None
	for event in mlt.timeline:
		match event:
			case ShowImageEvent():
				if last_show_image_event != event:
					last_show_image_event = event
					new_timeline.append(event)
			case _:
				new_timeline.append(event)
	mlt.timeline = new_timeline


def _merge_speak_events(mlt: _MLTProject):
	logger.info("merging speak events")
	new_timeline = []
	current_speak = None
	for event in mlt.timeline:
		match event:
			case SpeakEvent():
				if current_speak is None:
					current_speak = event
				elif current_speak.voice == event.voice:
					# merge the commands
					current_speak = SpeakEvent(text=f"{current_speak.text} {event.text}", voice=current_speak.voice)
				else:
					# commands cannot be merged, add them separatly to the timeline
					new_timeline.append(current_speak)
					new_timeline.append(event)
			case _:
				if current_speak is not None:
					new_timeline.append(current_speak)
					current_speak = None
				new_timeline.append(event)

	if current_speak is not None:
		new_timeline.append(current_speak)
	mlt.timeline = new_timeline


def _process_speak_events(mlt: _MLTProject):
	logger.info("processing speak events")
	new_timeline = []
	for event in mlt.timeline:
		match event:
			case SpeakEvent():
				if event.text.strip() == "":
					#ignore empty speak commands
					continue
				path = mlt.sample_db.get_sample(event.text, event.voice)
				new_event = PlayAudioEvent(audio_file=path)
				new_timeline.append(new_event)
			case _:
				new_timeline.append(event)
	mlt.timeline = new_timeline


def _create_mlt_producers(mlt: _MLTProject):
	logger.info(f"creating producers")
	for idx, event in enumerate(mlt.timeline):
		match event:
			case ShowImageEvent():
				path = event.image_file
				producer_name = f"producer{idx}_{path.name}"
				mlt.producers_xml += textwrap.dedent(
					f"""
					<producer id="{producer_name}" in="00:00:00.000" out="03:59:59.960">
						<property name="length">04:00:00.000</property>
						<property name="resource">{path}</property>
					</producer>"""
				)
				mlt.producers_dict[path] = producer_name
			case ShowImageRangeEvent():
				for frame in event.frames:
					path = frame.image_file
					producer_name = f"producer{idx}_{path.name}"
					mlt.producers_xml += textwrap.dedent(
						f"""
						<producer id="{producer_name}" in="00:00:00.000" out="03:59:59.960">
							<property name="length">04:00:00.000</property>
							<property name="resource">{path}</property>
						</producer>"""
					)
					mlt.producers_dict[path] = producer_name
			case PlayAudioEvent():
				path = event.audio_file
				producer_name = f"producer{idx}_{path.name}"
				mlt.producers_xml += textwrap.dedent(
					f"""
					<producer id="{producer_name}">
						<property name="resource">{path}</property>
					</producer>"""
				)
				mlt.producers_dict[path] = producer_name


def _create_mlt_playlists(mlt: _MLTProject):

	def add_event_to_video_playlist(event: TimelineEvent, target_duration: int):
		match event:
			case ShowImageEvent():
				producer_id = mlt.producers_dict[event.image_file]
				mlt.video_playlist_xml += f"""<entry producer="{producer_id}" out="{frames_to_str(target_duration-1)}"/>\n"""
			case ShowImageRangeEvent():
				num_auto_frame_duration = 0
				frame_durations: list[int] = [int(x.duration.total_seconds() * mlt.fps) for x in event.frames]
				num_auto_frame_duration = sum([x == 0 for x in frame_durations])
				static_event_duration = sum(frame_durations)

				if static_event_duration >= target_duration:
					raise Exception(
						"Unable to create video timeline. The specified static time of a video event is longer than then accompanying audio track!"
					)

				#calculate the auto duration
				auto_duration = int((target_duration - static_event_duration) / num_auto_frame_duration)
				for i in range(len(frame_durations)):
					if frame_durations[i] == 0:
						frame_durations[i] = auto_duration

				static_event_duration = sum(frame_durations)

				# hold the last frame if necessary
				frame_durations[-1] += target_duration - static_event_duration

				for idx, frame in enumerate(current_video_event.frames):
					producer_id = mlt.producers_dict[frame.image_file]
					mlt.video_playlist_xml += f"""<entry producer="{producer_id}" out="{frames_to_str(frame_durations[idx]-1)}"/>\n"""
			case _:
				raise NotImplementedError()

	logger.info("creating playlists")
	to_frames = lambda d: int(d * mlt.fps)
	frames_to_str = lambda x: f"{int(x / mlt.fps)}:{x % mlt.fps}"

	current_video_event = mlt.timeline[0]
	if not isinstance(current_video_event, (ShowImageEvent, ShowImageRangeEvent)):
		raise Exception("first timeline entry must be a video event!")

	# time unit: frames
	current_video_event_duration: int = 0
	total_length: int = 0

	for event in mlt.timeline[1:] + [None]:
		match event:
			case DelayEvent():
				length = to_frames(event.length.total_seconds())
				current_video_event_duration += length
				mlt.audio_playlist_xml += f"""<blank length="{length}"/>\n"""
			case PlayAudioEvent():
				length = to_frames(ffprobe_get_audio_length(event.audio_file))
				current_video_event_duration += length
				mlt.audio_playlist_xml += f"""<entry producer="{mlt.producers_dict[event.audio_file]}" out="{length-1}"/>\n"""
			case _:
				add_event_to_video_playlist(current_video_event, current_video_event_duration)

				total_length += current_video_event_duration
				current_video_event_duration = 0
				current_video_event = event

	mlt.total_length = total_length
	logger.info(f"total length of video project: {mlt.get_frame_time() * mlt.total_length}")


def _create_mlt_project_file(mlt: _MLTProject):
	producers = textwrap.indent(mlt.producers_xml, "\t\t\t")
	video_playlist = textwrap.indent(mlt.video_playlist_xml, "\t\t\t\t")
	audio_playlist = textwrap.indent(mlt.audio_playlist_xml, "\t\t\t\t")
	aspect_ratio_num, aspect_ratio_den = mlt.get_aspect_ratio()

	# The profile is important as it determines the output resolution/framerate
	# If it is ommitted the project cannot be rendered!
	profile_xml = f"""<profile description="Custom" width="{mlt.width}" height="{mlt.height}" progressive="1" sample_aspect_num="1" sample_aspect_den="1" display_aspect_num="{aspect_ratio_num}" display_aspect_den="{aspect_ratio_den}" frame_rate_num="{mlt.fps}" frame_rate_den="1" colorspace="709"/>"""

	mlt_template = textwrap.dedent(
		f"""\
		<?xml version="1.0" standalone="no"?>
		<mlt LC_NUMERIC="C" version="7.24.0" producer="main_bin">
			{profile_xml}
			<playlist id="main_bin">
				<property name="xml_retain">1</property>
			</playlist>
			<producer id="black" in="00:00:00.000" out="{mlt.total_length-1}">
				<property name="length">{mlt.total_length}</property>
				<property name="eof">pause</property>
				<property name="resource">0</property>
				<property name="aspect_ratio">1</property>
				<property name="mlt_service">color</property>
				<property name="mlt_image_format">rgba</property>
				<property name="set.test_audio">0</property>
			</producer>
			<playlist id="background">
				<entry producer="black" in="00:00:00.000" out="{mlt.total_length-1}"/>
			</playlist>
			{producers}
			<playlist id="playlist0">
				<property name="shotcut:video">1</property>
				<property name="shotcut:name">V1</property>
				{video_playlist}
			</playlist>
			<playlist id="playlist1">
				<property name="shotcut:audio">1</property>
				<property name="shotcut:name">A1</property>
				{audio_playlist}
			</playlist>
			<tractor id="tractor0">
				<property name="shotcut">1</property>
				<property name="shotcut:projectAudioChannels">2</property>
				<property name="shotcut:projectFolder">0</property>
				<property name="shotcut:scaleFactor">2.207</property>
				<property name="shotcut:skipConvert">0</property>
				<track producer="background"/>
				<track producer="playlist0"/>
				<track producer="playlist1" hide="video"/>
			</tractor>
		</mlt>"""
	)

	with open(mlt.project_file_path, "w") as f:
		f.write(mlt_template)


def create_mlt(project: TavoxProject, path: str | os.PathLike, merge_speak_commands: bool = False):
	logger.debug("create_mlt()")

	mlt_project_file_path = Path(path)
	if mlt_project_file_path.exists():
		raise Exception(f"file {mlt_project_file_path} already exists!")
	logger.info(f"mlt project file: {mlt_project_file_path}")

	mlt_project_dir_path = mlt_project_file_path.parent
	if not mlt_project_dir_path.exists():
		raise Exception(f"directory {mlt_project_dir_path} does not exist!")

	mlt = _MLTProject(
		project_file_path=mlt_project_file_path,
		width=project.resolution[0],
		height=project.resolution[1],
		fps=25,
		timeline=project.timeline,
		pdf_image_dict={},
		producers_xml="\n",
		producers_dict={},
		audio_playlist_xml="\n",
		video_playlist_xml="\n",
		total_length=timedelta(0),
		sample_db=SampleDB(Path.home() / ".tavox_cache")
	)

	_render_pdfs(project.get_all_pdfs(), mlt)

	_process_slide_events(mlt)
	_remove_unnecessary_cuts(mlt)

	if merge_speak_commands:
		_merge_speak_events(mlt)

	_process_speak_events(mlt)

	_create_mlt_producers(mlt)
	_create_mlt_playlists(mlt)
	_create_mlt_project_file(mlt)
