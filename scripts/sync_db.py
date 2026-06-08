#!/usr/bin/env python3
"""
本地 ↔ 线上（Supabase）数据库同步工具。

用法:
  py scripts/sync_db.py status              # 对比本地 / 远程行数
  py scripts/sync_db.py schema push         # 本地迁移 → 远程（Alembic）
  py scripts/sync_db.py data push --yes     # 本地数据 → 远程（覆盖远程）
  py scripts/sync_db.py data pull --yes     # 远程数据 → 本地（覆盖本地）

安全:
  - .env 中 DB_SYNC_ENABLED=true 才允许执行
  - 数据同步必须加 --yes 确认
"""

from __future__ import annotations

import argparse
import io
import os
import subprocess
import sys
from pathlib import Path

import psycopg2

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from scripts.sync_config import (  # noqa: E402
    PROJECT_ROOT as ROOT,
    SYNC_TABLES,
    SyncSettings,
    ensure_sync_enabled,
    get_local_url,
    get_remote_url,
    to_async_url,
)


def connect(url: str):
    return psycopg2.connect(url)


def table_counts(conn) -> dict[str, int]:
    counts: dict[str, int] = {}
    with conn.cursor() as cur:
        for table in SYNC_TABLES:
            cur.execute(f"SELECT COUNT(*) FROM {table}")
            counts[table] = cur.fetchone()[0]
    return counts


def cmd_status(_: argparse.Namespace) -> int:
    settings = SyncSettings()
    local_url = get_local_url(settings)
    try:
        remote_url = get_remote_url(settings)
    except ValueError as e:
        print(f"错误: {e}")
        return 1

    print(f"同步开关: {'开启' if settings.DB_SYNC_ENABLED else '关闭'}")
    print(f"本地: {mask_url(local_url)}")
    print(f"远程: {mask_url(remote_url)}")
    print()
    print(f"{'表名':<16} {'本地':>8} {'远程':>8}")
    print("-" * 36)

    with connect(local_url) as local, connect(remote_url) as remote:
        local_counts = table_counts(local)
        remote_counts = table_counts(remote)
        for table in SYNC_TABLES:
            print(f"{table:<16} {local_counts[table]:>8} {remote_counts[table]:>8}")
    return 0


def cmd_schema_push(_: argparse.Namespace) -> int:
    ensure_sync_enabled()
    settings = SyncSettings()
    remote_async = to_async_url(get_remote_url(settings))

    print("正在将 Alembic 迁移应用到远程数据库...")
    print(f"目标: {mask_url(remote_async)}")
    print()

    env = {**dict(os.environ), "DATABASE_URL": remote_async}
    result = subprocess.run(
        [sys.executable, "-m", "alembic", "upgrade", "head"],
        cwd=ROOT,
        env=env,
    )
    if result.returncode == 0:
        print("表结构同步完成（schema push）。")
    else:
        print("表结构同步失败，请检查 Alembic 日志。")
    return result.returncode


def sync_data(source_url: str, target_url: str, direction: str) -> int:
    ensure_sync_enabled()
    print(f"数据同步方向: {direction}")
    print(f"源: {mask_url(source_url)}")
    print(f"目标: {mask_url(target_url)}")
    print(f"表: {', '.join(SYNC_TABLES)}")
    print("警告: 目标库中以上表的数据将被清空并覆盖！")
    print()

    with connect(source_url) as src, connect(target_url) as dst:
        src.autocommit = False
        dst.autocommit = False

        with dst.cursor() as cur:
            tables_sql = ", ".join(SYNC_TABLES)
            cur.execute(f"TRUNCATE {tables_sql} RESTART IDENTITY CASCADE")

        for table in SYNC_TABLES:
            buf = io.BytesIO()
            with src.cursor() as sc:
                sc.copy_expert(f'COPY "{table}" TO STDOUT WITH (FORMAT binary)', buf)
            buf.seek(0)
            with dst.cursor() as dc:
                dc.copy_expert(f'COPY "{table}" FROM STDIN WITH (FORMAT binary)', buf)
            print(f"  ✓ {table}")

        dst.commit()

    print()
    print("数据同步完成。")
    return 0


def cmd_data_push(args: argparse.Namespace) -> int:
    if not args.yes:
        print("数据 push 会覆盖远程所有业务表数据。请加 --yes 确认。")
        return 1
    settings = SyncSettings()
    return sync_data(
        get_local_url(settings),
        get_remote_url(settings),
        "本地 → 远程 (push)",
    )


def cmd_data_pull(args: argparse.Namespace) -> int:
    if not args.yes:
        print("数据 pull 会覆盖本地所有业务表数据。请加 --yes 确认。")
        return 1
    settings = SyncSettings()
    return sync_data(
        get_remote_url(settings),
        get_local_url(settings),
        "远程 → 本地 (pull)",
    )


def mask_url(url: str) -> str:
    """隐藏密码便于打印。"""
    if "@" not in url:
        return url
    prefix, host = url.split("@", 1)
    if "://" in prefix:
        scheme, rest = prefix.split("://", 1)
        if ":" in rest:
            user = rest.split(":", 1)[0]
            return f"{scheme}://{user}:****@{host}"
    return url


def main() -> int:
    parser = argparse.ArgumentParser(description="本地 ↔ 远程 PostgreSQL 同步")
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("status", help="对比本地 / 远程各表行数")

    sub.add_parser("schema", help="同步表结构").add_argument(
        "action", choices=["push"], help="push = 本地 Alembic 迁移应用到远程"
    )

    data_push = sub.add_parser("data", help="同步数据")
    data_push.add_argument("action", choices=["push", "pull"])
    data_push.add_argument("--yes", action="store_true", help="确认覆盖目标库数据")

    args = parser.parse_args()

    if args.command == "status":
        return cmd_status(args)
    if args.command == "schema":
        if args.action == "push":
            return cmd_schema_push(args)
    if args.command == "data":
        if args.action == "push":
            return cmd_data_push(args)
        if args.action == "pull":
            return cmd_data_pull(args)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
