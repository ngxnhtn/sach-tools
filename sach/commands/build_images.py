"""
This module implements the `se build-images` command.
"""

import argparse
from pathlib import Path

import sach
from sach.sach_help_formatter import SachHelpFormatter
import sach.images
from sach.sach_epub import SachEpub

def build_images(plain_output: bool) -> int:
	"""
	Entry point for `se build-images`.
	"""

	parser = argparse.ArgumentParser(description="Generate ebook cover and titlepages for Vietnamese ebooks, and then build ebook covers and titlepages, placing the output in [path]DIRECTORY/src/epub/images/[/].", prog="[command]sach[/] [subcommand]build-images[/]", formatter_class=SachHelpFormatter)
	parser.add_argument("-g", "--no-generate", action="store_true", help="Don’t generate new source cover/titlepage SVGs, only build existing ones.")
	parser.add_argument("-v", "--verbose", action="store_true", help="Increase output verbosity.")
	parser.add_argument("directories", metavar="[path]DIRECTORY[/]", nargs="+", help="A Vietnamese ebook source directory.")
	args = parser.parse_args()

	console = sach.init_console()

	for directory in args.directories:
		directory = Path(directory).resolve()

		if args.verbose:
			console.print(sach.prep_output(f"Processing [path][link=file://{directory}]{directory}[/][/] ...", plain_output))

		try:
			sach_epub = SachEpub(directory)

			if args.verbose:
				console.print("\tCleaning metadata ...", end="")

			# Remove useless metadata from cover source files.
			for file_path in directory.glob("**/cover.*"):
				sach.images.remove_image_metadata(file_path)

			# Only generate the cover if this is an SE ebook.
			if sach_epub.is_se_ebook and not args.no_generate:
				if args.verbose:
					console.print(" done.")
					console.print(sach.prep_output(f"\tGenerating [path][link=file://{directory / 'images/cover.svg'}]cover.svg[/][/] ...", plain_output), end="")

				sach_epub.generate_cover_svg()

			if args.verbose:
				console.print(" done.")
				console.print(sach.prep_output(f"\tBuilding [path][link=file://{directory / 'src/epub/images/cover.svg'}]cover.svg[/][/] ...", plain_output), end="")

			sach_epub.build_cover_svg()

			# Only generate the titlepage if this is an SE ebook.
			if sach_epub.is_se_ebook and not args.no_generate:
				if args.verbose:
					console.print(" done.")
					console.print(sach.prep_output(f"\tGenerating [path][link=file://{directory / 'images/titlepage.svg'}]titlepage.svg[/][/] ...", plain_output), end="")

				sach_epub.generate_titlepage_svg()

			if args.verbose:
				console.print(" done.")
				console.print(sach.prep_output(f"\tBuilding [path][link=file://{directory / 'src/epub/images/titlepage.svg'}]titlepage.svg[/][/] ...", plain_output), end="")

			sach_epub.build_titlepage_svg()

			if args.verbose:
				console.print(" done.")

			if args.verbose:
				console.print("\tOptimizing PNGs ...", end="")

			# Optimize PNGs that we're distributing.
			for file_path in directory.glob("src/epub/**/*.png"):
				sach.images.optimize_png(file_path)

			if args.verbose:
				console.print(" done.")

		except sach.SachException as ex:
			sach.print_error(ex)
			return ex.code

	return 0
