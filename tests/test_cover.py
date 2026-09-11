"""
Tests for the procedurally generated book covers (`sach build-cover`).

These assert that theme choice is derived from the book's metadata and is
deterministic, that a cover actually renders ink (including Vietnamese tone
marks), and that the JPEG is written in a form e-readers accept.
"""

from pathlib import Path

import pytest
from PIL import Image

import sach.cover


def test_theme_chosen_from_genre() -> None:
	assert sach.cover.select_theme("Any Title", genres=["Fiction"]).name == "paper"
	assert sach.cover.select_theme("Any Title", genres=["Poetry"]).name == "poetry"
	assert sach.cover.select_theme("Any Title", genres=["Horror"]).name == "horror"


def test_theme_chosen_from_vietnamese_keywords() -> None:
	# Vietnamese subject words must map onto a palette too.
	assert sach.cover.select_theme("Bất kỳ", subjects=["Tiểu thuyết"]).name == "paper"
	assert sach.cover.select_theme("Bất kỳ", subjects=["Thơ"]).name == "poetry"
	# Compound LCSH-style subjects are matched word by word.
	assert sach.cover.select_theme("Any Title", subjects=["England--Social life--19th century--Fiction"]).name == "paper"


def test_theme_override_wins() -> None:
	assert sach.cover.select_theme("Any Title", genres=["Fiction"], override="horror").name == "horror"
	with pytest.raises(ValueError):
		sach.cover.select_theme("Any Title", override="not-a-real-theme")


def test_theme_fallback_is_deterministic() -> None:
	first = sach.cover.select_theme("Sống mòn")
	second = sach.cover.select_theme("Sống mòn")
	assert first.name == second.name
	assert first.name in sach.cover.THEMES
	# Different titles should not all collapse onto one palette.
	names = {sach.cover.select_theme(f"Title {index}").name for index in range(40)}
	assert len(names) > 1


def test_render_cover_shape_and_ink() -> None:
	theme = sach.cover.THEMES["paper"]
	image = sach.cover.render_cover("Sống mòn", author="Nam Cao", label="Tiểu thuyết", theme=theme, size=(600, 900))
	assert image.mode == "RGB"
	assert image.size == (600, 900)

	# The cover must not be a flat fill: the frame, text, and vignette all add colour.
	colours = image.getcolors(maxcolors=1_000_000)
	assert colours is not None
	assert len(colours) > 50

	# There must be ink in the title band and in the author band.
	def ink_fraction(y0: float, y1: float) -> float:
		width, height = image.size
		band = image.crop((0, int(height * y0), width, int(height * y1))).convert("L")
		histogram = band.histogram()
		total = sum(histogram)
		return sum(histogram[:120]) / total

	assert ink_fraction(0.32, 0.66) > 0.01, "no ink in the title band"
	assert ink_fraction(0.13, 0.18) > 0.002, "no ink in the author band"


def test_write_cover_produces_readable_jpeg(tmp_path: Path) -> None:
	output = tmp_path / "epub" / "images" / "cover.jpg"
	written = sach.cover.write_cover(output, "Sống mòn", author="Nam Cao", theme=sach.cover.THEMES["paper"], size=(400, 600))
	assert written == output
	assert output.is_file()

	with Image.open(output) as image:
		assert image.format == "JPEG"
		assert image.size == (400, 600)
		assert image.mode == "RGB"


def test_vietnamese_tone_marks_are_actually_drawn() -> None:
	"""
	Guard against a cover whose Vietnamese text silently loses its diacritics.

	A real tone mark is drawn above or below the base letter, so the glyph's row
	profile shows an ink run, a gap, and then the body of the letter. A missing
	glyph would instead be replaced by a solid `.notdef` box with no gap.
	"""

	from PIL import ImageDraw, ImageFont

	font_path = next(path for path in sach.cover._SERIF_FONTS if Path(path).is_file())  # pylint: disable=protected-access
	font = ImageFont.truetype(font_path, 120)

	def profile(char: str) -> list[tuple[str, int]]:
		image = Image.new("L", (300, 300), 255)
		ImageDraw.Draw(image).text((50, 200), char, font=font, fill=0, anchor="ls")
		bbox = image.point(lambda value: 255 - value).getbbox()
		assert bbox, f"no ink at all for {char!r}"
		cropped = image.crop(bbox)
		width, height = cropped.size
		pixels = cropped.load()
		rows = [any(pixels[x, y] < 128 for x in range(width)) for y in range(height)]
		runs: list[tuple[str, int]] = []
		current, length = rows[0], 1
		for value in rows[1:]:
			if value == current:
				length += 1
			else:
				runs.append(("ink" if current else "gap", length))
				current, length = value, 1
		runs.append(("ink" if current else "gap", length))
		return runs

	# The bare letter is a single ink run.
	assert [kind for kind, _ in profile("o")] == ["ink"]

	# A tone mark forces an extra run with a gap separating it from the letter.
	for char in ("ộ", "ế", "ự"):
		kinds = [kind for kind, _ in profile(char)]
		assert kinds.count("gap") >= 1, f"{char!r} produced no gap — the mark wasn't drawn"
		assert kinds.count("ink") >= 2, f"{char!r} produced a single block (tofu)"


def test_resolve_cover_size_defaults_to_3x4() -> None:
	assert sach.cover.resolve_cover_size(None) == (900, 1200)
	assert sach.cover.resolve_cover_size("") == (900, 1200)


def test_resolve_cover_size_named_formats() -> None:
	assert sach.cover.resolve_cover_size("3:4") == (900, 1200)
	assert sach.cover.resolve_cover_size("3x4") == (900, 1200)
	assert sach.cover.resolve_cover_size("2:3") == (1200, 1800)
	assert sach.cover.resolve_cover_size("1:1") == (1200, 1200)
	assert sach.cover.resolve_cover_size("16:9") == (1600, 900)
	# Case-insensitive.
	assert sach.cover.resolve_cover_size("3:4".upper()) == (900, 1200)


def test_resolve_cover_size_explicit_dimensions() -> None:
	assert sach.cover.resolve_cover_size("900x1200") == (900, 1200)
	assert sach.cover.resolve_cover_size("900:1200") == (900, 1200)
	# Leading/trailing whitespace is tolerated.
	assert sach.cover.resolve_cover_size("  600x800  ") == (600, 800)


def test_resolve_cover_size_rejects_garbage() -> None:
	for bad in ("banana", "0x800", "1200x", "x1200", "12x34x56"):
		with pytest.raises(ValueError):
			sach.cover.resolve_cover_size(bad)
