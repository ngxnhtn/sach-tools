"""
This module implements the `se semanticate` command.
"""

import argparse

import sach
from sach.sach_help_formatter import SachHelpFormatter
import sach.formatting


def semanticate(plain_output: bool) -> int:
	"""
	Entry point for `se semanticate`.
	"""

	parser = argparse.ArgumentParser(description="Automatically add semantics to Vietnamese ebook source directories.", prog="[command]sach[/] [subcommand]semanticate[/]", formatter_class=SachHelpFormatter)
	parser.add_argument("-v", "--verbose", action="store_true", help="Increase output verbosity.")
	parser.add_argument("targets", metavar="[path]TARGET[/]", nargs="+", help="An XHTML file, or a directory containing XHTML files.")
	args = parser.parse_args()

	console = sach.init_console()
	return_code = 0

	for filename in sach.get_target_filenames(args.targets, ".xhtml"):
		if args.verbose:
			console.print(sach.prep_output(f"Processing [path][link=file://{filename}]{filename}[/][/] ...", plain_output), end="")

		try:
			with open(filename, "r+", encoding="utf-8") as file:
				xhtml = file.read()

				is_ignored, _ = sach.get_dom_if_not_ignored(xhtml, ["imprint", "copyright-page", "toc", "loi"])

				if not is_ignored:
					processed_xhtml = sach.formatting.semanticate(xhtml)

					if processed_xhtml != xhtml:
						file.seek(0)
						file.write(processed_xhtml)
						file.truncate()
		except FileNotFoundError:
			sach.print_error(f"Couldn’t open file: [path][link=file://{filename}]{filename}[/][/].", plain_output=plain_output)
			return_code = sach.InvalidInputException.code
		except (sach.InvalidXmlException, sach.InvalidXhtmlException) as ex:
			sach.print_error(f"Invalid XML: [path][link=file://{filename}]{filename}[/][/]: {ex}", plain_output=plain_output)
			return_code = sach.InvalidInputException.code

		if args.verbose:
			console.print(" done.")

	return return_code
