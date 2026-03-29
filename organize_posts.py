"""
포스트를 카테고리별 폴더로 정리
"""
import re
import shutil
from pathlib import Path

POSTS_DIR = Path("C:/My/Claude/Blog/blog/content/posts")

moved = 0
skipped = 0

for f in sorted(POSTS_DIR.glob("*.md")):
    text = f.read_text(encoding="utf-8", errors="ignore")
    parts = text.split("---", 2)
    if len(parts) < 3:
        skipped += 1
        continue

    frontmatter = parts[1]
    cat_m = re.search(r'categories:\s*\["([^"]+)"', frontmatter)
    if not cat_m:
        skipped += 1
        continue

    category = cat_m.group(1)
    target_dir = POSTS_DIR / category
    target_dir.mkdir(exist_ok=True)

    target = target_dir / f.name
    shutil.move(str(f), str(target))
    moved += 1

    if moved % 100 == 0:
        print(f"Progress: {moved} files moved...")

print(f"\nDone! Moved: {moved}, Skipped: {skipped}")
