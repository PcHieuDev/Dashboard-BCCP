"""
agent_memory.py - Hệ thống bộ nhớ chung cho đa Agent Antigravity
=================================================================
Đặt file này ở thư mục gốc của project.
Agent gọi file này qua terminal để đọc/ghi trạng thái làm việc.

Cách dùng:
  python agent_memory.py init
      Khởi tạo database (tự động chạy khi gọi bất kỳ lệnh nào)

  python agent_memory.py read [N]
      Đọc N bản ghi gần nhất từ agent_ledger (mặc định: 5)

  python agent_memory.py log <chat_id> <mô_tả> <files> [role] [action] [status] [notes]
      Ghi nhật ký phiên làm việc
      - chat_id: Conversation ID hiện tại
      - mô_tả: Tóm tắt ngắn gọn tác vụ (tiếng Việt)
      - files: Danh sách file bị tác động (phân tách bằng dấu phẩy)
      - role: general | contractor | builder | debugger (mặc định: general)
      - action: create | modify | delete | refactor | debug | review (mặc định: modify)
      - status: completed | in_progress | failed | blocked (mặc định: completed)
      - notes: Ghi chú bổ sung (tùy chọn)

  python agent_memory.py manifest-read
      Đọc toàn bộ bản đồ ý nghĩa file (file_manifest)

  python agent_memory.py manifest-set <path> <purpose> [module] [chat_id]
      Cập nhật ý nghĩa của một file trong manifest
      - path: Đường dẫn tương đối từ project root
      - purpose: Mô tả ý nghĩa/chức năng của file
      - module: Thuộc module/feature nào (tùy chọn)
      - chat_id: Conversation ID đang cập nhật (tùy chọn)

  python agent_memory.py summary
      Tóm tắt trạng thái dự án (số phiên, số file, phiên cuối)
"""

import sqlite3
import sys
import os
from datetime import datetime
from pathlib import Path

# Database nằm cùng thư mục với script này (project root)
DB_NAME = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".agent_memory.db")


def get_conn():
    """Tạo kết nối SQLite với WAL mode và busy timeout để tránh lock."""
    conn = sqlite3.connect(DB_NAME, timeout=10)
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute("PRAGMA busy_timeout=5000;")
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """Khởi tạo database với 2 bảng: file_manifest và agent_ledger."""
    conn = get_conn()
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS file_manifest (
            file_path       TEXT PRIMARY KEY,
            purpose         TEXT NOT NULL,
            module          TEXT,
            dependencies    TEXT,
            last_updated    DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_by      TEXT
        )
    """)
    c.execute("""
        CREATE TABLE IF NOT EXISTS agent_ledger (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp       DATETIME DEFAULT CURRENT_TIMESTAMP,
            agent_chat_id   TEXT NOT NULL,
            agent_role      TEXT DEFAULT 'general',
            task_description TEXT NOT NULL,
            affected_files  TEXT,
            action_type     TEXT DEFAULT 'modify',
            status          TEXT DEFAULT 'completed',
            notes           TEXT
        )
    """)
    conn.commit()
    conn.close()


def read_ledger(n=5):
    """Đọc N bản ghi gần nhất từ agent_ledger."""
    conn = get_conn()
    rows = conn.execute(
        "SELECT * FROM agent_ledger ORDER BY id DESC LIMIT ?", (n,)
    ).fetchall()
    conn.close()

    if not rows:
        print("[Memory] Chua co ban ghi nao trong agent_ledger.")
        return

    print(f"[Memory] {len(rows)} phien lam viec gan nhat:")
    print("-" * 72)
    for r in rows:
        short_id = r["agent_chat_id"][:12] + "..." if len(r["agent_chat_id"]) > 12 else r["agent_chat_id"]
        print(f"  #{r['id']} | {r['timestamp']} | Chat: {short_id}")
        print(f"    Role: {r['agent_role']} | Action: {r['action_type']} | Status: {r['status']}")
        print(f"    Task: {r['task_description']}")
        if r["affected_files"]:
            print(f"    Files: {r['affected_files']}")
        if r["notes"]:
            print(f"    Notes: {r['notes']}")
        print()


def log_session(chat_id, task, files, role="general", action="modify",
                status="completed", notes=None):
    """Ghi nhật ký phiên làm việc vào agent_ledger."""
    conn = get_conn()
    conn.execute(
        """INSERT INTO agent_ledger
           (timestamp, agent_chat_id, agent_role, task_description,
            affected_files, action_type, status, notes)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
        (
            datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            chat_id, role, task, files, action, status, notes,
        ),
    )
    conn.commit()
    conn.close()
    print(f"[Memory] Da ghi phien: [{role}/{action}] {task}")


