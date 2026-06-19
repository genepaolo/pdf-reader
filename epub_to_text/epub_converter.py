#!/usr/bin/env python3
"""
EPUB to Text converter for TTS-friendly chapter exports.
"""

from __future__ import annotations

import json
import re
import zipfile
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from urllib.parse import unquote
import xml.etree.ElementTree as ET
from html.parser import HTMLParser
import html as html_module


EPUB_NS = {"opf": "http://www.idpf.org/2007/opf"}
XHTML_NS = {"xhtml": "http://www.w3.org/1999/xhtml"}
NCX_NS = {"ncx": "http://www.daisy.org/z3986/2005/ncx/"}

SERIES_TITLE = "Lord of Mysteries 2: Circle of Inevitability"


class _EpubBodyTextExtractor(HTMLParser):
    """Lenient XHTML/HTML text extraction when XML parsing fails."""

    # Only leaf blocks — never div/section/h1 or parent wrappers duplicate nested text.
    _BLOCK = frozenset({"p", "blockquote", "li"})
    _SKIP = frozenset({"script", "style", "nav", "head", "title", "meta", "link"})
    _SKIP_HEADING = frozenset({"h1", "h2", "h3", "h4", "h5", "h6"})

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self._skip_depth = 0
        self._heading_depth = 0
        self.paragraphs: List[str] = []
        self._buf: List[str] = []

    def handle_starttag(self, tag: str, attrs) -> None:
        t = tag.lower().split(":")[-1]
        if t in self._SKIP:
            self._skip_depth += 1
        elif t in self._SKIP_HEADING:
            self._heading_depth += 1

    def handle_endtag(self, tag: str) -> None:
        t = tag.lower().split(":")[-1]
        if t in self._SKIP and self._skip_depth:
            self._skip_depth -= 1
        elif t in self._SKIP_HEADING and self._heading_depth:
            self._heading_depth -= 1
        elif self._skip_depth == 0 and self._heading_depth == 0 and t in self._BLOCK:
            self._flush()

    def handle_data(self, data: str) -> None:
        if self._skip_depth == 0 and self._heading_depth == 0:
            self._buf.append(data)

    def _flush(self) -> None:
        text = "".join(self._buf).strip()
        self._buf = []
        if text:
            self.paragraphs.append(text)

    def close(self) -> None:
        super().close()
        if self._buf:
            self._flush()


@dataclass
class Chapter:
    href: str
    title: str
    chapter_number: int
    volume_number: int
    volume_name: str


def _chapter_header_line(chapter: Chapter) -> str:
    """Second line of written chapter files (colon after number for TTS pause)."""
    return f"Chapter {chapter.chapter_number}: {chapter.title}"


def _cmp_text(s: str) -> str:
    return re.sub(r"\s+", " ", (s or "").strip().lower())


def _should_skip_body_paragraph(text: str, chapter: Chapter) -> bool:
    """
    Drop EPUB heading echoes already represented by line 1–2 of the output file:
    <h1>, duplicate <p> chapter titles, 'Chapter N - N: Title', etc.
    """
    t = re.sub(r"\s+", " ", (text or "").strip())
    if not t:
        return True
    # Typical duplicate title line inside <p> (short); allow ASCII/en/em dash between numbers
    _dash = r"[\-\u2010\u2011\u2012\u2013\u2014\u2212]"
    if len(t) < 280:
        if re.match(r"^chapter\s+\d+\s*:\s*", t, re.IGNORECASE):
            return True
        if re.match(rf"^chapter\s+\d+\s*{_dash}\s*\d+\s*:\s*", t, re.IGNORECASE):
            return True
        if re.match(rf"^chapter\s+\d+\s*{_dash}\s*\d+\s*$", t, re.IGNORECASE):
            return True
    header = _chapter_header_line(chapter)
    if _cmp_text(t) == _cmp_text(header):
        return True
    if _cmp_text(t) == _cmp_text(chapter.title):
        return True
    # Nav / NCX style echo: "601 Strange Patient" (no word "Chapter") right after our header
    if len(t) < 280:
        num_title = f"{chapter.chapter_number} {chapter.title}"
        if _cmp_text(t) == _cmp_text(num_title):
            return True
        num_colon_title = f"{chapter.chapter_number}: {chapter.title}"
        if _cmp_text(t) == _cmp_text(num_colon_title):
            return True
    return False


