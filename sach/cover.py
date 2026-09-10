#!/usr/bin/env python3
"""
Generate a book cover from a book's own metadata — no AI, no image generation.

The cover is composed procedurally with Pillow: a themed colour palette chosen
from the book's genre/subject (falling back to a stable hash of the title so the
same book always gets the same cover), a classic ruled frame, the author name,
the title set in a Vietnamese-capable serif, and a genre label.

Everything is deterministic: the same title + genre always produces the same
image, byte for byte, so covers can be regenerated and diffed.
"""

import hashlib
import unicodedata
from dataclasses import dataclass
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

# Vietnamese needs precomposed glyphs beyond Latin-1; DejaVu and Liberation both
# cover Latin Extended Additional. Ordered by preference: a serif for the title,
# then anything legible rather than failing.
_SERIF_FONTS = [
	"/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf",
	"/usr/share/fonts/truetype/liberation/LiberationSerif-Bold.ttf",
	"/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
	"/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
]

_SANS_FONTS = [
	"/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
	"/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
	"/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf",
]


@dataclass(frozen=True)
class Theme:
	"""A cover palette."""

	name: str
	background: str
	ink: str
	accent: str
	# True when the ground is dark, so text should be light.
	dark: bool = False


# Palettes are deliberately muted and print-like rather than screen-bright, so a
# generated cover sits naturally next to a scanned one.
THEMES: dict[str, Theme] = {
	"paper":        Theme("paper",        "#f2ead9", "#2e2a24", "#8a6d3b"),
	"classic":      Theme("classic",      "#ece6da", "#2b2822", "#6f6350"),
	"slate":        Theme("slate",        "#e8ebee", "#232a30", "#4c6472"),
	"drama":        Theme("drama",        "#f3e7e0", "#3a1f1a", "#8c3b2e"),
	"tragedy":      Theme("tragedy",      "#e6e3dc", "#241f1b", "#5c5148"),
	"satire":       Theme("satire",       "#f5efdf", "#2b2b2b", "#b3452f"),
	"poetry":       Theme("poetry",       "#f1edf7", "#2c2740", "#6b5b95"),
	"philosophy":   Theme("philosophy",   "#e9eef0", "#22303a", "#43606f"),
	"spirituality": Theme("spirituality", "#f0ede4", "#2b2a24", "#9a8b5a"),
	"travel":       Theme("travel",       "#eaf0e6", "#24302a", "#4f7a5a"),
	"children":     Theme("children",     "#fdf3e3", "#33301f", "#c98a2b"),
	"fantasy":      Theme("fantasy",      "#eae4f2", "#2a2340", "#5d4a8a"),
	"mystery":      Theme("mystery",      "#1e2226", "#e6e2d8", "#7f9db0", dark=True),
	"horror":       Theme("horror",       "#1d1b1f", "#e8e3d9", "#8a3030", dark=True),
	"cosmos":       Theme("cosmos",       "#1b2230", "#e4e8f0", "#5f86c4", dark=True),
}

# Fold the Standard Ebooks genre vocabulary (and common Vietnamese subject
# words) onto a palette.
GENRE_THEMES: dict[str, str] = {
	"fiction": "paper",
	"shorts": "paper",
	"memoir": "classic",
	"autobiography": "classic",
	"biography": "classic",
	"nonfiction": "slate",
	"comedy": "satire",
	"satire": "satire",
	"drama": "drama",
	"tragedy": "tragedy",
	"poetry": "poetry",
	"philosophy": "philosophy",
	"spirituality": "spirituality",
	"travel": "travel",
	"adventure": "travel",
	"children’s": "children",
	"children's": "children",
	"fantasy": "fantasy",
	"mystery": "mystery",
	"horror": "horror",
	"science fiction": "cosmos",
	# Vietnamese keywords, for books whose subject is Vietnamese.
	"tiểu thuyết": "paper",
	"truyện ngắn": "paper",
	"truyện dài": "paper",
	"hồi ký": "classic",
	"tự truyện": "classic",
	"thơ": "poetry",
	"kịch": "drama",
	"bi kịch": "tragedy",
	"trào phúng": "satire",
	"triết học": "philosophy",
	"tâm linh": "spirituality",
	"du ký": "travel",
	"thiếu nhi": "children",
	"khoa học viễn tưởng": "cosmos",
	"trinh thám": "mystery",
	"kinh dị": "horror",
}

# Stable fallback order for books with no useful genre metadata.
_FALLBACK_ORDER = ["paper", "classic", "slate", "poetry", "philosophy", "spirituality", "travel", "drama"]


def list_themes() -> list[str]:
	"""
	Return the available theme names, sorted.

	INPUTS
	None.

	OUTPUTS
	A sorted list of theme names.
	"""

	return sorted(THEMES)


