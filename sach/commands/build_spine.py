"""
This module implements the `se build-spine` command.
"""

import argparse

import sach
from sach.sach_help_formatter import SachHelpFormatter
import sach.formatting
from sach.sach_epub import SachEpub


def build_spine(plain_output: bool) -> int:
	"""
	Entry point for `se build-spine`.
	"""

	parser = argparse.ArgumentParser(description="Generate the [xhtml]<spine>[/] element for the given Vietnamese ebook source directory and write it to the ebook’s metadata file.", prog="[command]sach[/] [subcommand]build-spine[/]", formatter_class=SachHelpFormatter)
	parser.add_argument("-s", "--stdout", action="store_true", help="Print to stdout instead of writing to the metadata file.")
	parser.add_argument("directories", metavar="[path]DIRECTORY[/]", nargs="+", help="A Vietnamese ebook source directory.")
	args = parser.parse_args()

	if args.stdout and len(args.directories) > 1:
		sach.print_error("Multiple directories are not allowed with the [flag]--stdout[/] option.", plain_output=plain_output)
		return sach.InvalidArgumentsException.code

	for directory in args.directories:
		try:
			sach_epub = SachEpub(directory)

			if args.stdout:
				print(sach_epub.generate_spine().to_string())
			else:
				nodes = sach_epub.metadata_dom.xpath("/package/spine")
				if nodes:
					for node in nodes:
						node.replace_with(sach_epub.generate_spine())
				else:
					for node in sach_epub.metadata_dom.xpath("/package"):
						node.append(sach_epub.generate_spine())

				with open(sach_epub.metadata_file_path, "w", encoding="utf-8") as file:
					file.write(sach.formatting.format_xml(sach_epub.metadata_dom.to_string()))

		except sach.SachException as ex:
			sach.print_error(ex)
			return ex.code

	return 0
