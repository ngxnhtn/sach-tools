"""
This module implements the `se recompose-epub` command.
"""

import argparse
from pathlib import Path

import sach
from sach.sach_help_formatter import SachHelpFormatter
from sach.sach_epub import SachEpub


def recomposach_epub(plain_output: bool) -> int: # pylint: disable=unused-argument
	"""
	Entry point for `se recompose-epub`.
	"""

	parser = argparse.ArgumentParser(description="Recompose a Vietnamese ebook source directory into a single (X?)HTML5 file, and print to standard output.", prog="[command]sach[/] [subcommand]recompose-epub[/]", formatter_class=SachHelpFormatter)
	parser.add_argument("-e", "--extra-css-file", metavar="[path]FILE[/]", type=str, default=None, help="The path to an additional CSS file to include after any CSS files in the epub.")
	parser.add_argument("-i", "--image-files", action="store_true", help="Leave image [attr]@src[/] attributes as relative URLs instead of inlining as [text]data:[/] URIs.")
	parser.add_argument("-o", "--output", metavar="[path]FILE[/]", type=str, default="", help="A file to write output to instead of printing to standard output.")
	parser.add_argument("-x", "--xhtml", action="store_true", help="Output XHTML instead of HTML5.")
	parser.add_argument("directory", metavar="[path]DIRECTORY[/]", help="A Vietnamese ebook source directory.")
	args = parser.parse_args()

	try:
		sach_epub = SachEpub(args.directory)
		recomposed_epub = sach_epub.recompose(args.xhtml, Path(args.extra_css_file) if args.extra_css_file else None, args.image_files)

		if args.output:
			with open(args.output, "w", encoding="utf-8") as file:
				file.write(recomposed_epub)
		else:
			print(recomposed_epub)
	except sach.SachException as ex:
		sach.print_error(ex)
		return ex.code
	except Exception as ex:
		sach.print_error(f"Couldn’t recompose epub: {ex}")
		return sach.InvalidFileException.code

	return 0
