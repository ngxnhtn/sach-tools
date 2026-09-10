"""
This module implements the `se titlecase` command.
"""

import argparse
import sys

import sach
from sach.sach_help_formatter import SachHelpFormatter
import sach.formatting


def titlecase(plain_output: bool) -> int: # pylint: disable=unused-argument
	"""
	Entry point for `se titlecase`.
	"""

	is_stdin_pipe = not sys.stdin.isatty()

	parser = argparse.ArgumentParser(description="Convert a string to titlecase. Pass a language with `--language` to get that language’s title convention: Vietnamese returns the string in sentence case, because Vietnamese does not use title case.", prog="[command]sach[/] [subcommand]titlecase[/]", formatter_class=SachHelpFormatter)
	parser.add_argument("-l", "--language", dest="language", help="The language of the string, e.g. `vi`. Vietnamese strings are returned in sentence case.")
	parser.add_argument("-n", "--no-newline", dest="newline", action="store_false", help="Don’t end output with a newline.")
	parser.add_argument("titles", metavar="STRING", nargs="*" if is_stdin_pipe else "+", help="A string.")
	args = parser.parse_args()

	lines: list[str] = []

	if is_stdin_pipe:
		for line in sys.stdin:
			lines.append(line.rstrip("\r\n"))

	for line in args.titles:
		lines.append(line)

	for line in lines:
		if args.newline:
			print(sach.formatting.titlecase(line, args.language))
		else:
			print(sach.formatting.titlecase(line, args.language), end="")

	return 0
