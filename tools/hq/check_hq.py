#!/usr/bin/env python3
"""Check the export tree against the publication rules. Standard library only."""
import argparse
import json
import re
import unicodedata
from pathlib import Path
from urllib.parse import unquote, urlsplit

# Exact (relative file, one-based line) entries only. No broad suppressions.
# Each entry must include the complete line, codes and a written reason.
LINE_ALLOWLIST = {}
ALLOWED_HOSTS = {
    "review.tizen.org", "download.tizen.org",
    "download.blender.org", "mango.blender.org", "peach.blender.org",
}
LITERALS = (
    "github", "githubusercontent", "lhmax2010", "autofdo_bolt_agent",
    "main branch", "hq branch", "orphan", "codex", "claude", "anthropic",
    "openai", "gpt", "kimi", "cline", "chatgpt", "llm-based", "pm review",
    "awaiting review", "internal main", "temp/", "/home/",
    "internal repository", "internal commit", "tools/profgen/board/",
)
URL_RE = re.compile(r"(?:https?|ssh|git|ftp)://[^\s<>\"'`]+", re.I)
INLINE_RE = re.compile(r"!?\[[^\]\n]*\]\(\s*(<[^>]+>|[^\s)]+)")
REF_RE = re.compile(r"^\s{0,3}\[[^\]]+\]:\s*(<[^>]+>|\S+)", re.M)
HTML_RE = re.compile(r"""(?:href|src)\s*=\s*["']([^"']+)["']""", re.I)

def is_cjk(char):
    n = ord(char)
    return any(a <= n <= b for a, b in [
        (0x2E80, 0x303F), (0x3040, 0x31FF), (0x3400, 0x4DBF),
        (0x4E00, 0x9FFF), (0xAC00, 0xD7AF), (0xF900, 0xFAFF),
        (0xFE10, 0xFE1F), (0xFE30, 0xFE4F), (0xFF00, 0xFFEF),
        (0x20000, 0x323AF),
    ])

def check_tree(root):
    root = Path(root).resolve()
    if not root.is_dir():
        raise ValueError("Input must be a worktree directory")
    errors, warnings, waived, links = [], [], [], []
    workspace = Path(__file__).resolve().parents[2]
    host_paths = {str(workspace), str(Path(__file__).absolute().parents[2])}
    def add(path, number, line, code, detail, warning=False):
        entry = dict(file=path, line=number, code=code, detail=detail)
        allow = LINE_ALLOWLIST.get((path, number))
        if allow and allow["line"] == line and code in allow["codes"]:
            entry["reason"] = allow["reason"]
            waived.append(entry)
        else:
            (warnings if warning else errors).append(entry)
    def check_destination(p, dest, number, line):
        dest = dest.strip("<>").rstrip(".,;")
        parts = urlsplit(dest)
        rel = p.relative_to(root).as_posix()
        if parts.scheme or parts.netloc:
            if (parts.scheme not in ("https", "http", "ssh")
                    or parts.hostname not in ALLOWED_HOSTS):
                add(rel, number, line, "url_not_allowed", dest)
            if parts.password is not None:
                add(rel, number, line, "credential_in_url", dest)
            return
        path = unquote(parts.path)
        target = (p.parent / path).resolve() if path else p
        try:
            target.relative_to(root)
        except ValueError:
            add(rel, number, line, "link_outside_tree", dest)
            return
        exists = target.exists()
        links.append(dict(file=rel, line=number, destination=dest, exists=exists))
        if not exists:
            add(rel, number, line, "missing_link", dest)

    files = []
    for p in sorted(root.rglob("*")):
        if ".git" in p.relative_to(root).parts:
            continue
        if p.is_symlink():
            try:
                p.resolve().relative_to(root)
            except ValueError:
                add(p.relative_to(root).as_posix(), 0, "", "symlink_outside_tree", str(p.readlink()))
                continue
        if not p.is_file():
            continue
        rel = p.relative_to(root).as_posix()
        files.append(rel)
        try:
            text = p.read_text(encoding="utf-8")
        except UnicodeError:
            add(rel, 0, "", "non_text_file", "Not UTF-8 text")
            continue
        lines = text.splitlines()
        for number, line in [(0, rel)] + list(enumerate(lines, 1)):
            lower = line.lower()
            for word in LITERALS:
                if word in lower:
                    add(rel, number, line, "forbidden:" + word, word)
            if re.search(r"(?<![A-Za-z0-9_])ai(?![A-Za-z0-9_])", line, re.I):
                add(rel, number, line, "forbidden:ai", "Standalone word")
            for host in host_paths:
                if host.lower() in lower:
                    add(rel, number, line, "host_workspace_path", host)
            for char in sorted(set(line)):
                if ord(char) > 127:
                    add(rel, number, line, "cjk_or_fullwidth" if is_cjk(char) else "non_ascii",
                        "U+%04X %s" % (ord(char), unicodedata.name(char, "UNNAMED")),
                        warning=not is_cjk(char))
            for match in URL_RE.finditer(line):
                check_destination(p, match.group(), number, line)
        if p.suffix.lower() in (".md", ".markdown"):
            for pattern in (INLINE_RE, REF_RE, HTML_RE):
                for match in pattern.finditer(text):
                    number = text.count("\n", 0, match.start()) + 1
                    check_destination(p, match.group(1), number, lines[number - 1])
    return dict(passed=not errors, files=len(files), violations=errors,
                warnings=warnings, whitelist_used=waived,
                whitelist_entries=[dict(file=k[0], line_number=k[1], **v)
                                   for k, v in LINE_ALLOWLIST.items()], links=links)

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("tree")
    parser.add_argument("--json", type=Path, help="Optional audit output outside the export tree")
    args = parser.parse_args()
    try:
        result = check_tree(args.tree)
    except (OSError, ValueError) as exc:
        result = dict(passed=False, violations=[dict(code="scan_error", detail=str(exc))])
    data = json.dumps(result, indent=2, ensure_ascii=True) + "\n"
    if args.json:
        args.json.write_text(data)
    print(data, end="")
    return 0 if result["passed"] else 1

if __name__ == "__main__":
    raise SystemExit(main())
