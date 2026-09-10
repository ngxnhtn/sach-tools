#!/usr/bin/env python3
"""
Vietnamese (tiếng Việt) editorial helpers for the `sach` toolset.

This module centralises the conventions of Vietnamese book editing that differ
from the English toolset it was forked from:

- **Unicode normalisation:** Vietnamese on-line (quốc ngữ) text is written with
  precomposed Unicode (NFC) as the house representation. Diacritics attach to
  the base Latin letter; mark-only decompositions (NFD) are discouraged because
  they render inconsistently across e-readers. `normalize()` therefore converts
  text to NFC.
- **Hyphenation:** standard Vietnamese publishing practice does *not* hyphenate
  words at line ends. Words are space-separated syllables already, so end-of-
  line hyphenation is not used. The hyphenator is therefore skipped for
  Vietnamese rather than inserting soft hyphens.
- **Word counting:** a Vietnamese lexical word is one or more syllables written
  without internal spaces; boundary counting therefore uses the space as the
  primary separator, which the generic word counter already approximates.
- **Quotation:** Vietnamese uses the same double/single curly quotation marks
  (“ ” ‘ ’) as the English convention, so no quote-style conversion is applied.

The module is intentionally small and imports only the standard library so it
can be used from any submodule without introducing dependency cycles.
"""

import unicodedata


# The ISO language codes (and their regional variants) that identify Vietnamese
# book sources. Used to decide whether to apply Vietnamese-specific behaviour.
VIETNAMESE_LANGUAGES = frozenset({
	"vi",
	"vi-VN",
	"vi-VI",
	"vi-Latn",
	"vi-Latn-VN",
})


def is_vietnamese(language: str | None) -> bool:
	"""
	Return whether `language` identifies a Vietnamese text.

	INPUTS
	language: An ISO 639/3166 language code (e.g. "vi", "vi-VN"), or `None`.

	OUTPUTS
	`True` if the code is a known Vietnamese variant.
	"""

	if not language:
		return False
	return language.strip() in VIETNAMESE_LANGUAGES


def normalize(text: str) -> str:
	"""
	Normalise Vietnamese text to our house representation (NFC).

	Vietnamese is canonically represented with precomposed base letters plus
	combining tone marks where a precomposed code point exists. NFC composes
	those where possible, which is the representation used by Vietnamese
	publishers and e-readers.

	INPUTS
	text: A string of Vietnamese text in any normalisation form.

	OUTPUTS
	The same text composed to NFC (no other characters are changed).
	"""

	return unicodedata.normalize("NFC", text)


def has_vietnamese_marks(text: str) -> bool:
	"""
	Return whether a string contains Vietnamese diacritics.

	This is a light heuristic used to decide whether Vietnamese handling should
	be applied even when the language attribute is absent or unreliable. It
	looks for the Vietnamese-specific precomposed letters Ă/Â/Ê/Ô/Ơ/Ư and the
	combining tone marks (acute, grave, hook above, tilde, dot below) that
	Vietnamese stacks onto those vowels.

	INPUTS
	text: A string to test.

	OUTPUTS
	`True` if the string contains Vietnamese letters or tone-mark characters.
	"""

	# Precomposed Vietnamese letters.
	vietnamese_letters = "ăâđêôơưĂÂĐÊÔƠƯ"
	# Tone marks (glyphs) used by Vietnamese on top of the base letters above.
	vietnamese_tone_glyphs = "áàảãạắằẳẵặấầẩẫậéèẻẽẹếềểễệíìỉĩịóòỏõọốồổỗộớờởỡợúùủũụứừửữựýỳỷỹỵÁÀẢÃẠẮẰẲẴẶẤẦẨẪẬÉÈẺẼẸẾỀỂỄỆÍÌỈĨỊÓÒỎÕỌỐỒỔỖỘỚỜỞỠỢÚÙỦŨỤỨỪỬỮỰÝỲỶỸỴ"
	# Combining tone marks (Mark, nonspacing) used by Vietnamese stacks:
	#   ́   accent aigu        ̀   accent grave
	#   ̉   hook above         ̣   dot below
	#   ̃   tilde
	combining_marks = "\u0301\u0300\u0309\u0323\u0303"

	for char in text:
		if char in vietnamese_letters or char in vietnamese_tone_glyphs:
			return True
		if char in combining_marks:
			return True
	return False