"""
This module implements the `se renumber-endnotes` command.
"""

import argparse

import sach
from sach.sach_help_formatter import SachHelpFormatter
from sach.sach_epub import SachEpub


def renumber_endnotes(plain_output: bool) -> int:
	"""
	Entry point for `se renumber-endnotes`.
	"""

	parser = argparse.ArgumentParser(description="Renumber all endnotes and noterefs sequentially from the beginning, taking care to match noterefs and endnotes if possible.", prog="[command]sach[/] [subcommand]renumber-endnotes[/]", formatter_class=SachHelpFormatter)
	parser.add_argument("-b", "--brute-force", action="store_true", help="Renumber without checking that noterefs and endnotes match; may result in endnotes with empty backlinks or noterefs without matching endnotes.")
	parser.add_argument("-v", "--verbose", action="store_true", help="Increase output verbosity.")
	parser.add_argument("directories", metavar="[path]DIRECTORY[/]", nargs="+", help="A Vietnamese ebook source directory.")
	args = parser.parse_args()

	return_code = 0

	for directory in args.directories:
		try:
			sach_epub = SachEpub(directory)
		except sach.SachException as ex:
			sach.print_error(ex)
			return_code = ex.code
			return return_code

		try:
			if args.brute_force:
				sach_epub.recreate_endnotes()
			else:
				found_endnote_count, changed_endnote_count, change_list = sach_epub.generate_endnotes()
				if args.verbose:
					print(sach.prep_output(f"Found {found_endnote_count} endnote{'s' if found_endnote_count != 1 else ''} and changed {changed_endnote_count} endnote{'s' if changed_endnote_count != 1 else ''}.", plain_output))
					for change in change_list:
						print(f"{change.old_anchor}->{change.new_anchor} in {change.filename}")
		except sach.SachException as ex:
			sach.print_error(ex)
			return_code = ex.code
		except FileNotFoundError:
			sach.print_error("Couldn’t find [path]endnotes.xhtml[/].", plain_output=plain_output)
			return_code = sach.InvalidSachEbookException.code

	return return_code