def _finalize_chapter_body(body: str, chapter: Chapter) -> str:
    """
    Remove any leading blank blocks or title-echo paragraphs so body starts with real prose
    right after the two-line header written by _write_output.
    """
    chunks = body.split("\n\n")
    while chunks:
        first = chunks[0].strip()
        if not first:
            chunks.pop(0)
            continue
        if _should_skip_body_paragraph(first, chapter):
            chunks.pop(0)
            continue
        break
    return "\n\n".join(chunks).strip()


def _regex_body_text_fallback(html: str, chapter: Chapter) -> str:
    match = re.search(r"(?is)<body[^>]*>(.*)</body>", html)
    blob = match.group(1) if match else html
    blob = re.sub(r"(?is)<script[^>]*>.*?</script>", " ", blob)
    blob = re.sub(r"(?is)<style[^>]*>.*?</style>", " ", blob)
    parts: List[str] = []
    for raw_inner in re.findall(r"(?is)<p[^>]*>(.*?)</p>", blob):
        inner = re.sub(r"<[^>]+>", " ", raw_inner)
        inner = html_module.unescape(inner)
        inner = re.sub(r"\s+", " ", inner).strip()
        if inner and not _should_skip_body_paragraph(inner, chapter):
            parts.append(inner)
    return _finalize_chapter_body("\n\n".join(parts).strip(), chapter)