def manifest_read():
    """Đọc toàn bộ file_manifest."""
    conn = get_conn()
    rows = conn.execute(
        "SELECT * FROM file_manifest ORDER BY last_updated DESC"
    ).fetchall()
    conn.close()

    if not rows:
        print("[Memory] file_manifest trong.")
        return

    print(f"[Memory] {len(rows)} file trong manifest:")
    print("-" * 72)
    for r in rows:
        module_tag = f" [{r['module']}]" if r["module"] else ""
        print(f"  {r['file_path']}{module_tag}")
        print(f"    -> {r['purpose']}")
        if r["dependencies"]:
            print(f"    Deps: {r['dependencies']}")
        print()


def manifest_set(path, purpose, module=None, chat_id=None):
    """Thêm hoặc cập nhật một file trong file_manifest."""
    conn = get_conn()
    conn.execute(
        """INSERT OR REPLACE INTO file_manifest
           (file_path, purpose, module, last_updated, updated_by)
           VALUES (?, ?, ?, ?, ?)""",
        (
            path, purpose, module,
            datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            chat_id,
        ),
    )
    conn.commit()
    conn.close()
    print(f"[Memory] Manifest cap nhat: {path}")


def summary():
    """Tóm tắt trạng thái dự án."""
    conn = get_conn()
    ledger_count = conn.execute("SELECT COUNT(*) FROM agent_ledger").fetchone()[0]
    manifest_count = conn.execute("SELECT COUNT(*) FROM file_manifest").fetchone()[0]
    last_entry = conn.execute(
        "SELECT * FROM agent_ledger ORDER BY id DESC LIMIT 1"
    ).fetchone()
    conn.close()

    print("=" * 56)
    print("[Memory] TOM TAT TRANG THAI DU AN")
    print("=" * 56)
    print(f"  Tong phien lam viec : {ledger_count}")
    print(f"  Tong file theo doi  : {manifest_count}")
    if last_entry:
        short_id = (
            last_entry["agent_chat_id"][:12] + "..."
            if len(last_entry["agent_chat_id"]) > 12
            else last_entry["agent_chat_id"]
        )
        print(f"  Phien cuoi          : {last_entry['timestamp']}")
        print(f"    Chat  : {short_id}")
        print(f"    Role  : {last_entry['agent_role']}")
        print(f"    Task  : {last_entry['task_description']}")
    else:
        print("  (Chua co phien nao)")
    print("=" * 56)


# ─── CLI Entry Point ────────────────────────────────────────────────
def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    cmd = sys.argv[1]

    # Luôn đảm bảo DB tồn tại trước khi chạy lệnh
    init_db()

    if cmd == "init":
        print(f"[Memory] DB san sang: {DB_NAME}")

    elif cmd == "read":
        n = int(sys.argv[2]) if len(sys.argv) > 2 else 5
        read_ledger(n)

    elif cmd == "log":
        if len(sys.argv) < 5:
            print("Cach dung: python agent_memory.py log <chat_id> <mo_ta> <files> "
                  "[role] [action] [status] [notes]")
            sys.exit(1)
        log_session(
            chat_id=sys.argv[2],
            task=sys.argv[3],
            files=sys.argv[4],
            role=sys.argv[5] if len(sys.argv) > 5 else "general",
            action=sys.argv[6] if len(sys.argv) > 6 else "modify",
            status=sys.argv[7] if len(sys.argv) > 7 else "completed",
            notes=sys.argv[8] if len(sys.argv) > 8 else None,
        )

    elif cmd == "manifest-read":
        manifest_read()

    elif cmd == "manifest-set":
        if len(sys.argv) < 4:
            print("Cach dung: python agent_memory.py manifest-set "
                  "<path> <purpose> [module] [chat_id]")
            sys.exit(1)
        manifest_set(
            path=sys.argv[2],
            purpose=sys.argv[3],
            module=sys.argv[4] if len(sys.argv) > 4 else None,
            chat_id=sys.argv[5] if len(sys.argv) > 5 else None,
        )

    elif cmd == "summary":
        summary()

    else:
        print(f"[Memory] Lenh khong hop le: {cmd}")
        print(__doc__)
        sys.exit(1)


if __name__ == "__main__":
    main()
