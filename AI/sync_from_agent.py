#!/usr/bin/env python3
"""INF-EXPORT / Wave 0 — sync FEMA_AI CSVs into AI/data/live/.

Sources:
  demo   — Terminal Common/Files/FEMA_AI (preferred) then Terminal MQL5/Files
  tester — Strategy Tester Agent FEMA_AI
  auto   — newest readable file (tester ranked higher historically; prefer explicit)

Usage:
  python AI/sync_from_agent.py --source demo
  python AI/sync_from_agent.py --source tester --magic 20260707
  python -m fema_ops ingest --source demo
"""

from __future__ import annotations

import argparse
import json
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path

_AI_DIR = Path(__file__).resolve().parent
_LIVE = _AI_DIR / "data" / "live"
_APPDATA = Path.home() / "AppData" / "Roaming" / "MetaQuotes"

HEARTBEAT_JSON = _LIVE / "sync_heartbeat.json"


def find_fema_ai_dirs(source: str = "auto") -> list[Path]:
    dirs: list[Path] = []
    if not _APPDATA.exists():
        return dirs
    tester = _APPDATA / "Tester"
    terminal = _APPDATA / "Terminal"
    common: list[Path] = []
    local: list[Path] = []
    agents: list[Path] = []

    if tester.exists() and source in ("auto", "tester"):
        for p in tester.glob("**/MQL5/Files/FEMA_AI"):
            if p.is_dir():
                agents.append(p)
    if terminal.exists() and source in ("auto", "demo"):
        for p in terminal.glob("**/Common/Files/FEMA_AI"):
            if p.is_dir():
                common.append(p)
        for p in terminal.glob("**/MQL5/Files/FEMA_AI"):
            if p.is_dir():
                local.append(p)

    if source == "demo":
        ordered = common + local
    elif source == "tester":
        ordered = agents
    else:
        ordered = agents + common + local

    seen: set[str] = set()
    out: list[Path] = []
    for d in ordered:
        key = str(d.resolve()).lower()
        if key not in seen:
            seen.add(key)
            out.append(d)
    return out


def _path_kind(path: Path) -> str:
    s = str(path).lower().replace("/", "\\")
    if "\\tester\\" in s:
        return "tester"
    if "\\common\\" in s:
        return "demo_common"
    return "demo_local"


def pick_newest_baskets(
    dirs: list[Path],
    magic: str | None,
    source: str,
    *,
    allow_empty: bool = False,
) -> list[Path]:
    """Newest-first; ranking depends on --source."""
    scored: list[tuple[int, float, int, Path]] = []
    for d in dirs:
        pattern = f"*_{magic}_baskets.csv" if magic else "*_baskets.csv"
        for p in d.glob(pattern):
            try:
                st = p.stat()
            except OSError:
                continue
            if st.st_size <= 0 and not allow_empty:
                continue
            kind = _path_kind(p)
            if source == "demo":
                rank = 2 if kind == "demo_common" else (1 if kind == "demo_local" else 0)
            elif source == "tester":
                rank = 2 if kind == "tester" else 0
            else:
                rank = 2 if kind == "tester" else (1 if kind == "demo_common" else 0)
            scored.append((rank, st.st_mtime, st.st_size, p))
    scored.sort(key=lambda t: (t[0], t[1], t[2]), reverse=True)
    return [p for _, _, _, p in scored]


def copy_file(src: Path, dst: Path) -> None:
    """Copy even when MT5 holds a share/exclusive lock (best-effort)."""
    try:
        shutil.copy2(src, dst)
        return
    except OSError:
        pass

    data = _win32_shared_read(src)
    if data is not None:
        dst.write_bytes(data)
        return

    try:
        data = src.read_bytes()
        dst.write_bytes(data)
        return
    except OSError:
        pass

    # PowerShell Copy-Item sometimes succeeds when Python open fails
    if sys.platform == "win32":
        import subprocess

        r = subprocess.run(
            [
                "powershell",
                "-NoProfile",
                "-Command",
                f"Copy-Item -LiteralPath '{src}' -Destination '{dst}' -Force",
            ],
            capture_output=True,
            text=True,
        )
        if r.returncode == 0 and dst.is_file() and dst.stat().st_size >= 0:
            return

    raise PermissionError(
        f"locked (try --source tester after run, or stop EA briefly): {src}"
    )


