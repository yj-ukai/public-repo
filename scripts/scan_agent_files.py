#!/usr/bin/env python3
"""AIエージェント設定ファイルから、人間には見えにくい指示を検出する。

使い方:
  python3 scripts/scan_agent_files.py            # リポジトリを検査
  python3 scripts/scan_agent_files.py <dir>      # プラグインなど任意のディレクトリを検査
"""
import pathlib
import re
import sys

TARGET_GLOBS = [
    "CLAUDE.md", "**/CLAUDE.md", "AGENTS.md",
    ".claude/**/*", ".mcp.json",
    # プラグイン・マーケットプレイスのカタログ（5-4）
    ".claude-plugin/**/*",
    # プラグインのレビュー用
    "skills/**/*.md", "agents/**/*.md", "commands/**/*.md", "hooks/**/*",
]

# ゼロ幅文字・双方向制御文字・Unicodeタグ文字・文中のBOM
INVISIBLE = re.compile(
    "[\u200b-\u200f\u202a-\u202e\u2060-\u2064\u2066-\u2069\ufeff"
    "\U000e0000-\U000e007f]"
)
HTML_COMMENT = re.compile(r"<!--(.*?)-->", re.S)

def iter_targets(root: pathlib.Path):
    seen = set()
    for pattern in TARGET_GLOBS:
        for p in root.glob(pattern):
            if p.is_file() and "node_modules" not in p.parts and p not in seen:
                seen.add(p)
                yield p

def main() -> int:
    root = pathlib.Path(sys.argv[1]) if len(sys.argv) > 1 else pathlib.Path(".")
    errors = 0
    for path in iter_targets(root):
        text = path.read_text(encoding="utf-8", errors="replace")
        for lineno, line in enumerate(text.splitlines(), 1):
            for m in INVISIBLE.finditer(line):
                print(f"::error file={path},line={lineno}::"
                      f"不可視文字 U+{ord(m.group()):04X} を検出")
                errors += 1
        if path.suffix == ".md":
            for m in HTML_COMMENT.finditer(text):
                lineno = text.count("\n", 0, m.start()) + 1
                print(f"::warning file={path},line={lineno}::"
                      "HTMLコメントがあります（レンダリング時に非表示）。内容を確認してください")
    return 1 if errors else 0

if __name__ == "__main__":
    sys.exit(main())