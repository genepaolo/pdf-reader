#!/usr/bin/env python3
"""
Count how many "volumes" an EPUB exposes in its navigation (NCX / EPUB3 nav).

Important: Many fan or conversion EPUBs list every chapter at the top level of the
TOC with no Volume sections. In that case this script reports 0 structural volumes
(and explains why). That does not mean the story only has one printed volume — it
means the file did not encode volume breaks in the TOC.
"""

from __future__ import annotations

import argparse
import re
import sys
import zipfile
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import List, Optional, Tuple
from urllib.parse import unquote

EPUB_NS = {"opf": "http://www.idpf.org/2007/opf"}
XHTML_NS = {"xhtml": "http://www.w3.org/1999/xhtml"}
NCX_NS = {"ncx": "http://www.daisy.org/z3986/2005/ncx/"}

VOLUME_LABEL_RE = re.compile(
    r"(?is)^\s*(volume|book|part)\s+(\d+|[ivxlcdm]+)\b",
)


def _get_opf_path(zf: zipfile.ZipFile) -> str:
    container = ET.fromstring(zf.read("META-INF/container.xml"))
    rootfile = container.find(".//{*}rootfile")
    if rootfile is None:
        raise ValueError("Invalid EPUB: missing container rootfile.")
    path = rootfile.attrib.get("full-path")
    if not path:
        raise ValueError("Invalid EPUB: rootfile full-path missing.")
    return path


def _manifest_spine(opf_root: ET.Element) -> Tuple[dict, List[str], Optional[str]]:
    manifest: dict = {}
    for item in opf_root.findall(".//opf:manifest/opf:item", EPUB_NS):
        iid = item.attrib.get("id")
        href = item.attrib.get("href")
        if iid and href:
            manifest[iid] = {
                "href": href,
                "props": item.attrib.get("properties") or "",
                "media": item.attrib.get("media-type") or "",
            }
    spine_ids: List[str] = []
    spine_el = opf_root.find(".//opf:spine", EPUB_NS)
    toc_id = spine_el.attrib.get("toc") if spine_el is not None else None
    for itemref in opf_root.findall(".//opf:spine/opf:itemref", EPUB_NS):
        idref = itemref.attrib.get("idref")
        if idref:
            spine_ids.append(idref)
    return manifest, spine_ids, toc_id


def _resolve_href(base: str, href: str) -> str:
    href = unquote(href).replace("\\", "/")
    if "#" in href:
        raw, _ = href.split("#", 1)
        href = raw
    base_path = Path(base) if base else Path(".")
    return (base_path / href).as_posix().lstrip("./")


def _parse_ncx_volume_stats(zf: zipfile.ZipFile, ncx_path: str) -> Tuple[int, int, List[str]]:
    """
    Returns:
      - structural_sections: top-level NCX navPoints that contain nested navPoints
        (often volume / part groupings).
      - label_volume_entries: nav labels whose text looks like a volume heading.
      - sample_labels: first few matching labels for debugging.
    """
    root = ET.fromstring(zf.read(ncx_path))
    nav_map = root.find(".//ncx:navMap", NCX_NS)
    if nav_map is None:
        return 0, 0, []

    structural = 0
    label_hits: List[str] = []

    # Only top-level parents (nested TOC containers like Volume → chapters)
    for np in nav_map.findall("ncx:navPoint", NCX_NS):
        if np.findall("ncx:navPoint", NCX_NS):
            structural += 1

    # Collect all text labels that look like explicit volume lines (any depth)
    for text_el in root.iter():
        if text_el.tag.split("}")[-1].lower() != "text":
            continue
        if text_el.text:
            t = text_el.text.strip()
            if VOLUME_LABEL_RE.match(t):
                label_hits.append(t)

    return structural, len(label_hits), label_hits[:15]