class EpubConverter:
    def __init__(self, output_dir: str = "formatted_text"):
        self.output_dir = Path(output_dir)

    def convert_epub(
        self,
        epub_path: str,
        project_name: Optional[str] = None,
        inspect_only: bool = False,
        volume_map_path: Optional[str] = None,
        series_title: Optional[str] = None,
    ) -> None:
        epub_file = Path(epub_path)
        if not project_name:
            project_name = epub_file.stem

        volume_map = self._load_volume_map(epub_file, volume_map_path)

        with zipfile.ZipFile(epub_file, "r") as zf:
            opf_rel_path = self._get_opf_path(zf)
            opf_root = ET.fromstring(zf.read(opf_rel_path))
            opf_base = Path(opf_rel_path).parent.as_posix()

            manifest, spine = self._read_manifest_spine(opf_root)
            toc_entries = self._read_toc_entries(zf, opf_root, manifest, opf_base)
            chapters = self._build_chapters(toc_entries, manifest, spine, opf_base, volume_map)

            if not chapters:
                raise ValueError("No chapters detected in EPUB TOC/spine.")

            self._print_hierarchy(chapters)
            if inspect_only:
                return

            self._write_output(project_name, chapters, zf, series_title or SERIES_TITLE)

    def _load_volume_map(self, epub_file: Path, explicit: Optional[str]) -> Optional[List[dict]]:
        path = self._resolve_volume_map_path(epub_file, explicit)
        if path is None:
            return None
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        volumes = data.get("volumes")
        if not volumes:
            return None
        print(f"Loaded volume map: {path} ({len(volumes)} volumes)")
        return volumes

    def _resolve_volume_map_path(self, epub_file: Path, explicit: Optional[str]) -> Optional[Path]:
        if explicit:
            p = Path(explicit)
            return p if p.is_file() else None
        candidates = [
            epub_file.parent / "volume_map.json",
            epub_file.parent.parent / "volume_map.json",
        ]
        for c in candidates:
            if c.is_file():
                return c
        return None

    def _get_opf_path(self, zf: zipfile.ZipFile) -> str:
        container_xml = ET.fromstring(zf.read("META-INF/container.xml"))
        rootfile = container_xml.find(".//{*}rootfile")
        if rootfile is None:
            raise ValueError("Invalid EPUB: OPF rootfile not found.")
        opf_path = rootfile.attrib.get("full-path")
        if not opf_path:
            raise ValueError("Invalid EPUB: rootfile full-path missing.")
        return opf_path

    def _read_manifest_spine(self, opf_root: ET.Element) -> Tuple[Dict[str, str], List[str]]:
        manifest: Dict[str, str] = {}
        for item in opf_root.findall(".//opf:manifest/opf:item", EPUB_NS):
            item_id = item.attrib.get("id")
            href = item.attrib.get("href")
            if item_id and href:
                manifest[item_id] = href

        spine: List[str] = []
        for itemref in opf_root.findall(".//opf:spine/opf:itemref", EPUB_NS):
            idref = itemref.attrib.get("idref")
            if idref:
                spine.append(idref)
        return manifest, spine

    def _read_toc_entries(
        self,
        zf: zipfile.ZipFile,
        opf_root: ET.Element,
        manifest: Dict[str, str],
        opf_base: str,
    ) -> List[Tuple[str, str, int]]:
        nav_path = self._get_nav_path(opf_root, manifest, opf_base)
        if nav_path:
            entries = self._parse_nav_xhtml(zf, nav_path)
            if entries:
                return entries

        ncx_path = self._get_ncx_path(opf_root, manifest, opf_base)
        if ncx_path:
            entries = self._parse_ncx(zf, ncx_path)
            if entries:
                return entries

        return []

    def _get_nav_path(self, opf_root: ET.Element, manifest: Dict[str, str], opf_base: str) -> Optional[str]:
        for item in opf_root.findall(".//opf:manifest/opf:item", EPUB_NS):
            props = item.attrib.get("properties", "")
            if "nav" in props.split():
                href = item.attrib.get("href")
                if href:
                    return self._resolve_href(opf_base, href)
        return None

    def _get_ncx_path(self, opf_root: ET.Element, manifest: Dict[str, str], opf_base: str) -> Optional[str]:
        spine = opf_root.find(".//opf:spine", EPUB_NS)
        if spine is not None:
            toc_id = spine.attrib.get("toc")
            if toc_id and toc_id in manifest:
                return self._resolve_href(opf_base, manifest[toc_id])

        for item in opf_root.findall(".//opf:manifest/opf:item", EPUB_NS):
            media_type = item.attrib.get("media-type", "")
            if media_type == "application/x-dtbncx+xml":
                href = item.attrib.get("href")
                if href:
                    return self._resolve_href(opf_base, href)
        return None

    def _parse_nav_xhtml(self, zf: zipfile.ZipFile, nav_path: str) -> List[Tuple[str, str, int]]:
        root = ET.fromstring(zf.read(nav_path))
        toc_nav = root.find(".//xhtml:nav[@epub:type='toc']", XHTML_NS)
        if toc_nav is None:
            toc_nav = root.find(".//xhtml:nav", XHTML_NS)
        if toc_nav is None:
            return []

        entries: List[Tuple[str, str, int]] = []
        ol = toc_nav.find("xhtml:ol", XHTML_NS)
        if ol is not None:
            self._walk_nav_ol(ol, nav_path, 0, entries)
        return entries

    def _walk_nav_ol(
        self,
        ol: ET.Element,
        nav_path: str,
        level: int,
        entries: List[Tuple[str, str, int]],
    ) -> None:
        for li in ol.findall("xhtml:li", XHTML_NS):
            a = li.find("xhtml:a", XHTML_NS)
            if a is not None:
                href = a.attrib.get("href", "").strip()
                title = self._normalize_text("".join(a.itertext()))
                if href and title:
                    entries.append((self._resolve_href(Path(nav_path).parent.as_posix(), href), title, level))
            child_ol = li.find("xhtml:ol", XHTML_NS)
            if child_ol is not None:
                self._walk_nav_ol(child_ol, nav_path, level + 1, entries)

    def _parse_ncx(self, zf: zipfile.ZipFile, ncx_path: str) -> List[Tuple[str, str, int]]:
        root = ET.fromstring(zf.read(ncx_path))
        entries: List[Tuple[str, str, int]] = []
        nav_map = root.find(".//ncx:navMap", NCX_NS)
        if nav_map is None:
            return entries
        self._walk_ncx_nodes(nav_map, ncx_path, 0, entries)
        return entries

    def _walk_ncx_nodes(
        self,
        parent: ET.Element,
        ncx_path: str,
        level: int,
        entries: List[Tuple[str, str, int]],
    ) -> None:
        for nav_point in parent.findall("ncx:navPoint", NCX_NS):
            text_node = nav_point.find("ncx:navLabel/ncx:text", NCX_NS)
            content_node = nav_point.find("ncx:content", NCX_NS)
            title = self._normalize_text(text_node.text if text_node is not None else "")
            src = content_node.attrib.get("src", "").strip() if content_node is not None else ""
            if src and title:
                entries.append((self._resolve_href(Path(ncx_path).parent.as_posix(), src), title, level))
            self._walk_ncx_nodes(nav_point, ncx_path, level + 1, entries)

    def _build_chapters(
        self,
        toc_entries: List[Tuple[str, str, int]],
        manifest: Dict[str, str],
        spine: List[str],
        opf_base: str,
        volume_map: Optional[List[dict]] = None,
    ) -> List[Chapter]:
        spine_hrefs: List[str] = []
        for idref in spine:
            href = manifest.get(idref)
            if href:
                spine_hrefs.append(self._resolve_href(opf_base, href))

        if not toc_entries:
            chapters: List[Chapter] = []
            for idx, href in enumerate(spine_hrefs, start=1):
                if not href.lower().endswith((".xhtml", ".html", ".htm")):
                    continue
                vn, vna = self._volume_from_map(idx, volume_map) if volume_map else (1, "Main Story")
                chapters.append(Chapter(href, f"Chapter {idx}", idx, vn, vna))
            return chapters

        if volume_map:
            return self._build_chapters_with_volume_map(toc_entries, volume_map)

        chapters: List[Chapter] = []
        current_volume_num = 1
        current_volume_name = "Main Story"
        current_chapter_num = 1

        for href, title, level in toc_entries:
            if self._is_volume_title(title, level):
                current_volume_num += 1 if chapters else 0
                current_volume_name = self._clean_volume_name(title)
                current_chapter_num = 1
                continue

            if not self._looks_like_chapter(title):
                continue

            chapter_title = self._clean_chapter_title(title)
            if not chapter_title:
                chapter_title = f"Chapter {current_chapter_num}"

            chapters.append(
                Chapter(
                    href=href,
                    title=chapter_title,
                    chapter_number=current_chapter_num,
                    volume_number=current_volume_num,
                    volume_name=current_volume_name,
                )
            )
            current_chapter_num += 1

        if not chapters:
            # Last-resort fallback: sequential chapters from spine
            for idx, href in enumerate(spine_hrefs, start=1):
                if href.lower().endswith((".xhtml", ".html", ".htm")):
                    chapters.append(Chapter(href, f"Chapter {idx}", idx, 1, "Main Story"))

        return chapters

    def _build_chapters_with_volume_map(
        self,
        toc_entries: List[Tuple[str, str, int]],
        volume_map: List[dict],
    ) -> List[Chapter]:
        """Flat TOC + JSON ranges (global chapter index in titles like '110: …')."""
        chapters: List[Chapter] = []
        next_fallback_num = 1
        seen_nums: set = set()

        for href, title, _level in toc_entries:
            if self._is_toc_noise(title):
                continue
            if not self._looks_like_chapter(title):
                continue

            chapter_title = self._clean_chapter_title(title)
            parsed = self._parse_leading_chapter_number(title)
            if parsed is not None:
                chapter_num = parsed
                next_fallback_num = max(next_fallback_num, chapter_num + 1)
            else:
                chapter_num = next_fallback_num
                next_fallback_num += 1

            if chapter_num in seen_nums:
                raise ValueError(f"Duplicate chapter index {chapter_num} in TOC ({title!r})")
            seen_nums.add(chapter_num)

            if not chapter_title:
                chapter_title = f"Section_{chapter_num}"

            vn, vname = self._volume_from_map(chapter_num, volume_map)
            chapters.append(
                Chapter(
                    href=href,
                    title=chapter_title,
                    chapter_number=chapter_num,
                    volume_number=vn,
                    volume_name=vname,
                )
            )

        chapters.sort(key=lambda c: c.chapter_number)
        return chapters

    def _parse_leading_chapter_number(self, title: str) -> Optional[int]:
        t = title.strip()
        m = re.match(r"^\s*(\d+)\s*:", t)
        if m:
            return int(m.group(1))
        m2 = re.match(r"^\s*chapter\s+(\d+)\b", t, re.IGNORECASE)
        return int(m2.group(1)) if m2 else None

    def _volume_from_map(self, chapter_num: int, volume_map: Optional[List[dict]]) -> Tuple[int, str]:
        if not volume_map:
            return 1, "Main_Story"
        for v in volume_map:
            lo = int(v["first_chapter"])
            hi = int(v["last_chapter"])
            if lo <= chapter_num <= hi:
                return int(v["number"]), str(v["title"])
        last = volume_map[-1]
        return int(last["number"]), str(last["title"])

    def _is_toc_noise(self, title: str) -> bool:
        t = self._normalize_text(title).lower()
        return t in {"information", "cover", "copyright", "metadata", "title page"}

    def _write_output(self, project_name: str, chapters: List[Chapter], zf: zipfile.ZipFile, series_title: str = SERIES_TITLE) -> None:
        project_dir = self.output_dir / self._safe_name(project_name)
        project_dir.mkdir(parents=True, exist_ok=True)

        for chapter in chapters:
            volume_dir_name = f"Volume_{chapter.volume_number}_{self._safe_name(chapter.volume_name)}"
            volume_dir = project_dir / volume_dir_name
            volume_dir.mkdir(parents=True, exist_ok=True)

            chapter_file_name = f"Chapter_{chapter.chapter_number}_{self._safe_name(chapter.title)}.txt"
            chapter_path = volume_dir / chapter_file_name

            chapter_text = self._extract_chapter_text(zf, chapter.href, chapter)
            with open(chapter_path, "w", encoding="utf-8") as f:
                f.write(f"{series_title}\n")
                f.write(f"{_chapter_header_line(chapter)}\n")
                f.write(f"{chapter_text}\n")

        print(f"\nCreated TTS output at: {project_dir}")
        print(f"Total chapters written: {len(chapters)}")

    def _extract_chapter_text(self, zf: zipfile.ZipFile, href: str, chapter: Chapter) -> str:
        base_href = href.split("#")[0]
        data = zf.read(base_href)
        try:
            return self._extract_from_xml_bytes(data, chapter)
        except ET.ParseError:
            return self._extract_from_html_bytes(data, chapter)

    def _extract_from_xml_bytes(self, data: bytes, chapter: Chapter) -> str:
        root = ET.fromstring(data)
        body = root.find(".//xhtml:body", XHTML_NS)
        if body is None:
            body = root.find(".//{http://www.w3.org/1999/xhtml}body")
        if body is None:
            body = root.find(".//{*}body")
        if body is None:
            return ""

        paragraphs: List[str] = []
        # Only leaf blocks — do not use div/section/h1 or parents duplicate all inner text.
        for elem in body.iter():
            local_name = elem.tag.split("}")[-1].lower()
            if local_name in {"script", "style", "nav"}:
                continue
            if local_name not in {"p", "blockquote", "li"}:
                continue
            text = self._normalize_text("".join(elem.itertext()))
            if not text or self._is_noise_line(text):
                continue
            if _should_skip_body_paragraph(text, chapter):
                continue
            paragraphs.append(text)

        deduped: List[str] = []
        prev = ""
        for line in paragraphs:
            if line != prev:
                deduped.append(line)
            prev = line

        return _finalize_chapter_body("\n\n".join(deduped).strip(), chapter)

    def _extract_from_html_bytes(self, data: bytes, chapter: Chapter) -> str:
        text = data.decode("utf-8", errors="replace")
        extractor = _EpubBodyTextExtractor()
        try:
            extractor.feed(text)
            extractor.close()
        except Exception:
            return _regex_body_text_fallback(text, chapter)
        parts = extractor.paragraphs
        deduped: List[str] = []
        prev = ""
        for line in parts:
            line = self._normalize_text(line)
            if not line or self._is_noise_line(line):
                continue
            if _should_skip_body_paragraph(line, chapter):
                continue
            if line != prev:
                deduped.append(line)
            prev = line
        return _finalize_chapter_body("\n\n".join(deduped).strip(), chapter)

    def _print_hierarchy(self, chapters: List[Chapter]) -> None:
        print("\nDetected hierarchy:")
        grouped: Dict[Tuple[int, str], List[Chapter]] = {}
        for ch in chapters:
            grouped.setdefault((ch.volume_number, ch.volume_name), []).append(ch)

        for (vnum, vname), vchapters in sorted(grouped.items(), key=lambda x: x[0][0]):
            print(f"  Volume {vnum}: {vname} ({len(vchapters)} chapters)")
            for ch in vchapters[:3]:
                print(f"    - Chapter {ch.chapter_number}: {ch.title}")
            if len(vchapters) > 3:
                print("    - ...")
        print(f"\nTotal detected chapters: {len(chapters)}")

    def _resolve_href(self, base: str, href: str) -> str:
        href = unquote(href).replace("\\", "/")
        if "://" in href:
            return href
        if "#" in href:
            raw, frag = href.split("#", 1)
            resolved = self._resolve_href(base, raw)
            return f"{resolved}#{frag}" if frag else resolved
        base_path = Path(base) if base else Path(".")
        return (base_path / href).as_posix().lstrip("./")

    def _normalize_text(self, text: str) -> str:
        text = text or ""
        text = re.sub(r"\s+", " ", text).strip()
        return text

    def _safe_name(self, value: str) -> str:
        value = self._normalize_text(value)
        value = re.sub(r"[<>:\"/\\|?*]", "_", value)
        value = re.sub(r"\s+", "_", value)
        value = re.sub(r"_+", "_", value).strip("._")
        return value[:120] if len(value) > 120 else value

    def _is_volume_title(self, title: str, level: int) -> bool:
        if level == 0 and re.search(r"\b(volume|book)\b", title, re.IGNORECASE):
            return True
        return bool(re.match(r"^\s*volume\s+\d+", title, re.IGNORECASE))

    def _looks_like_chapter(self, title: str) -> bool:
        return bool(re.search(r"\bchapter\b", title, re.IGNORECASE) or re.search(r"\d+", title))

    def _clean_volume_name(self, title: str) -> str:
        cleaned = re.sub(r"^\s*volume\s+\d+\s*[:\-]?\s*", "", title, flags=re.IGNORECASE).strip()
        return cleaned or "Main Story"

    def _clean_chapter_title(self, title: str) -> str:
        cleaned = re.sub(r"^\s*chapter\s*\d*\s*[:\-]?\s*", "", title, flags=re.IGNORECASE).strip()
        prev = None
        while prev != cleaned:
            prev = cleaned
            cleaned = re.sub(r"^\s*\d+\s*:\s*", "", cleaned).strip()
            cleaned = re.sub(r'^\s*\d+\s*"\s*', "", cleaned).strip()
        return cleaned or title.strip()

    def _is_noise_line(self, line: str) -> bool:
        lowered = line.lower()
        noise_markers = [
            "table of contents",
            "copyright",
            "all rights reserved",
            "click here",
        ]
        return any(marker in lowered for marker in noise_markers)
