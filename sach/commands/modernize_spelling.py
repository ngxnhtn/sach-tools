"""
This module implements the `se modernize-spelling` command.
"""

import argparse

import sach
from sach.sach_help_formatter import SachHelpFormatter
import sach.spelling


def modernize_spelling(plain_output: bool) -> int:
	"""
	Entry point for `se modernize-spelling`.
	"""

	parser = argparse.ArgumentParser(description="Modernize spelling of some archaic words, and replace words that may be archaically compounded with a dash to a more modern spelling. For example, replace [text]ash-tray[/] with [text]ashtray[/].", prog="[command]sach[/] [subcommand]modernize-spelling[/]", formatter_class=SachHelpFormatter)
	parser.add_argument("-n", "--no-hyphens", dest="modernize_hyphenation", action="store_false", help="Don’t modernize hyphenation.")
	parser.add_argument("-v", "--verbose", action="store_true", help="Increase output verbosity.")
	parser.add_argument("targets", metavar="[path]TARGET[/]", nargs="+", help="An XHTML file, or a directory containing XHTML files.")
	args = parser.parse_args()

	return_code = 0
	console = sach.init_console()

	for filename in sach.get_target_filenames(args.targets, ".xhtml"):
		if args.verbose:
			console.print(sach.prep_output(f"Processing [path][link=file://{filename}]{filename}[/][/] ...", plain_output), end="")

		try:
			with open(filename, "r+", encoding="utf-8") as file:
				xhtml = file.read()

				try:
					new_xhtml = sach.spelling.modernize_spelling(xhtml)

				except sach.InvalidLanguageException as ex:
					sach.print_error(f"{ex} File: [path][link=file://{filename}]{filename}[/][/]", plain_output=plain_output)
					return ex.code

				if args.modernize_hyphenation:
					new_xhtml = sach.spelling.modernize_hyphenation(new_xhtml)

				problem_spellings = sach.spelling.detect_problem_spellings(new_xhtml)

				for problem_spelling in problem_spellings:
					console.print(sach.prep_output(f"{('[path][link=file://' + str(filename) + ']' + filename.name + '[/][/]') + ': ' if not args.verbose else ''}{problem_spelling}", plain_output))

				if new_xhtml != xhtml:
					file.seek(0)
					file.write(new_xhtml)
					file.truncate()
		except FileNotFoundError:
			sach.print_error(f"Couldn’t open file: [path][link=file://{filename}]{filename}[/][/].", plain_output=plain_output)
			return_code = sach.InvalidInputException.code

		if args.verbose:
			console.print(" done.")

	return return_code