def _win32_shared_read(src: Path) -> bytes | None:
    if sys.platform != "win32":
        return None
    try:
        import ctypes
        from ctypes import wintypes
    except ImportError:
        return None

    GENERIC_READ = 0x80000000
    FILE_SHARE_ALL = 0x1 | 0x2 | 0x4
    OPEN_EXISTING = 3
    FILE_ATTRIBUTE_NORMAL = 0x80
    INVALID_HANDLE = wintypes.HANDLE(-1).value

    CreateFileW = ctypes.windll.kernel32.CreateFileW
    CreateFileW.argtypes = [
        wintypes.LPCWSTR,
        wintypes.DWORD,
        wintypes.DWORD,
        wintypes.LPVOID,
        wintypes.DWORD,
        wintypes.DWORD,
        wintypes.HANDLE,
    ]
    CreateFileW.restype = wintypes.HANDLE
    ReadFile = ctypes.windll.kernel32.ReadFile
    CloseHandle = ctypes.windll.kernel32.CloseHandle
    GetFileSizeEx = ctypes.windll.kernel32.GetFileSizeEx

    handle = CreateFileW(
        str(src),
        GENERIC_READ,
        FILE_SHARE_ALL,
        None,
        OPEN_EXISTING,
        FILE_ATTRIBUTE_NORMAL,
        None,
    )
    if handle == INVALID_HANDLE or handle is None:
        return None
    try:
        size = wintypes.LARGE_INTEGER()
        if not GetFileSizeEx(handle, ctypes.byref(size)):
            return None
        n = int(size.QuadPart)
        if n < 0 or n > 512 * 1024 * 1024:
            return None
        buf = ctypes.create_string_buffer(n)
        read = wintypes.DWORD(0)
        if not ReadFile(handle, buf, n, ctypes.byref(read), None):
            return None
        return buf.raw[: read.value]
    finally:
        CloseHandle(handle)


def sibling(path: Path, suffix: str) -> Path | None:
    name = path.name
    if not name.endswith("_baskets.csv"):
        return None
    stem = name[: -len("_baskets.csv")]
    cand = path.with_name(stem + suffix)
    return cand if cand.exists() else None


def _classify_source(baskets: Path, requested: str) -> str:
    kind = _path_kind(baskets)
    if requested == "demo":
        return "demo"
    if requested == "tester":
        return "tester"
    if kind == "tester":
        return "tester"
    return "demo"


