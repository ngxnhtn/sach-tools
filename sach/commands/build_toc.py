"""
This module implements the `se build-toc` command.
"""

import argparse

import sach
from sach.sach_help_formatter import SachHelpFormatter
from sach.sach_epub import SachEpub


def build_toc(plain_output: bool) -> int:
	"""
	Entry point for `se build-toc`.

	The meat of this function is broken out into the `sach_epub_generate_toc.py` module for readability and maintainability.
	"""

	parser = argparse.ArgumentParser(description="Generate the table of contents for the ebook’s source directory and update the ToC file.", prog="[command]sach[/] [subcommand]build-toc[/]", formatter_class=SachHelpFormatter)
	parser.add_argument("-s", "--stdout", action="store_true", help="Print to stdout instead of writing to the ToC file.")
	parser.add_argument("directories", metavar="[path]DIRECTORY[/]", nargs="+", help="A Vietnamese ebook source directory.")
	args = parser.parse_args()

	if args.stdout and len(args.directories) > 1:
		sach.print_error("Multiple directories are not allowed with the [flag]--stdout[/] option.", plain_output=plain_output)
		return sach.InvalidArgumentsException.code

	for directory in args.directories:
		try:
			sach_epub = SachEpub(directory)
		except sach.SachException as ex:
			sach.print_error(ex)
			return ex.code

		try:
			if args.stdout:
				print(sach_epub.generate_toc())
			else:
				toc = sach_epub.generate_toc()
				with open(sach_epub.toc_path, "w", encoding="utf-8") as file:
					file.write(toc)

		except sach.SachException as ex:
			sach.print_error(ex)
			return ex.code
		except FileNotFoundError:
			sach.print_error(f"Couldn’t open file: [path][link=file://{sach_epub.toc_path}]{sach_epub.toc_path}[/][/].", plain_output=plain_output)
			return sach.InvalidSachEbookException.code

	return 0