def _parse_nav_volume_stats(zf: zipfile.ZipFile, nav_path: str) -> Tuple[int, int, List[str]]:
    root = ET.fromstring(zf.read(nav_path))
    toc_nav = root.find(".//xhtml:nav[@epub:type='toc']", XHTML_NS)
    if toc_nav is None:
        toc_nav = root.find(".//xhtml:nav", XHTML_NS)
    if toc_nav is None:
        return 0, 0, []

    structural = 0
    label_hits: List[str] = []

    def walk_ol(ol: ET.Element, depth: int) -> None:
        for li in ol.findall("xhtml:li", XHTML_NS):
            child_ol = li.find("xhtml:ol", XHTML_NS)
            a = li.find("xhtml:a", XHTML_NS)
            title = ""
            if a is not None:
                title = "".join(a.itertext()).strip()
            if depth == 0 and child_ol is not None:
                structural += 1
            if child_ol is not None:
                walk_ol(child_ol, depth + 1)
            if title and VOLUME_LABEL_RE.match(title):
                label_hits.append(title)

    top_ol = toc_nav.find("xhtml:ol", XHTML_NS)
    if top_ol is not None:
        walk_ol(top_ol, 0)

    return structural, len(label_hits), label_hits[:15]


def analyze_epub(epub_path: Path) -> None:
    with zipfile.ZipFile(epub_path, "r") as zf:
        opf_path = _get_opf_path(zf)
        opf_root = ET.fromstring(zf.read(opf_path))
        opf_base = Path(opf_path).parent.as_posix()
        manifest, _spine, toc_id = _manifest_spine(opf_root)

        nav_path: Optional[str] = None
        for mid, meta in manifest.items():
            if "nav" in meta["props"].split():
                nav_path = _resolve_href(opf_base, meta["href"])
                break

        ncx_path: Optional[str] = None
        if toc_id and toc_id in manifest:
            ncx_path = _resolve_href(opf_base, manifest[toc_id]["href"])
        if not ncx_path:
            for meta in manifest.values():
                if meta["media"] == "application/x-dtbncx+xml":
                    ncx_path = _resolve_href(opf_base, meta["href"])
                    break

        print(f"EPUB: {epub_path}")
        print(f"OPF:  {opf_path}")
        print()

        structural = 0
        label_count = 0
        samples: List[str] = []
        source = "none"

        if nav_path and nav_path in zf.namelist():
            structural, label_count, samples = _parse_nav_volume_stats(zf, nav_path)
            source = f"EPUB3 nav ({nav_path})"
        elif ncx_path and ncx_path in zf.namelist():
            structural, label_count, samples = _parse_ncx_volume_stats(zf, ncx_path)
            source = f"NCX ({ncx_path})"
        else:
            print("Could not find EPUB3 nav or NCX in manifest.")
            sys.exit(1)

        print(f"TOC source: {source}")
        print()
        print("Counts:")
        print(f"  Top-level TOC sections that contain nested entries (volume-like): {structural}")
        print(f"  Entries whose label looks like 'Volume N' / 'Book N' / 'Part N': {label_count}")
        if samples:
            print("  Sample matching labels:")
            for s in samples:
                print(f"    - {s}")
        print()
        if structural == 0 and label_count == 0:
            print(
                "Interpretation: This EPUB's table of contents does not declare separate "
                "volumes (flat chapter list). You cannot get '8 volumes' from the TOC alone."
            )
            print(
                "To split into 8 folders you need an external chapter-range map or chapter "
                "titles/file patterns that encode volume breaks."
            )
        elif structural > 0:
            print(
                f"Interpretation: The TOC has {structural} parent section(s) that wrap "
                "other entries (often volumes or parts). Verify in a reader that these "
                "match the printed volume boundaries you want."
            )


def main() -> None:
    parser = argparse.ArgumentParser(description="Count volume-like sections in an EPUB TOC.")
    parser.add_argument(
        "epub",
        nargs="?",
        default=str(
            Path(__file__).resolve().parent / "lom_book2_coi" / "epub" / "Lord_of_...tability.epub"
        ),
        help="Path to .epub file",
    )
    args = parser.parse_args()
    path = Path(args.epub)
    if not path.is_file():
        print(f"ERROR: File not found: {path}", file=sys.stderr)
        sys.exit(1)
    if path.suffix.lower() != ".epub":
        print("ERROR: Expected a .epub file.", file=sys.stderr)
        sys.exit(1)
    analyze_epub(path)


if __name__ == "__main__":
    main()
