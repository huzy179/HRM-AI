from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Set


@dataclass(frozen=True)
class CleanupReport:
    tenant_id: str
    orphan_files: int
    deleted_files: int
    orphan_dirs: int
    deleted_dirs: int
    notes: list[str]


def _within(root: Path, p: Path) -> bool:
    try:
        p.resolve().relative_to(root.resolve())
        return True
    except Exception:
        return False


def cleanup_storage(
    *,
    tenant_id: str,
    uploads_root: Path,
    chroma_root: Path,
    referenced_files: Set[str],
    referenced_campaign_ids: Set[int],
    dry_run: bool = True,
) -> CleanupReport:
    """
    Cleanup tenant-scoped storage:
    - remove files under uploads/tenant_<tenant_id> that are not referenced in DB
    - remove chroma tenant campaign dirs that have no campaign in DB
    """
    notes: list[str] = []

    tenant_uploads = uploads_root / f"tenant_{tenant_id}"
    tenant_chroma = chroma_root / f"tenant_{tenant_id}"

    orphan_files = 0
    deleted_files = 0
    orphan_dirs = 0
    deleted_dirs = 0

    # 1) Orphan uploads files
    if tenant_uploads.exists():
        for f in tenant_uploads.rglob("*"):
            if not f.is_file():
                continue
            if not _within(tenant_uploads, f):
                continue
            fp = str(f)
            if fp in referenced_files:
                continue
            orphan_files += 1
            if not dry_run:
                try:
                    f.unlink()
                    deleted_files += 1
                except Exception as exc:
                    notes.append(f"failed_delete_file:{fp}:{exc.__class__.__name__}")

    # 2) Orphan chroma campaign dirs
    if tenant_chroma.exists():
        for d in tenant_chroma.glob("campaign_*"):
            if not d.is_dir():
                continue
            if not _within(tenant_chroma, d):
                continue
            try:
                cid = int(d.name.split("_", 1)[1])
            except Exception:
                continue
            if cid in referenced_campaign_ids:
                continue
            orphan_dirs += 1
            if not dry_run:
                try:
                    # remove tree
                    for sub in sorted(d.rglob("*"), reverse=True):
                        try:
                            if sub.is_file():
                                sub.unlink()
                            else:
                                sub.rmdir()
                        except Exception:
                            pass
                    d.rmdir()
                    deleted_dirs += 1
                except Exception as exc:
                    notes.append(f"failed_delete_dir:{str(d)}:{exc.__class__.__name__}")

    return CleanupReport(
        tenant_id=tenant_id,
        orphan_files=orphan_files,
        deleted_files=deleted_files,
        orphan_dirs=orphan_dirs,
        deleted_dirs=deleted_dirs,
        notes=notes[:50],
    )

