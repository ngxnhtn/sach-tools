"""
This module implements the `se shift-endnotes` command.
"""

import argparse

import sach
from sach.sach_help_formatter import SachHelpFormatter
from sach.sach_epub import SachEpub


def shift_endnotes(plain_output: bool) -> int: # pylint: disable=unused-argument
	"""
	Entry point for `se shift-endnotes`.
	"""

	parser = argparse.ArgumentParser(description="Increment or decrement the specified endnote and all following endnotes by a specified amount.", prog="[command]sach[/] [subcommand]shift-endnotes[/]", formatter_class=SachHelpFormatter)
	group = parser.add_mutually_exclusive_group(required=True)
	group.add_argument("-d", "--decrement", metavar="NUMBER", type=sach.is_positive_integer, help="Decrement the target endnote number and all following endnotes by this amount.")
	group.add_argument("-i", "--increment", metavar="NUMBER", type=sach.is_positive_integer, help="Increment the target endnote number and all following endnotes by this amount.")
	parser.add_argument("target_endnote_number", metavar="ENDNOTE_NUMBER", type=sach.is_positive_integer, help="The endnote number to start shifting at.")
	parser.add_argument("directory", metavar="[path]DIRECTORY[/]", help="A Vietnamese ebook source directory.")
	args = parser.parse_args()

	return_code = 0

	try:
		if args.increment is not None:
			step = args.increment
		else:
			step = args.decrement * -1

		sach_epub = SachEpub(args.directory)
		sach_epub.shift_endnotes(args.target_endnote_number, step)

	except sach.SachException as ex:
		sach.print_error(ex)
		return_code = ex.code

	return return_code