def select_theme(title: str, genres: list[str] | None = None, subjects: list[str] | None = None, override: str | None = None) -> Theme:
	"""
	Choose a palette for a book.

	INPUTS
	title: The book title, used for the deterministic fallback.
	genres: `schema:genre` values from the metadata.
	subjects: `dc:subject` values from the metadata.
	override: An explicit theme name, which wins over everything else.

	OUTPUTS
	The chosen `Theme`.
	"""

	if override:
		if override not in THEMES:
			raise ValueError(f"Unknown theme: {override}. Available: {', '.join(list_themes())}")
		return THEMES[override]

	# Metadata first: an explicit genre is the strongest signal of the book's
	# theme, then a subject keyword.
	for value in list(genres or []) + list(subjects or []):
		needle = unicodedata.normalize("NFC", value).strip().lower()
		if needle in GENRE_THEMES:
			return THEMES[GENRE_THEMES[needle]]
		# Subjects are often compound ("England--Social life--19th century--Fiction").
		for part in needle.replace("--", " ").replace(",", " ").split():
			if part in GENRE_THEMES:
				return THEMES[GENRE_THEMES[part]]

	# Otherwise pick deterministically from the title, so the same book always
	# gets the same cover and different books tend to differ.
	digest = hashlib.sha256(unicodedata.normalize("NFC", title).encode("utf-8")).digest()
	return THEMES[_FALLBACK_ORDER[digest[0] % len(_FALLBACK_ORDER)]]


