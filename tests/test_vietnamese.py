"""
Tests for the Vietnamese (tiếng Việt) adaptation of the sach toolset.

These cover the language-specific behaviours introduced in the fork:
NFC normalisation, hyphenation suppression, word counting, and language
detection.
"""

import unicodedata

import pytest

import sach
from sach import vietnamese
from sach.easy_xml import EasyXmlTree
import sach.formatting
import sach.typography

VI_TEXT = "Mọi người sinh ra đều được tự do và bình đẳng về nhân phẩm và quyền"


def test_vietnamese_language_detection() -> None:
	assert vietnamese.is_vietnamese("vi")
	assert vietnamese.is_vietnamese("vi-VN")
	assert vietnamese.is_vietnamese("vi-Latn-VN")
	assert not vietnamese.is_vietnamese("en")
	assert not vietnamese.is_vietnamese("fr-FR")
	assert not vietnamese.is_vietnamese(None)
	assert not vietnamese.is_vietnamese("")


def test_normalize_composes_nfd() -> None:
	decomposed = unicodedata.normalize("NFD", VI_TEXT)
	assert decomposed != VI_TEXT
	normalized = vietnamese.normalize(decomposed)
	assert normalized == unicodedata.normalize("NFC", VI_TEXT)
	assert normalized == VI_TEXT


def test_has_vietnamese_marks() -> None:
	assert vietnamese.has_vietnamese_marks(VI_TEXT)
	assert vietnamese.has_vietnamese_marks("à ố ự")  # even marked alphanumerics
	assert not vietnamese.has_vietnamese_marks("plain english text")


def test_word_count_ignores_normalisation_form() -> None:
	nfc = VI_TEXT
	nfd = unicodedata.normalize("NFD", nfc)
	assert sach.formatting.get_word_count(nfc) == sach.formatting.get_word_count(nfd) != 0


def test_hyphenate_skips_vietnamese() -> None:
	xhtml = f"""<?xml version="1.0" encoding="utf-8"?><html xmlns="http://www.w3.org/1999/xhtml" xml:lang="vi"><body><p>{VI_TEXT}</p></body></html>"""
	dom = EasyXmlTree(xhtml)
	# Language passed explicitly.
	out = sach.typography.hyphenate(dom, "vi", ignore_h_tags=True)
	assert sach.SHY_HYPHEN not in out
	# Language read from the document.
	out2 = sach.typography.hyphenate(EasyXmlTree(xhtml), None, ignore_h_tags=True)
	assert sach.SHY_HYPHEN not in out2


def test_hyphenate_still_hyphenates_english() -> None:
	xhtml = """<?xml version="1.0" encoding="utf-8"?><html xmlns="http://www.w3.org/1999/xhtml" xml:lang="en-US"><body><p>This word hyphens: internationalization</p></body></html>"""
	# English is handled by pyphen; if pyphen is available it will insert a shy
	# hyphen somewhere in a long word.
	out = sach.typography.hyphenate(EasyXmlTree(xhtml), "en-US", ignore_h_tags=True)
	assert sach.SHY_HYPHEN in out


def test_typogrify_composes_vietnamese_marks() -> None:
	source = unicodedata.normalize("NFD", f"<p>{VI_TEXT}.</p>")
	mark_count_before = source.count("\u0300") + source.count("\u0301") + source.count("\u0309") + source.count("\u0323") + source.count("\u0303")
	# typogrify normalises Vietnamese to NFC when marks are present, so the
	# composed result no longer contains standalone combining marks.
	result = sach.typography.typogrify(source)
	assert sach.vietnamese.normalize(result) == result
	mark_count_after = result.count("\u0300") + result.count("\u0301") + result.count("\u0309") + result.count("\u0323") + result.count("\u0303")
	assert mark_count_after < mark_count_before or mark_count_after == 0