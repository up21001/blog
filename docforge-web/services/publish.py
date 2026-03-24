"""Hugo content/posts 배포 경로."""

from __future__ import annotations

import base64 as _b64
import os
import re
import tempfile
from datetime import datetime
from pathlib import Path

_DATA_IMG_RE = re.compile(
    r'!\[(?P<alt>[^\]]*)\]\(data:(?P<mime>[^;]+);base64,(?P<b64>[A-Za-z0-9+/=\n]+)\)'
)

PACKAGE_ROOT = Path(__file__).resolve().parent.parent


def get_posts_dir() -> Path:
    raw = (os.environ.get("DOCFORGE_POSTS_DIR") or "").strip()
    if raw:
        p = Path(raw).expanduser().resolve()
        # Hugo 관례: .../content 만 넣은 경우 posts 하위로 통일
        if p.is_dir() and p.name.lower() == "content":
            return (p / "posts").resolve()
        return p
    return (PACKAGE_ROOT.parent / "content" / "posts").resolve()


def _probe_dir_writable(d: Path) -> bool:
    """실제 임시 파일 생성·삭제로 검사 (Windows에서 os.access W_OK 는 불신)."""
    try:
        d = d.resolve()
        if not d.is_dir():
            return False
        fd, name = tempfile.mkstemp(prefix=".docforge_w_", suffix=".tmp", dir=str(d))
        try:
            os.close(fd)
        except OSError:
            pass
        try:
            Path(name).unlink(missing_ok=True)
        except OSError:
            return False
        return True
    except OSError:
        return False


def posts_tree_writable(posts: Path) -> bool:
    """posts 가 있으면 그 안에, 없으면 부모(content 등)에 쓸 수 있는지."""
    try:
        posts = posts.resolve()
        if posts.is_dir():
            return _probe_dir_writable(posts)
        parent = posts.parent
        return parent.is_dir() and _probe_dir_writable(parent)
    except OSError:
        return False


def suggest_filename(markdown: str, slug_hint: str) -> str:
    """Front matter의 slug·date 우선, 없으면 slug_hint + 오늘 날짜."""
    slug = None
    m = re.search(r'^slug:\s*["\']?([^\s"\']+)["\']?\s*$', markdown, re.MULTILINE)
    if m:
        slug = m.group(1).strip()
    if not slug:
        slug = slug_hint or "post"
    slug = re.sub(r"[^\w\-가-힣]", "-", slug).strip("-")[:100] or "post"

    date_prefix = datetime.now().strftime("%Y-%m-%d")
    dm = re.search(r"^date:\s*(\d{4}-\d{2}-\d{2})", markdown, re.MULTILINE)
    if dm:
        date_prefix = dm.group(1)

    return f"{date_prefix}-{slug}.md"


_SUBDIR_RE = re.compile(r"^[a-zA-Z0-9][a-zA-Z0-9_-]{0,126}$")


def list_post_subdirs() -> list[str]:
    """posts 바로 아래의 하위 디렉터리 이름만 (정렬)."""
    posts = get_posts_dir()
    if not posts.is_dir():
        return []
    names: list[str] = []
    for p in posts.iterdir():
        if p.is_dir() and not p.name.startswith("."):
            names.append(p.name)
    return sorted(names, key=str.lower)


def sanitize_subdir(name: str | None) -> str:
    """단일 세그먼트만 허용. 빈 문자열 = posts 루트."""
    if name is None or not str(name).strip():
        return ""
    s = str(name).strip().replace("\\", "/")
    if "/" in s:
        raise ValueError("하위 폴더는 한 단계만 지정할 수 있습니다.")
    base = Path(s).name
    if not base or base in (".", "..") or base != s:
        raise ValueError("하위 폴더 이름이 올바르지 않습니다.")
    if not _SUBDIR_RE.match(base):
        raise ValueError(
            "하위 폴더 이름은 영문·숫자·하이픈·밑줄만 한 단계로 쓸 수 있습니다."
        )
    return base


