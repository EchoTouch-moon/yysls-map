"""Import a normalized content dataset into the application database."""

from __future__ import annotations

import argparse
import hashlib
import sys
from collections.abc import Callable, Sequence
from pathlib import Path

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.db import SessionLocal
from app.models import ContentImportRun

from .apply import import_dataset
from .models import ContentDataset, ImportStats
from .validation import load_dataset

CONTENT_IMPORT_LOCK_KEY = 5_664_314_909_166_029_169


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(64 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def run_import(
    db: Session,
    *,
    dataset: ContentDataset,
    dataset_path: Path,
    replace_existing: bool,
) -> ImportStats:
    db.execute(select(func.pg_advisory_xact_lock(CONTENT_IMPORT_LOCK_KEY)))
    stats = import_dataset(
        db,
        dataset,
        replace_existing=replace_existing,
    )
    db.add(
        ContentImportRun(
            dataset_id=dataset.dataset.id,
            dataset_title=dataset.dataset.title,
            schema_version=dataset.schema_version,
            collected_at=dataset.dataset.collected_at,
            file_sha256=file_sha256(dataset_path),
            replaced_existing=replace_existing,
            stats=stats.model_dump(),
        )
    )
    db.flush()
    return stats


def main(
    argv: Sequence[str] | None = None,
    *,
    session_factory: Callable[[], Session] = SessionLocal,
) -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("dataset", type=Path)
    parser.add_argument(
        "--canonical",
        action="store_true",
        help="Import a canonical story dataset (frozen contract v0.1) instead of v5.",
    )
    parser.add_argument(
        "--validate-only",
        action="store_true",
        help="Validate the dataset without connecting to the database.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Run the database import and always roll it back.",
    )
    parser.add_argument(
        "--replace-existing",
        action="store_true",
        help="Delete existing graph content before importing this dataset.",
    )
    parser.add_argument(
        "--confirm-replace",
        metavar="DATASET_ID",
        help="Required confirmation value when using --replace-existing.",
    )
    args = parser.parse_args(argv)
    if args.canonical:
        from .apply import import_canonical_dataset
        from .validation import load_canonical_dataset as load_canon

        canonical = load_canon(args.dataset)
        if args.replace_existing and args.confirm_replace != canonical.dataset.id:
            parser.error(
                f"--replace-existing requires --confirm-replace {canonical.dataset.id}"
            )
        if args.validate_only:
            print(f"Canonical dataset valid: {canonical.dataset.id}")
            return
        with session_factory() as db:
            try:
                canon_stats = import_canonical_dataset(
                    db, canonical, replace_existing=args.replace_existing
                )
                if args.dry_run:
                    db.rollback()
                else:
                    db.commit()
            except Exception as exc:
                db.rollback()
                print(f"Canonical import failed: {exc}", file=sys.stderr)
                raise
        status = "rolled back" if args.dry_run else "committed"
        print(f"Canonical import {status}: {canon_stats.model_dump_json()}")
        return
    dataset = load_dataset(args.dataset)
    if args.replace_existing and args.confirm_replace != dataset.dataset.id:
        parser.error(f"--replace-existing requires --confirm-replace {dataset.dataset.id}")
    if args.confirm_replace and not args.replace_existing:
        parser.error("--confirm-replace requires --replace-existing")
    if args.validate_only:
        print(f"Content dataset valid: {dataset.dataset.id}")
        return

    with session_factory() as db:
        try:
            stats = run_import(
                db,
                dataset=dataset,
                dataset_path=args.dataset,
                replace_existing=args.replace_existing,
            )
            if args.dry_run:
                db.rollback()
            else:
                db.commit()
        except Exception as exc:
            db.rollback()
            print(f"Content import failed: {exc}", file=sys.stderr)
            raise
    status = "rolled back" if args.dry_run else "committed"
    print(f"Content import {status}: {stats.model_dump_json()}")


if __name__ == "__main__":
    main()