def _load_font(candidates: list[str], size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
	"""
	Load the first available font from a preference list.

	INPUTS
	candidates: Font file paths, most preferred first.
	size: The pixel size.

	OUTPUTS
	A loaded `ImageFont`.
	"""

	for path in candidates:
		if Path(path).is_file():
			try:
				return ImageFont.truetype(path, size)
			except OSError:
				continue

	# Last resort: Pillow's bundled bitmap font, so the command never hard-crashes.
	return ImageFont.load_default(size=size)


def _text_width(draw: ImageDraw.ImageDraw, text: str, font: ImageFont.FreeTypeFont, tracking: int) -> float:
	"""
	Measure a string including letter spacing.

	INPUTS
	draw: The draw context.
	text: The string to measure.
	font: The font to measure with.
	tracking: Extra pixels between characters.

	OUTPUTS
	The width in pixels.
	"""

	if not text:
		return 0.0
	return float(sum(draw.textlength(char, font=font) for char in text) + tracking * (len(text) - 1))


def _draw_tracked(draw: ImageDraw.ImageDraw, xy: tuple[float, float], text: str, font: ImageFont.FreeTypeFont, fill: str, tracking: int) -> None:
	"""
	Draw a string centred on `xy`, with letter spacing.

	INPUTS
	draw: The draw context.
	xy: The centre point.
	text: The string to draw.
	font: The font to draw with.
	fill: A colour string.
	tracking: Extra pixels between characters.

	OUTPUTS
	None
	"""

	x = xy[0] - _text_width(draw, text, font, tracking) / 2
	# Use the font's own metrics so diacritics above/below don't shift the line.
	ascent, descent = font.getmetrics()
	y = xy[1] - (ascent + descent) / 2 + descent * 0.5
	for char in text:
		draw.text((x, y), char, font=font, fill=fill, anchor="ls")
		x += draw.textlength(char, font=font) + tracking


def _wrap(text: str, draw: ImageDraw.ImageDraw, font: ImageFont.FreeTypeFont, tracking: int, max_width: float) -> list[str]:
	"""
	Greedily wrap a string to a maximum width.

	INPUTS
	text: The string to wrap.
	draw: The draw context.
	font: The font to measure with.
	tracking: Extra pixels between characters.
	max_width: The maximum line width in pixels.

	OUTPUTS
	A list of lines.
	"""

	words = text.split()
	lines: list[str] = []
	current = ""
	for word in words:
		candidate = f"{current} {word}".strip()
		if current and _text_width(draw, candidate, font, tracking) > max_width:
			lines.append(current)
			current = word
		else:
			current = candidate
	if current:
		lines.append(current)
	return lines


def _fit_title(draw: ImageDraw.ImageDraw, title: str, size: tuple[int, int], font_candidates: list[str]) -> tuple[ImageFont.FreeTypeFont, list[str], int, float]:
	"""
	Choose a font size and line breaks so the title fills its box without overflowing.

	INPUTS
	draw: The draw context.
	title: The title text.
	size: The image size, `(width, height)`.
	font_candidates: Font file preference list.

	OUTPUTS
	A tuple of the font, the wrapped lines, the tracking, and the line height.
	"""

	width, height = size
	max_width = width * 0.78
	max_height = height * 0.42
	tracking = 2

	for point_size in range(int(height * 0.16), 39, -2):
		font = _load_font(font_candidates, point_size)
		lines = _wrap(title, draw, font, tracking, max_width)
		line_height = (font.getmetrics()[0] + font.getmetrics()[1]) * 1.22
		block_height = line_height * len(lines)
		widest = max((_text_width(draw, line, font, tracking) for line in lines), default=0)
		if block_height <= max_height and widest <= max_width and len(lines) <= 4:
			return font, lines, tracking, line_height

	# Nothing fit: use the smallest size and accept the wrap.
	font = _load_font(font_candidates, 40)
	lines = _wrap(title, draw, font, tracking, max_width)
	return font, lines, tracking, (font.getmetrics()[0] + font.getmetrics()[1]) * 1.22


def render_cover(title: str, author: str | None = None, label: str | None = None, theme: Theme | None = None, size: tuple[int, int] = (1200, 1800)) -> Image.Image:
	"""
	Render a cover image.

	INPUTS
	title: The book title.
	author: The author name, if known.
	label: A short genre label printed near the foot (e.g. "TIỂU THUYẾT").
	theme: The palette; defaults to the "paper" theme.
	size: A `(width, height)` tuple; defaults to a 2:3 ratio.

	OUTPUTS
	A PIL `Image` in RGB mode.
	"""

	theme = theme or THEMES["paper"]
	width, height = size

	base = Image.new("RGB", (width, height), theme.background)
	draw = ImageDraw.Draw(base)

	# A soft edge darkening gives the flat fill some depth the way a printed
	# jacket catches light; purely procedural, no texture files.
	gradient = Image.radial_gradient("L").resize((width, height), Image.Resampling.LANCZOS)
	shadow = Image.new("RGB", (width, height), _shade(theme.background, 0.82))
	mask = gradient.point(lambda value: int(value * 0.35))
	base = Image.composite(shadow, base, mask)
	draw = ImageDraw.Draw(base)

	# Classic double rule frame.
	inset_outer = int(width * 0.045)
	inset_inner = inset_outer + max(4, int(width * 0.006))
	draw.rectangle([inset_outer, inset_outer, width - inset_outer, height - inset_outer], outline=theme.accent, width=max(2, int(width * 0.0022)))
	draw.rectangle([inset_inner, inset_inner, width - inset_inner, height - inset_inner], outline=theme.accent, width=max(1, int(width * 0.0012)))

	centre_x = width / 2

	# Author, near the head.
	if author:
		font = _load_font(_SANS_FONTS, int(height * 0.028))
		_draw_tracked(draw, (centre_x, height * 0.155), author.upper(), font, theme.ink, tracking=int(height * 0.006))

	# A rule with a lozenge, one above and one below the title block.
	_ornament(draw, (centre_x, height * 0.215), width * 0.20, theme.accent)

	# Title, optically centred in the upper-middle of the cover.
	font, lines, tracking, line_height = _fit_title(draw, title, size, _SERIF_FONTS)
	block_height = line_height * len(lines)
	top = height * 0.50 - block_height / 2
	for index, line in enumerate(lines):
		_draw_tracked(draw, (centre_x, top + line_height * (index + 0.5)), line, font, theme.ink, tracking)

	_ornament(draw, (centre_x, height * 0.735), width * 0.20, theme.accent)

	# Genre label near the foot.
	if label:
		font = _load_font(_SANS_FONTS, int(height * 0.024))
		_draw_tracked(draw, (centre_x, height * 0.80), label.upper(), font, theme.accent, tracking=int(height * 0.007))

	return base


def _shade(color: str, factor: float) -> str:
	"""
	Multiply a hex colour's channels, for shading.

	INPUTS
	color: A `#rrggbb` string.
	factor: The multiplier, e.g. `0.8` to darken.

	OUTPUTS
	A `#rrggbb` string.
	"""

	color = color.lstrip("#")
	channels = [int(color[i:i + 2], 16) for i in (0, 2, 4)]
	return "#" + "".join(f"{max(0, min(255, int(channel * factor))):02x}" for channel in channels)


def _ornament(draw: ImageDraw.ImageDraw, xy: tuple[float, float], width: float, color: str) -> None:
	"""
	Draw a small centred rule with a lozenge in the middle.

	INPUTS
	draw: The draw context.
	xy: The centre point.
	width: The total width of the ornament.
	color: A colour string.

	OUTPUTS
	None
	"""

	x, y = xy
	half = width / 2
	gap = max(10.0, width * 0.10)
	thickness = max(1, int(width * 0.012))
	draw.line([(x - half, y), (x - gap, y)], fill=color, width=thickness)
	draw.line([(x + gap, y), (x + half, y)], fill=color, width=thickness)
	radius = max(3.0, width * 0.030)
	draw.polygon([(x, y - radius), (x + radius, y), (x, y + radius), (x - radius, y)], fill=color)


def write_cover(output_path: Path, title: str, author: str | None = None, label: str | None = None, theme: Theme | None = None, size: tuple[int, int] = (1200, 1800), quality: int = 92) -> Path:
	"""
	Render a cover and save it as a JPEG.

	INPUTS
	output_path: Where to write the image.
	title: The book title.
	author: The author name, if known.
	label: A short genre label printed near the foot.
	theme: The palette; defaults to the "paper" theme.
	size: A `(width, height)` tuple.
	quality: JPEG quality, 1-95.

	OUTPUTS
	The path written.
	"""

	image = render_cover(title, author=author, label=label, theme=theme, size=size)
	output_path.parent.mkdir(parents=True, exist_ok=True)
	image.save(output_path, "JPEG", quality=quality, optimize=True, progressive=True)
	return output_path
