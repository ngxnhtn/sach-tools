"""
This module implements the `se add-file` command.
"""

import argparse
import importlib.resources
import os
from pathlib import Path
import shutil

import sach
from sach.sach_help_formatter import SachHelpFormatter
from sach.sach_epub import SachEpub

def _copy_file(filename: str, dest_path: Path, force: bool) -> None:
	if not force and os.path.exists(dest_path):
		raise sach.FileExistsException(f"File [path][link={dest_path}]{dest_path}[/][/] exists. Use [flag]--force[/] to overwrite.")

	with importlib.resources.as_file(importlib.resources.files("sach.data.templates").joinpath(filename)) as src_path:
		shutil.copyfile(src_path, dest_path)


def _replace_language(file_path: Path, language: str | None) -> None:
	if language:
		with open(file_path, "r+", encoding="utf-8") as file:
			xhtml = file.read()
			xhtml = xhtml.replace("\"LANG\"", f"\"{language}\"")

			file.seek(0)
			file.write(xhtml)
			file.truncate()

def _insert_css(sach_epub: SachEpub, filename: str) -> None:
	with importlib.resources.as_file(importlib.resources.files("sach.data.templates").joinpath(filename)) as src_path:
		template_css = ""
		with open(src_path, "r", encoding="utf-8") as file:
			template_css = file.read()

	with open(sach_epub.content_path / "css" / "local.css", "r+", encoding="utf-8") as file:
		css = file.read()
		css += "\n" + template_css

		file.seek(0)
		file.write(css)
		file.truncate()

def add_file(plain_output: bool) -> int: # pylint: disable=unused-argument
	"""
	Entry point for `se add-file`.
	"""

	file_types = ["chapter", "dedication", "dramatis-personae", "endnotes", "epigraph", "glossary", "halftitlepage", "ignore", "loi", "part"]

	parser = argparse.ArgumentParser(description="Add a Vietnamese ebook template file and any accompanying CSS.", prog="[command]sach[/] [subcommand]add-file[/]", formatter_class=SachHelpFormatter)
	parser.add_argument("-f", "--force", dest="force", action="store_true", help="Overwrite any existing files.")
	parser.add_argument("file_type", metavar="FILE_TYPE", choices=file_types, help="The type of file to add; one of: " + ", ".join([f"[text]{file_type}[/]" for file_type in file_types]) + ".")
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
			match args.file_type:
				case "chapter":
					dest_path = sach_epub.content_path / "text/chapter-.xhtml"

					_copy_file("chapter-template-add-file.xhtml", dest_path, args.force)

					_replace_language(dest_path, sach_epub.language)

				case "dedication":
					dest_path = sach_epub.content_path / "text/dedication.xhtml"

					_copy_file("dedication.xhtml", dest_path, args.force)

					_replace_language(dest_path, sach_epub.language)

					_insert_css(sach_epub, "dedication.css")

				case "dramatis-personae":
					dest_path = sach_epub.content_path / "text/dramatis-personae.xhtml"

					_copy_file("dramatis-personae.xhtml", dest_path, args.force)

					_replace_language(dest_path, sach_epub.language)

					_insert_css(sach_epub, "dramatis-personae.css")

				case "endnotes":
					dest_path = sach_epub.content_path / "text/endnotes.xhtml"

					_copy_file("endnotes.xhtml", dest_path, args.force)

					_replace_language(dest_path, sach_epub.language)

				case "epigraph":
					dest_path = sach_epub.content_path / "text/epigraph.xhtml"

					_copy_file("epigraph.xhtml", dest_path, args.force)

					_replace_language(dest_path, sach_epub.language)

					_insert_css(sach_epub, "epigraph.css")

				case "glossary":
					dest_path = sach_epub.content_path / "text/glossary.xhtml"

					_copy_file("glossary.xhtml", dest_path, args.force)

					_replace_language(dest_path, sach_epub.language)

					_insert_css(sach_epub, "glossary.css")

				case "halftitlepage":
					subtitle = sach_epub.get_subtitle()

					src_path ="halftitlepage.xhtml"

					if subtitle:
						src_path = "halftitlepage-subtitle.xhtml"

					dest_path = sach_epub.content_path / "text/halftitlepage.xhtml"

					_copy_file(src_path, dest_path, args.force)

					_replace_language(dest_path, sach_epub.language)

					with open(dest_path, "r+", encoding="utf-8") as file:
						xhtml = file.read()

						xhtml = xhtml.replace(">TITLE<", f">{sach_epub.get_title()}<")

						if subtitle:
							xhtml = xhtml.replace(">SUBTITLE<", f">{subtitle}<")

						file.seek(0)
						file.write(xhtml)
						file.truncate()

				case "ignore":
					dest_path = sach_epub.path / "se-lint-ignore.xml"

					_copy_file("se-lint-ignore.xml", dest_path, args.force)

				case "loi":
					dest_path = sach_epub.content_path / "text/loi.xhtml"

					_copy_file("loi.xhtml", dest_path, args.force)

					_replace_language(dest_path, sach_epub.language)

				case "part":
					dest_path = sach_epub.content_path / "text/part-.xhtml"

					_copy_file("part-template.xhtml", dest_path, args.force)

					_replace_language(dest_path, sach_epub.language)

				case _:
					# Unrecognized, do nothing.
					pass


		except sach.SachException as ex:
			sach.print_error(ex)
			return_code = ex.code
			return return_code

	return return_code
