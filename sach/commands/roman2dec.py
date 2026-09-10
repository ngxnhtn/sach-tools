"""
This module implements the `se roman2dec` command.
"""

import argparse
import sys

import roman

import sach
from sach.sach_help_formatter import SachHelpFormatter


def roman2dec(plain_output: bool) -> int:
	"""
	Entry point for `se roman2dec`.
	"""

	is_stdin_pipe = not sys.stdin.isatty()

	parser = argparse.ArgumentParser(description="Convert a Roman numeral to a decimal number.", prog="[command]sach[/] [subcommand]roman2dec[/]", formatter_class=SachHelpFormatter)
	parser.add_argument("-n", "--no-newline", dest="newline", action="store_false", help="Don’t end output with a newline.")
	parser.add_argument("numbers", metavar="NUMERAL", nargs="*" if is_stdin_pipe else "+", help="A Roman numeral.")
	args = parser.parse_args()

	lines: list[str] = []

	if is_stdin_pipe:
		for line in sys.stdin:
			lines.append(line.rstrip("\n"))

	for line in args.numbers:
		lines.append(line)

	for line in lines:
		try:
			if args.newline:
				print(roman.fromRoman(line.upper()))
			else:
				print(roman.fromRoman(line.upper()), end="")
		except roman.InvalidRomanNumeralError:
			sach.print_error(f"Not a Roman numeral: [text]{line}[/]", plain_output=plain_output)
			return sach.InvalidInputException.code

	return 0
