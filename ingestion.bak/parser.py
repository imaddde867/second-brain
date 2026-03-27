import hashlib
import re
from pathlib import Path
from dataclasses import dataclass
from typing import Optional

@dataclass
class ParsedNote:
    path: str
    title: str
    content: str
    tags: list[str]
    links: list[str]
    frontmatter: dict
    checksum: str

def parse_markdown(path: Path) -> ParsedNote:
    text = path.read_text(encoding="utf-8")
    frontmatter, body = _split_frontmatter(text)
    tags = _extract_tags(frontmatter, body)
    links = re.findall(r'\[\[([^\]]+)\]\]', body)
    title = frontmatter.get("title") or path.stem.replace("-", " ").title()
    checksum = hashlib.md5(text.encode()).hexdigest()
    return ParsedNote(
        path=str(path),
        title=title,
        content=body.strip(),
        tags=tags,
        links=links,
        frontmatter=frontmatter,
        checksum=checksum,
    )

def _split_frontmatter(text: str) -> tuple[dict, str]:
    import yaml
    if text.startswith("---"):
        end = text.find("---", 3)
        if end != -1:
            try:
                fm = yaml.safe_load(text[3:end]) or {}
                return fm, text[end+3:]
            except Exception:
                pass
    return {}, text

def _extract_tags(frontmatter: dict, body: str) -> list[str]:
    tags = list(frontmatter.get("tags", []))
    inline = re.findall(r'#([\w/\-äöå]+)', body)
    return list(set(tags + inline))
