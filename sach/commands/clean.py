"""
This module implements the `se clean` command.
"""

import argparse

import sach
from sach.sach_help_formatter import SachHelpFormatter
import sach.formatting


def clean(plain_output: bool) -> int:
	"""
	Entry point for `se clean`.
	"""

	parser = argparse.ArgumentParser(description="Prettify and canonicalize individual XHTML, SVG, or CSS files, or all XHTML, SVG, or CSS files in a source directory.", prog="[command]sach[/] [subcommand]clean[/]", formatter_class=SachHelpFormatter)
	parser.add_argument("-v", "--verbose", action="store_true", help="Increase output verbosity.")
	parser.add_argument("targets", metavar="[path]TARGET[/]", nargs="+", help="An XHTML, SVG, or CSS file, or a directory containing XHTML, SVG, or CSS files.")
	args = parser.parse_args()

	console = sach.init_console()

	for filepath in sach.get_target_filenames(args.targets, (".xhtml", ".svg", ".opf", ".ncx", ".xml", ".css")):
		if args.verbose:
			console.print(sach.prep_output(f"Processing [path][link=file://{filepath}]{filepath}[/][/] ...", plain_output), end="")

		if filepath.suffix == ".css":
			with open(filepath, "r+", encoding="utf-8") as file:
				css = file.read()

				try:
					processed_css = sach.formatting.format_css(css)

					if processed_css != css:
						file.seek(0)
						file.write(processed_css)
						file.truncate()
				except sach.SachException as ex:
					sach.print_error(f"File: [path][link=file://{filepath}]{filepath}[/][/]: {ex}", args.verbose, plain_output=plain_output)
					return ex.code

		else:
			try:
				sach.formatting.format_xml_file(filepath)
			except sach.MissingDependencyException as ex:
				sach.print_error(ex)
				return ex.code
			except sach.SachException as ex:
				sach.print_error(f"File: [path][link=file://{filepath}]{filepath}[/][/]: {ex}", args.verbose, plain_output=plain_output)
				return ex.code
			except FileNotFoundError:
				sach.print_error(f"Invalid file: [path][link=file://{filepath}]{filepath}[/][/].", args.verbose, plain_output=plain_output)
				return sach.InvalidFileException.code

		if args.verbose:
			console.print(" done.")

	return 0
