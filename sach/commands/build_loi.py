"""
This module implements the `se build-loi` command.
"""

import argparse

import sach
from sach.sach_help_formatter import SachHelpFormatter
from sach.sach_epub import SachEpub

def build_loi(plain_output: bool) -> int:
	"""
	Entry point for `se build-loi`.
	"""

	parser = argparse.ArgumentParser(description="Update the LoI file based on all [xhtml]<figure>[/] elements that contain an [xhtml]<img>[/].", prog="[command]sach[/] [subcommand]build-loi[/]", formatter_class=SachHelpFormatter)
	parser.add_argument("-s", "--stdout", action="store_true", help="Print to stdout instead of writing to the LoI file.")
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
			xhtml = sach_epub.generate_loi()

			if args.stdout:
				print(xhtml)
			else:
				loi_path = sach_epub.loi_path or (sach_epub.content_path / "text/loi.xhtml")
				with open(loi_path, "w", encoding="utf-8") as file:
					file.write(xhtml)

		except sach.SachException as ex:
			sach.print_error(ex)
			return ex.code
		except FileNotFoundError:
			sach.print_error(f"Couldn’t open file: [path][link=file://{sach_epub.loi_path}]{sach_epub.loi_path}[/][/].", plain_output=plain_output)
			return sach.InvalidSachEbookException.code

	return 0