def sync(
    *,
    source: str = "auto",
    magic: str | None = None,
    from_dir: Path | None = None,
    out_dir: Path | None = None,
    allow_empty: bool = False,
) -> dict:
    """Programmatic sync; returns heartbeat dict. Raises SystemExit codes via return."""
    out = out_dir or _LIVE
    out.mkdir(parents=True, exist_ok=True)

    if from_dir is not None:
        if not from_dir.is_dir():
            raise FileNotFoundError(f"not a directory: {from_dir}")
        dirs = [from_dir]
    else:
        dirs = find_fema_ai_dirs(source)
        if not dirs:
            raise FileNotFoundError(
                f"no FEMA_AI folders for source={source} under AppData MetaQuotes"
            )

    # Demo often header-only while basket open — allow empty/small for demo
    allow = allow_empty or source == "demo"
    candidates = pick_newest_baskets(dirs, magic, source, allow_empty=allow)
    if not candidates and source == "demo":
        candidates = pick_newest_baskets(dirs, magic, source, allow_empty=True)
    if not candidates:
        # Still try to find any baskets.csv including 0-byte for heartbeat
        for d in dirs:
            for p in d.glob("*_baskets.csv" if not magic else f"*_{magic}_baskets.csv"):
                candidates.append(p)
        if not candidates:
            raise FileNotFoundError("no *_baskets.csv found")

    baskets = None
    baskets_locked = False
    last_err: Exception | None = None
    for cand in candidates:
        try:
            tmp = out / "_probe_baskets.csv"
            copy_file(cand, tmp)
            tmp.unlink(missing_ok=True)
            baskets = cand
            break
        except OSError as e:
            last_err = e
            continue
    if baskets is None:
        # Partial Wave 0: meta/config often readable while baskets exclusive-locked
        baskets = candidates[0]
        baskets_locked = True

    events = sibling(baskets, "_events.csv")
    meta = sibling(baskets, "_run.meta.txt")
    config = sibling(baskets, "_run_config.json")

    dst_b = out / "latest_baskets.csv"
    dst_e = out / "latest_events.csv"
    dst_m = out / "latest_run.meta.txt"
    dst_c = out / "latest_run_config.json"
    src_note = out / "latest_source.txt"

    baskets_copied = False
    if not baskets_locked:
        copy_file(baskets, dst_b)
        baskets_copied = True
    else:
        # Leave prior latest_baskets if present; still record lock in heartbeat
        pass

    if events is not None:
        try:
            copy_file(events, dst_e)
        except PermissionError:
            events = None
    if meta is not None:
        try:
            copy_file(meta, dst_m)
        except PermissionError:
            meta = None
    if config is not None:
        try:
            copy_file(config, dst_c)
        except PermissionError:
            config = None

    stamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    archive = out / "archive"
    archive.mkdir(exist_ok=True)
    if baskets_copied:
        try:
            copy_file(baskets, archive / f"{stamp}_{baskets.name}")
        except PermissionError:
            pass

    try:
        st = baskets.stat()
        mtime_iso = datetime.fromtimestamp(st.st_mtime, tz=timezone.utc).isoformat()
        nbytes = st.st_size
    except OSError:
        mtime_iso = ""
        nbytes = dst_b.stat().st_size if dst_b.is_file() else 0

    src_label = _classify_source(baskets, source)
    now = datetime.now(timezone.utc)
    n_rows = 0
    read_path = dst_b if dst_b.is_file() else None
    if baskets_copied and read_path:
        try:
            for line in read_path.read_text(encoding="utf-8", errors="replace").splitlines():
                s = line.strip()
                if not s or s.startswith("#") or s.lower().startswith("basket"):
                    continue
                n_rows += 1
        except OSError:
            pass

    age_hours = None
    if mtime_iso:
        try:
            mt = datetime.fromisoformat(mtime_iso)
            age_hours = round((now - mt).total_seconds() / 3600.0, 2)
        except ValueError:
            pass

    # Header-only heuristic from size when locked (~503 B = header)
    header_only = (n_rows == 0 and nbytes > 0) or (
        baskets_locked and nbytes > 0 and nbytes < 2000
    )

    heartbeat = {
        "synced_utc": now.isoformat(),
        "source": src_label,
        "source_requested": source,
        "baskets_src": str(baskets),
        "events_src": str(events) if events else "",
        "meta_src": str(meta) if meta else "",
        "baskets_mtime": mtime_iso,
        "baskets_bytes": nbytes,
        "baskets_rows": n_rows if baskets_copied else None,
        "age_hours": age_hours,
        "stale": bool(age_hours is not None and age_hours > 24),
        "header_only": header_only,
        "baskets_locked": baskets_locked,
        "baskets_copied": baskets_copied,
        "latest_baskets": str(dst_b),
        "wave": "IS-W0",
        "partial": baskets_locked,
        "note": (
            "baskets exclusive-locked by MT5; synced meta/config; "
            "re-ingest after basket close or brief EA unload"
            if baskets_locked
            else ""
        ),
    }

    src_note.write_text(
        "\n".join(
            [
                f"synced_utc={heartbeat['synced_utc']}",
                f"source={src_label}",
                f"source_requested={source}",
                f"baskets_src={baskets}",
                f"events_src={events or ''}",
                f"meta_src={meta or ''}",
                f"baskets_mtime={mtime_iso}",
                f"baskets_bytes={nbytes}",
                f"baskets_rows={heartbeat['baskets_rows']}",
                f"age_hours={age_hours}",
                f"stale={int(bool(heartbeat['stale']))}",
                f"header_only={int(header_only)}",
                f"baskets_locked={int(baskets_locked)}",
                f"baskets_copied={int(baskets_copied)}",
                f"latest_baskets={dst_b}",
                f"latest_events={dst_e if events else '(missing)'}",
                f"note={heartbeat['note']}",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    HEARTBEAT_JSON.write_text(json.dumps(heartbeat, indent=2) + "\n", encoding="utf-8")
    heartbeat["_last_err"] = str(last_err) if last_err else ""
    return heartbeat


def main() -> int:
    ap = argparse.ArgumentParser(description="Sync FEMA_AI CSVs to AI/data/live/")
    ap.add_argument("--from-dir", type=Path, default=None, help="Explicit FEMA_AI folder")
    ap.add_argument("--magic", type=str, default="", help="Filter by magic (e.g. 20260707)")
    ap.add_argument(
        "--source",
        choices=["auto", "demo", "tester"],
        default="auto",
        help="demo=Common/Terminal; tester=Agent; auto=newest readable",
    )
    ap.add_argument("--out-dir", type=Path, default=_LIVE)
    ap.add_argument(
        "--allow-empty",
        action="store_true",
        help="Allow 0-byte / header-only baskets (demo open book)",
    )
    args = ap.parse_args()

    magic = args.magic.strip() or None
    try:
        hb = sync(
            source=args.source,
            magic=magic,
            from_dir=args.from_dir,
            out_dir=args.out_dir,
            allow_empty=args.allow_empty,
        )
    except FileNotFoundError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return 2
    except PermissionError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return 3

    flag = "PARTIAL" if hb.get("partial") else "OK"
    print(
        f"synced [{flag}] source={hb['source']} baskets_locked={int(bool(hb.get('baskets_locked')))} "
        f"<- {hb['baskets_src']}"
    )
    print(
        f"  bytes={hb['baskets_bytes']} rows={hb['baskets_rows']} age_h={hb['age_hours']} "
        f"stale={int(hb['stale'])} header_only={int(hb['header_only'])}"
    )
    if hb.get("note"):
        print(f"  note: {hb['note']}")
    print(f"wrote {HEARTBEAT_JSON}")
    return 4 if hb.get("partial") else 0


if __name__ == "__main__":
    raise SystemExit(main())
