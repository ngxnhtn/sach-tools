"""
This module implements the `se typogrify` command.
"""

import argparse
import html

import sach
from sach.sach_help_formatter import SachHelpFormatter
import sach.typography


def typogrify(plain_output: bool) -> int:
	"""
	Entry point for `se typogrify`.
	"""

	parser = argparse.ArgumentParser(description="Apply some scriptable typography rules from the Vietnamese ebook typography manual to XHTML files.", prog="[command]sach[/] [subcommand]typogrify[/]", formatter_class=SachHelpFormatter)
	parser.add_argument("-n", "--no-quotes", dest="quotes", action="store_false", help="Don’t convert to smart quotes before doing other adjustments.")
	parser.add_argument("-v", "--verbose", action="store_true", help="Increase output verbosity.")
	parser.add_argument("targets", metavar="[path]TARGET[/]", nargs="+", help="An XHTML file, or a directory containing XHTML files.")
	args = parser.parse_args()

	console = sach.init_console()
	return_code = 0

	for filename in sach.get_target_filenames(args.targets, (".xhtml", ".opf")):
		if args.verbose:
			console.print(sach.prep_output(f"Processing [path][link=file://{filename}]{filename}[/][/] ...", plain_output), end="")

		try:
			with open(filename, "r+", encoding="utf-8") as file:
				xhtml = file.read()

				is_ignored, dom = sach.get_dom_if_not_ignored(xhtml, ["titlepage", "imprint", "copyright-page"])

				if not is_ignored:
					if dom:
						processed_xhtml = ""

						# Is this a metadata file?
						# Typogrify metadata except for URLs, dates, and LoC subjects.
						if dom.xpath("/package"):
							for node in dom.xpath("/package/metadata/dc:*[normalize-space(.) and local-name() != 'subject' and local-name() != 'source' and local-name() != 'date' and local-name() != 'identifier'] | /package/metadata/meta[normalize-space(.) and not(re:test(., '^[a-z]+://[^\\s]+$') or @property='dcterms:modified')]"):
								node.text = html.unescape(node.text)

								node.text = sach.typography.typogrify(node.text)

								# Tweak: Word joiners and nbsp don't go in metadata.
								node.text = node.text.replace(sach.WORD_JOINER, "")
								node.text = node.text.replace(sach.NO_BREAK_SPACE, " ")

								# Typogrify escapes ampersands, and then lxml will also escape them again, so we unescape them before passing to lxml.
								if node.tag != "{http://purl.org/dc/elements/1.1/}description":
									node.text = node.text.replace("&amp;", "&").strip()

								processed_xhtml = dom.to_string()
						else:
							for node in dom.xpath("/html/body//img[@alt]"):
								node.set_attr("alt", sach.typography.typogrify(node.get_attr("alt"), args.quotes))

							processed_xhtml = dom.to_string()
							# Word joiners and nbsp don't belong in `alt` attributes, but that is handled by typogrify itself.
							processed_xhtml = sach.typography.typogrify(processed_xhtml, args.quotes)

						# Tweak: Word joiners and `nbsp` don't go in the ToC.
						if dom.xpath("/html/body//nav[contains(@epub:type, 'toc')]"):
							processed_xhtml = processed_xhtml.replace(sach.WORD_JOINER, "")
							processed_xhtml = processed_xhtml.replace(sach.NO_BREAK_SPACE, " ")

					else:
						processed_xhtml = sach.typography.typogrify(xhtml, args.quotes)

					if processed_xhtml != xhtml:
						file.seek(0)
						file.write(processed_xhtml)
						file.truncate()

			if args.verbose:
				console.print(" done.")

		except FileNotFoundError:
			sach.print_error(f"Couldn’t open file: [path][link=file://{filename}]{filename}[/][/].", plain_output=plain_output)
			return_code = sach.InvalidInputException.code

	return return_code
