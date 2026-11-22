"""Copy guard: user-facing text must read like a person wrote it.

Fails the build on emoji, marketing-cliché wording or text glyphs standing
in for icons in the frontend source, the README and the docs. The lists
below are the project's own bar, not a style guide import: a security
console earns trust with plain words and real icons, not decoration.
"""
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

# Emoji and symbol blocks. Typographic punctuation used deliberately in the
# UI (em dash, ellipsis, middle dot, arrows, the multiplication sign used
# as a clear-search mark) is not in these ranges and stays allowed.
EMOJI = re.compile(
    r"[\U0001F000-\U0001FAFF\u2600-\u27BF\u2B00-\u2BFF\uFE0F]"
)
# Geometric shapes that render as icons when typed as text. Lucide icons
# exist for all of these; a glyph in source is a placeholder for one.
ICON_GLYPHS = set("◆▲△▽◇●○■□▪▫►◄")

# Marketing words the product must never say about itself. Word boundaries
# matter: the CSS token `nexus-elevated-bg` is not the word "elevate".
BANNED_WORDS = [
    "seamless", "supercharge", "elevate", "unlock", "revolution",
    "game-changer", "game changer", "ai-powered", "cutting-edge",
    "cutting edge", "next-gen", "next gen", "world-class", "superpower",
    "ultra-fast", "laser-focused",
]
BANNED = [re.compile(r"\b" + re.escape(word) + r"\b", re.IGNORECASE)
          for word in BANNED_WORDS]

# Playbook surface/motion patterns. The design playbook bans frosted
# surfaces, staggered entrances, shimmer, breathing motion, radial glows
# and hover lifts outright — the build fails if any of them comes back.
# These scan the frontend source only: the docs describe the ban in
# prose ("backdrop blur" with a space), which is not a code pattern.
SURFACE_PATTERNS = [
    ("backdrop blur", re.compile(r"backdrop-filter|backdropFilter|backdrop-blur")),
    ("staggered entrance", re.compile(r"staggerChildren|\.stagger\b")),
    ("shimmer", re.compile(r"shimmer")),
    ("entrance fade", re.compile(r"fadeUp")),
    ("radial glow", re.compile(r"radial-gradient")),
    ("breathing motion", re.compile(r"pulse-dot|animate-breathe")),
    ("hover lift", re.compile(r"translateY\(-2px\)")),
    ("dot-pattern background", re.compile(r"DotGrid")),
]


def _frontend_files():
    for path in sorted((ROOT / "frontend" / "src").rglob("*")):
        if path.suffix in {".tsx", ".ts", ".css"}:
            yield path


def _readable_files():
    for path in sorted((ROOT / "frontend" / "src").rglob("*")):
        if path.suffix in {".tsx", ".ts", ".css"}:
            yield path
    yield ROOT / "README.md"
    yield from sorted((ROOT / "docs").glob("*.md"))


class UserFacingCopyTests(unittest.TestCase):
    def test_no_emoji_or_icon_glyphs_in_user_facing_text(self):
        for path in _readable_files():
            text = path.read_text(encoding="utf-8")
            with self.subTest(path=str(path.relative_to(ROOT))):
                found = EMOJI.findall(text)
                self.assertEqual(found, [], f"emoji in {path.name}: {found[:5]}")
                glyphs = sorted(set(text) & ICON_GLYPHS)
                self.assertEqual(glyphs, [], f"icon glyphs in {path.name}: {glyphs}")

    def test_no_marketing_cliches_in_user_facing_text(self):
        for path in _readable_files():
            text = path.read_text(encoding="utf-8")
            with self.subTest(path=str(path.relative_to(ROOT))):
                for word, pattern in zip(BANNED_WORDS, BANNED):
                    self.assertIsNone(
                        pattern.search(text),
                        f"{word!r} in {path.relative_to(ROOT)}",
                    )

    def test_no_frosted_surfaces_or_decorative_motion(self):
        # Playbook checklist, enforced by the build: solid surfaces only,
        # no staggered entrances, no shimmer, no breathing motion, no
        # radial glows, no hover lifts, no dot-pattern backgrounds.
        for path in _frontend_files():
            text = path.read_text(encoding="utf-8")
            with self.subTest(path=str(path.relative_to(ROOT))):
                for name, pattern in SURFACE_PATTERNS:
                    self.assertIsNone(
                        pattern.search(text),
                        f"{name} pattern in {path.relative_to(ROOT)}",
                    )


if __name__ == "__main__":
    unittest.main()
