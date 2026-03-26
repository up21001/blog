"""코드베이스 디렉터리 파싱 — 소스 파일 트리 + 내용 추출 → 참고 텍스트."""

from __future__ import annotations

import logging
import os
from pathlib import Path

logger = logging.getLogger(__name__)

# 분석 대상 확장자
SOURCE_EXTENSIONS = {
    ".py", ".ts", ".tsx", ".js", ".jsx", ".go", ".rs",
    ".java", ".kt", ".cs", ".cpp", ".c", ".h", ".hpp",
    ".rb", ".php", ".swift", ".dart", ".scala", ".clj",
    ".ex", ".exs", ".elm", ".hs", ".lua", ".r", ".jl",
    ".vue", ".svelte",
    ".toml", ".yaml", ".yml", ".json", ".xml",
    ".sh", ".bash", ".zsh", ".fish",
    ".md", ".txt", ".rst",
    ".sql", ".graphql", ".proto",
    ".dockerfile", ".tf", ".hcl",
}

# 건너뛸 디렉터리
SKIP_DIRS = {
    ".git", ".hg", ".svn",
    "node_modules", "__pycache__", ".pytest_cache",
    "venv", ".venv", "env", ".env",
    "dist", "build", "out", "target", "bin", "obj",
    ".idea", ".vscode", ".vs",
    "vendor", "Pods",
    "coverage", ".nyc_output",
}

# 파일당 미리보기 줄 수
PREVIEW_LINES = 100


def parse_codebase(directory_path: str, max_total_bytes: int = 100_000) -> str:
    """Parse a codebase directory into a reference text for blog generation."""
    root = Path(directory_path).resolve()
    if not root.exists():
        raise ValueError(f"경로가 존재하지 않습니다: {directory_path}")
    if not root.is_dir():
        raise ValueError(f"디렉터리가 아닙니다: {directory_path}")

    # 소스 파일 수집
    source_files: list[Path] = []
    for dirpath, dirnames, filenames in os.walk(root):
        # 건너뛸 디렉터리 제거 (in-place)
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS and not d.startswith(".")]
        for fname in sorted(filenames):
            fpath = Path(dirpath) / fname
            ext = fpath.suffix.lower()
            # 확장자 없는 파일도 Dockerfile/Makefile 등 포함
            if ext in SOURCE_EXTENSIONS or fname in ("Dockerfile", "Makefile", "Makefile.am", "CMakeLists.txt"):
                source_files.append(fpath)

    source_files.sort()
    total_files = len(source_files)
    total_size = sum(f.stat().st_size for f in source_files if f.exists())

    # 파일 트리 생성
    tree_lines: list[str] = [f"# 코드베이스: {root.name}", "", "## 파일 트리", ""]
    last_dir: Path | None = None
    for fpath in source_files:
        rel = fpath.relative_to(root)
        parent = rel.parent
        if parent != last_dir:
            if str(parent) != ".":
                tree_lines.append(f"  {parent}/")
            last_dir = parent
        size_kb = fpath.stat().st_size / 1024
        tree_lines.append(f"    {rel.name}  ({size_kb:.1f} KB)")

    tree_lines += [
        "",
        f"총 {total_files}개 파일, {total_size / 1024:.1f} KB",
        "",
    ]
    tree_text = "\n".join(tree_lines)

    # 소스 내용 수집 (바이트 예산 내)
    content_parts: list[str] = []
    budget = max_total_bytes - len(tree_text.encode("utf-8"))
    used = 0

    for fpath in source_files:
        if used >= budget:
            content_parts.append(f"\n... (예산 초과로 이후 파일 생략) ...")
            break
        try:
            raw = fpath.read_bytes()
        except OSError:
            continue

        # 바이너리 파일 건너뜀
        try:
            text = raw.decode("utf-8")
        except UnicodeDecodeError:
            try:
                text = raw.decode("latin-1")
            except Exception:
                continue

        lines = text.splitlines()
        preview = "\n".join(lines[:PREVIEW_LINES])
        truncated = len(lines) > PREVIEW_LINES

        rel = fpath.relative_to(root)
        ext = fpath.suffix.lstrip(".") or "text"
        header = f"\n\n### {rel}"
        if truncated:
            header += f"  (첫 {PREVIEW_LINES}줄 / 총 {len(lines)}줄)"
        block = f"{header}\n```{ext}\n{preview}\n```"

        block_bytes = len(block.encode("utf-8"))
        if used + block_bytes > budget:
            # 남은 예산에 맞게 잘라내기
            remaining = budget - used
            block = block.encode("utf-8")[:remaining].decode("utf-8", errors="ignore")
            block += "\n... (잘림)"
            content_parts.append(block)
            used += remaining
            break

        content_parts.append(block)
        used += block_bytes

    return tree_text + "\n".join(content_parts)