def sanitize_filename(name: str) -> str:
    """경로 조각 제거, .md 보장."""
    name = (name or "").strip()
    if not name:
        raise ValueError("파일명이 비어 있습니다.")
    base = Path(name).name
    if not base or base in (".", "..") or ".." in name:
        raise ValueError("파일명이 올바르지 않습니다.")
    if "/" in base or "\\" in base:
        raise ValueError("파일명에 경로를 넣을 수 없습니다.")
    if not base.lower().endswith(".md"):
        base = f"{base}.md"
    if len(base) > 200:
        raise ValueError("파일명이 너무 깁니다.")
    return base


def publish_markdown(
    markdown: str,
    filename: str | None,
    slug_hint: str,
    subfolder: str = "",
) -> tuple[Path, str, str, str]:
    """posts(또는 posts/하위폴더)에 UTF-8 저장. 반환: (절대경로, 파일명, 상대표시, sub폴더명)."""
    posts = get_posts_dir()
    posts.mkdir(parents=True, exist_ok=True)

    raw_sub = (subfolder or "").strip()
    sub = sanitize_subdir(raw_sub) if raw_sub else ""
    dest_dir = (posts / sub) if sub else posts
    if sub:
        dest_dir.mkdir(parents=True, exist_ok=True)

    if filename and filename.strip():
        fname = sanitize_filename(filename)
    else:
        fname = suggest_filename(markdown, slug_hint)

    target = (dest_dir / fname).resolve()
    base_resolved = posts.resolve()
    try:
        target.relative_to(base_resolved)
    except ValueError as e:
        raise ValueError("저장 경로가 허용 범위를 벗어났습니다.") from e

    target.write_text(markdown, encoding="utf-8", newline="\n")
    rel_display = f"{sub}/{fname}" if sub else fname
    return target, fname, rel_display, sub


def has_data_images(markdown: str) -> bool:
    """마크다운에 data: URL 이미지가 있으면 True."""
    return bool(_DATA_IMG_RE.search(markdown))


def publish_bundle(
    markdown: str,
    filename: str | None,
    slug_hint: str,
    subfolder: str = "",
) -> tuple[Path, str, str, str]:
    """data: URL 이미지를 실제 파일로 분리해 Page Bundle 형태로 저장.
    반환: (index.md 절대경로, 'index.md', 상대표시, sub폴더명)
    """
    posts = get_posts_dir()
    posts.mkdir(parents=True, exist_ok=True)

    raw_sub = (subfolder or "").strip()
    sub = sanitize_subdir(raw_sub) if raw_sub else ""

    if filename and filename.strip():
        fname = sanitize_filename(filename)
    else:
        fname = suggest_filename(markdown, slug_hint)

    # 번들 폴더명 = 파일명에서 .md 제거
    bundle_name = fname[:-3] if fname.lower().endswith(".md") else fname

    dest_dir = (posts / sub / bundle_name) if sub else (posts / bundle_name)
    dest_dir.mkdir(parents=True, exist_ok=True)

    # data: URL → 상대 파일명으로 교체 + 이미지 파일 수집
    img_files: list[tuple[str, bytes]] = []
    idx = [0]

    def _repl(m: re.Match) -> str:
        mime = m.group("mime")
        b64data = m.group("b64").replace("\n", "")
        alt = m.group("alt")
        ext = "png" if "png" in mime else "jpg"
        img_fname = f"image-{idx[0] + 1}.{ext}"
        try:
            raw = _b64.standard_b64decode(b64data)
            img_files.append((img_fname, raw))
        except Exception:
            return m.group(0)
        idx[0] += 1
        return f"![{alt}]({img_fname})"

    clean_md = _DATA_IMG_RE.sub(_repl, markdown)

    # index.md 저장
    index_path = dest_dir / "index.md"
    index_path.write_text(clean_md, encoding="utf-8", newline="\n")

    # 이미지 파일 저장
    for img_name, img_data in img_files:
        (dest_dir / img_name).write_bytes(img_data)

    rel_display = f"{sub}/{bundle_name}/index.md" if sub else f"{bundle_name}/index.md"
    return index_path, "index.md", rel_display, sub


def get_static_images_dir() -> Path:
    """static/images/posts/ 경로."""
    return (PACKAGE_ROOT.parent / "static" / "images" / "posts").resolve()


