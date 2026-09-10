"""
This module implements the `se prepare-release` command.
"""

import argparse
from pathlib import Path

import sach
from sach.sach_help_formatter import SachHelpFormatter
from sach.sach_epub import SachEpub


def prepare_release(plain_output: bool) -> int:
	"""
	Entry point for `se prepare-release`.
	"""

	parser = argparse.ArgumentParser(description="Calculate work word count, insert release date if not yet set, and update modified date and revision number.", prog="[command]sach[/] [subcommand]prepare-release[/]", formatter_class=SachHelpFormatter)
	parser.add_argument("-r", "--no-revision", dest="revision", action="store_false", help="Don’t increment the revision number.")
	parser.add_argument("-v", "--verbose", action="store_true", help="Increase output verbosity.")
	parser.add_argument("-w", "--no-word-count", dest="word_count", action="store_false", help="Don’t calculate word count.")
	parser.add_argument("directories", metavar="[path]DIRECTORY[/]", nargs="+", help="A Vietnamese ebook source directory.")
	args = parser.parse_args()

	console =sach.init_console()

	for directory in args.directories:
		directory = Path(directory).resolve()

		if args.verbose:
			console.print(sach.prep_output(f"Processing [path][link=file://{directory}]{directory}[/][/] ...", plain_output))

		try:
			sach_epub = SachEpub(directory)

			if args.word_count:
				if args.verbose:
					console.print("\tUpdating word count and reading ease ...", end="")

				sach_epub.update_word_count()
				sach_epub.update_flesch_reading_ease()

				if args.verbose:
					console.print(" done.")

			if args.revision:
				if args.verbose:
					console.print("\tUpdating revision number ...", end="")

				sach_epub.set_release_timestamp()

				if args.verbose:
					console.print(" done.")
		except sach.SachException as ex:
			sach.print_error(ex)
			return ex.code

	return 0
