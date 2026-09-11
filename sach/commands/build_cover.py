"""
This module implements the `sach build-cover` command.
"""

import argparse
from pathlib import Path

import sach
import sach.cover
from sach.sach_help_formatter import SachHelpFormatter
from sach.sach_epub import SachEpub


def _read_metadata(directory: Path) -> tuple[str, str | None, list[str], list[str]]:
	"""
	Pull the title, author, genres and subjects out of an ebook source folder.

	INPUTS
	directory: The ebook source directory.

	OUTPUTS
	A `(title, author, genres, subjects)` tuple.
	"""

	epub = SachEpub(directory)

	titles = epub.metadata_dom.xpath("/package/metadata/dc:title/text()", str)
	if not titles:
		raise sach.InvalidSachEbookException(f"Couldn’t find a [xml]<dc:title>[/] element in the metadata of [path]{directory}[/].")

	authors = epub.metadata_dom.xpath("/package/metadata/dc:creator/text()", str)
	genres = epub.metadata_dom.xpath("/package/metadata/meta[@property='schema:genre']/text()", str)
	subjects = epub.metadata_dom.xpath("/package/metadata/dc:subject/text()", str)

	return titles[0], (authors[0] if authors else None), list(genres), list(subjects)


def build_cover(plain_output: bool) -> int:
	"""
	Entry point for `sach build-cover`.
	"""

	parser = argparse.ArgumentParser(description="Generate a cover image for an ebook from its own title, author, and genre metadata. The palette is chosen from the book's genre (falling back to a stable hash of its title), so the same book always gets the same cover. Nothing here is AI-generated: the cover is drawn procedurally.", prog="[command]sach[/] [subcommand]build-cover[/]", formatter_class=SachHelpFormatter)
	parser.add_argument("-a", "--author", dest="author", help="The author name, if the ebook directory doesn’t provide one.")
	parser.add_argument("-t", "--title", dest="title", help="The title, if the ebook directory doesn’t provide one.")
	parser.add_argument("-l", "--label", dest="label", help="A short genre label printed near the foot of the cover, e.g. [text]Tiểu thuyết[/]. Defaults to the book’s genre when it has one.")
	parser.add_argument("-o", "--output", dest="output", help="Where to write the JPEG. Defaults to [path]<DIRECTORY>/epub/images/cover.jpg[/].")
	parser.add_argument("-f", "--format", "--size", dest="format", help="A named cover format: [text]3:4[/] (default), [text]2:3[/], [text]1:1[/], [text]16:9[/], or an explicit [text]WIDTHxHEIGHT[/].")
	parser.add_argument("--theme", dest="theme", help="Force a palette instead of choosing one from the book’s metadata. Use [flag]--list-themes[/] to see the options.")
	parser.add_argument("--list-themes", dest="list_themes", action="store_true", help="List the available cover themes and exit.")
	parser.add_argument("--overwrite", dest="overwrite", action="store_true", help="Overwrite an existing cover file. Without this, an existing cover is left alone.")
	parser.add_argument("directory", metavar="[path]DIRECTORY[/]", nargs="?", help="An ebook source directory to read the metadata from.")
	args = parser.parse_args()

	if args.list_themes:
		for name in sach.cover.list_themes():
			theme = sach.cover.THEMES[name]
			print(f"{name}\t{theme.background}\t{theme.ink}\t{theme.accent}")
		return 0

	# Work out where the metadata comes from.
	directory = Path(args.directory).resolve() if args.directory else None
	title = args.title
	author = args.author
	genres: list[str] = []
	subjects: list[str] = []

	if directory:
		if not directory.is_dir():
			sach.print_error(f"Not a directory: [path]{directory}[/].", plain_output=plain_output)
			return sach.InvalidInputException.code
		try:
			meta_title, meta_author, genres, subjects = _read_metadata(directory)
		except sach.SachException as ex:
			sach.print_error(ex, plain_output=plain_output)
			return ex.code
		title = title or meta_title
		author = author or meta_author

	if not title:
		sach.print_error("No title given. Pass [flag]--title[/], or a source [path]DIRECTORY[/] to read the metadata from.", plain_output=plain_output)
		return sach.InvalidInputException.code

	try:
		theme = sach.cover.select_theme(title, genres=genres, subjects=subjects, override=args.theme)
	except ValueError as ex:
		sach.print_error(f"{ex}", plain_output=plain_output)
		return sach.InvalidInputException.code

	# Where does the image go?
	if args.output:
		output_path = Path(args.output).resolve()
	elif directory:
		output_path = directory / "epub" / "images" / "cover.jpg"
	else:
		sach.print_error("Nothing to do: pass a source [path]DIRECTORY[/] or an output path with [flag]--output[/].", plain_output=plain_output)
		return sach.InvalidInputException.code

	try:
		width, height = sach.cover.resolve_cover_size(args.format)
	except ValueError as ex:
		sach.print_error(f"{ex}", plain_output=plain_output)
		return sach.InvalidInputException.code

	if output_path.is_file() and not args.overwrite:
		sach.print_error(f"Refusing to overwrite the existing cover at [path]{output_path}[/]. Pass [flag]--overwrite[/] to replace it.", plain_output=plain_output)
		return sach.InvalidInputException.code

	# A genre doubles as a label when the book has no explicit one.
	label = args.label
	if not label and genres:
		label = genres[0]

	sach.cover.write_cover(output_path, title, author=author, label=label, theme=theme, size=(width, height))

	reason = "forced by --theme" if args.theme else ("chosen from the book’s genre" if (genres or subjects) and theme.name in sach.cover.GENRE_THEMES.values() else "chosen from the title")
	print(sach.prep_output(f"Wrote [path]{output_path}[/] ([text]{width}×{height}[/], theme [val]{theme.name}[/], {reason}).", plain_output))

	return 0