def save_static_images(images: list[dict], slug: str) -> list[str]:
    """이미지를 static/images/posts/<slug>/ 에 저장. 반환: 저장된 파일명 목록."""
    img_dir = get_static_images_dir() / slug
    img_dir.mkdir(parents=True, exist_ok=True)

    saved = []
    for i, img in enumerate(images):
        mime = img.get("mime", "image/png")
        ext = "png" if "png" in mime else ("webp" if "webp" in mime else "jpg")
        fname = img.get("filename") or f"image-{i + 1}.{ext}"
        data = _b64.standard_b64decode(img["data_base64"])
        (img_dir / fname).write_bytes(data)
        saved.append(fname)
    return saved


def delete_static_image(slug: str, filename: str) -> bool:
    """static/images/posts/<slug>/<filename> 삭제."""
    base = get_static_images_dir()
    target = (base / slug / filename).resolve()
    if not str(target).startswith(str(base)):
        return False
    if target.is_file():
        target.unlink()
        # 폴더가 비었으면 삭제
        parent = target.parent
        if parent.is_dir() and not list(parent.iterdir()):
            parent.rmdir()
        return True
    return False


def list_posts(subfolder: str = "") -> list[dict]:
    """포스트 목록 반환. [{name, path, size, modified}]"""
    posts = get_posts_dir()
    target = (posts / subfolder) if subfolder else posts
    if not target.is_dir():
        return []
    result = []
    for f in sorted(target.iterdir(), key=lambda x: x.name, reverse=True):
        if f.is_file() and f.suffix.lower() == ".md":
            result.append({
                "name": f.name,
                "subfolder": subfolder,
                "path": f"{subfolder}/{f.name}" if subfolder else f.name,
                "size": f.stat().st_size,
                "modified": datetime.fromtimestamp(f.stat().st_mtime).isoformat(),
            })
    return result


def load_post(rel_path: str) -> dict:
    """포스트 마크다운 로드. {markdown, filename, subfolder, images}"""
    posts = get_posts_dir()
    target = (posts / rel_path).resolve()
    if not str(target).startswith(str(posts.resolve())):
        raise ValueError("허용 범위를 벗어난 경로입니다.")
    if not target.is_file():
        raise FileNotFoundError(f"파일을 찾을 수 없습니다: {rel_path}")

    markdown = target.read_text(encoding="utf-8")
    parts = rel_path.replace("\\", "/").split("/")
    subfolder = parts[0] if len(parts) > 1 else ""
    filename = parts[-1]

    # 연결된 이미지/SVG 찾기 (마크다운에서 /images/posts/<slug>/ 참조 탐색)
    slug = filename.replace(".md", "")
    img_dir = get_static_images_dir() / slug
    images = []
    svgs = []
    if img_dir.is_dir():
        img_exts = {".png", ".jpg", ".jpeg", ".webp", ".gif"}
        for f in sorted(img_dir.iterdir()):
            if f.suffix.lower() in img_exts:
                data = _b64.standard_b64encode(f.read_bytes()).decode("ascii")
                mime = "image/png" if f.suffix.lower() == ".png" else "image/jpeg"
                if f.suffix.lower() == ".webp":
                    mime = "image/webp"
                images.append({
                    "filename": f.name,
                    "mime": mime,
                    "data_base64": data,
                    "url": f"/images/posts/{slug}/{f.name}",
                })
            elif f.suffix.lower() == ".svg":
                svg_code = f.read_text(encoding="utf-8")
                svgs.append({
                    "filename": f.name,
                    "description": f.stem,
                    "type": "architecture",
                    "style": "modern",
                    "svg": svg_code,
                    "url": f"/images/posts/{slug}/{f.name}",
                })

    return {
        "markdown": markdown,
        "filename": filename,
        "subfolder": subfolder,
        "slug": slug,
        "images": images,
        "svgs": svgs,
    }


def content_target_info() -> dict:
    posts = get_posts_dir()
    exists = posts.is_dir()
    writable = posts_tree_writable(posts)
    subfolders = list_post_subdirs() if exists else []
    return {
        "posts_dir": str(posts),
        "exists": exists,
        "writable": writable,
        "subfolders": subfolders,
    }
