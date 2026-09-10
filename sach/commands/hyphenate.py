"""
This module implements the `se hyphenate` command.
"""

import argparse

import sach
from sach.sach_help_formatter import SachHelpFormatter
import sach.typography


def hyphenate(plain_output: bool) -> int:
	"""
	Entry point for `se hyphenate`.
	"""

	parser = argparse.ArgumentParser(description="Insert soft hyphens at syllable breaks in XHTML files.", prog="[command]sach[/] [subcommand]hyphenate[/]", formatter_class=SachHelpFormatter)
	parser.add_argument("-i", "--ignore-h-tags", action="store_true", help="Don’t add soft hyphens to text in [xhtml]<h1-6>[/] tags.")
	parser.add_argument("-l", "--language", action="store", help="Specify the language for the XHTML files; if unspecified, defaults to the [attr]@xml:lang[/] or [attr]@lang[/] attribute of the root [xhtml]<html>[/] element.")
	parser.add_argument("-v", "--verbose", action="store_true", help="Increase output verbosity.")
	parser.add_argument("targets", metavar="[path]TARGET[/]", nargs="+", help="An XHTML file, or a directory containing XHTML files.")
	args = parser.parse_args()

	console = sach.init_console()

	for filename in sach.get_target_filenames(args.targets, ".xhtml"):
		if args.verbose:
			console.print(sach.prep_output(f"Processing [path][link=file://{filename}]{filename}[/][/] ...", plain_output), end="")

		with open(filename, "r+", encoding="utf-8") as file:
			xhtml = file.read()

			is_ignored, dom = sach.get_dom_if_not_ignored(xhtml, ["toc"])

			if not is_ignored and dom:
				processed_xhtml = sach.typography.hyphenate(dom, args.language, args.ignore_h_tags)

				if processed_xhtml != xhtml:
					file.seek(0)
					file.write(processed_xhtml)
					file.truncate()

		if args.verbose:
			console.print(" done.")

	return 0
