"""Хранилище Чатов, сообщений и вложений: SQLite + файлы на диске."""

from __future__ import annotations

import hashlib
import re
import sqlite3
from contextlib import contextmanager
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterator

SCHEMA = """
CREATE TABLE IF NOT EXISTS chats (
    id INTEGER PRIMARY KEY,
    title TEXT NOT NULL,
    owner TEXT NOT NULL,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS messages (
    id INTEGER PRIMARY KEY,
    chat_id INTEGER NOT NULL REFERENCES chats(id),
    author TEXT NOT NULL,
    role TEXT NOT NULL CHECK (role IN ('user', 'assistant')),
    action TEXT,
    content TEXT NOT NULL,
    created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS attachments (
    id INTEGER PRIMARY KEY,
    message_id INTEGER NOT NULL REFERENCES messages(id),
    name TEXT NOT NULL,
    path TEXT NOT NULL,
    size INTEGER NOT NULL,
    sha256 TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS messages_chat ON messages(chat_id, id);
CREATE INDEX IF NOT EXISTS attachments_message ON attachments(message_id);
"""


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def safe_file_name(name: str) -> str:
    """Имя файла без путей и управляющих символов; кириллица сохраняется."""

    base = Path(name).name.strip() or "file"
    base = re.sub(r"[\x00-\x1f/\\:*?\"<>|]", "_", base)
    return base[:180]


@dataclass(frozen=True)
class Attachment:
    id: int
    name: str
    path: Path
    size: int


@dataclass(frozen=True)
class Message:
    id: int
    chat_id: int
    author: str
    role: str
    action: str | None
    content: str
    created_at: str
    attachments: tuple[Attachment, ...] = field(default_factory=tuple)


@dataclass(frozen=True)
class Chat:
    id: int
    title: str
    owner: str
    created_at: str
    updated_at: str
    message_count: int = 0


class Store:
    def __init__(self, db_path: Path, files_dir: Path) -> None:
        self.db_path = db_path
        self.files_dir = files_dir
        db_path.parent.mkdir(parents=True, exist_ok=True)
        files_dir.mkdir(parents=True, exist_ok=True)
        with self._connect() as db:
            db.executescript(SCHEMA)

    @contextmanager
    def _connect(self) -> Iterator[sqlite3.Connection]:
        # Отдельное соединение на операцию: Streamlit обслуживает сессии в разных потоках.
        db = sqlite3.connect(self.db_path, timeout=30)
        db.row_factory = sqlite3.Row
        db.execute("PRAGMA journal_mode=WAL")
        db.execute("PRAGMA foreign_keys=ON")
        try:
            yield db
            db.commit()
        finally:
            db.close()

    def create_chat(self, title: str, owner: str) -> int:
        now = _now()
        with self._connect() as db:
            cursor = db.execute(
                "INSERT INTO chats (title, owner, created_at, updated_at) VALUES (?, ?, ?, ?)",
                (title.strip() or "Новый чат", owner, now, now),
            )
            return int(cursor.lastrowid)

    def get_chat(self, chat_id: int) -> Chat | None:
        with self._connect() as db:
            row = db.execute(
                "SELECT c.*, (SELECT COUNT(*) FROM messages m WHERE m.chat_id = c.id) AS message_count "
                "FROM chats c WHERE c.id = ?",
                (chat_id,),
            ).fetchone()
        return Chat(**dict(row)) if row else None

    def list_chats(self, *, owner: str | None = None, query: str = "") -> list[Chat]:
        sql = (
            "SELECT c.*, (SELECT COUNT(*) FROM messages m WHERE m.chat_id = c.id) AS message_count "
            "FROM chats c WHERE 1=1"
        )
        params: list[object] = []
        if owner is not None:
            sql += " AND c.owner = ?"
            params.append(owner)
        if query.strip():
            sql += (
                " AND (c.title LIKE ? OR EXISTS (SELECT 1 FROM messages m "
                "WHERE m.chat_id = c.id AND m.content LIKE ?))"
            )
            like = f"%{query.strip()}%"
            params += [like, like]
        sql += " ORDER BY c.updated_at DESC, c.id DESC"
        with self._connect() as db:
            return [Chat(**dict(row)) for row in db.execute(sql, params)]

    def add_message(
        self,
        chat_id: int,
        *,
        author: str,
        role: str,
        content: str,
        action: str | None = None,
        files: list[tuple[str, bytes]] | tuple = (),
    ) -> Message:
        now = _now()
        with self._connect() as db:
            cursor = db.execute(
                "INSERT INTO messages (chat_id, author, role, action, content, created_at) "
                "VALUES (?, ?, ?, ?, ?, ?)",
                (chat_id, author, role, action, content, now),
            )
            message_id = int(cursor.lastrowid)
            for name, data in files:
                file_name = safe_file_name(name)
                target = self.files_dir / str(chat_id) / str(message_id) / file_name
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(data)
                db.execute(
                    "INSERT INTO attachments (message_id, name, path, size, sha256) VALUES (?, ?, ?, ?, ?)",
                    (
                        message_id,
                        file_name,
                        str(target.relative_to(self.files_dir)),
                        len(data),
                        hashlib.sha256(data).hexdigest(),
                    ),
                )
            db.execute("UPDATE chats SET updated_at = ? WHERE id = ?", (now, chat_id))
        return next(m for m in self.messages(chat_id) if m.id == message_id)

    def messages(self, chat_id: int) -> list[Message]:
        with self._connect() as db:
            rows = db.execute(
                "SELECT * FROM messages WHERE chat_id = ? ORDER BY id", (chat_id,)
            ).fetchall()
            files = db.execute(
                "SELECT a.* FROM attachments a JOIN messages m ON m.id = a.message_id "
                "WHERE m.chat_id = ? ORDER BY a.id",
                (chat_id,),
            ).fetchall()
        by_message: dict[int, list[Attachment]] = {}
        for row in files:
            by_message.setdefault(row["message_id"], []).append(
                Attachment(
                    id=row["id"],
                    name=row["name"],
                    path=self.files_dir / row["path"],
                    size=row["size"],
                )
            )
        return [
            Message(
                id=row["id"],
                chat_id=row["chat_id"],
                author=row["author"],
                role=row["role"],
                action=row["action"],
                content=row["content"],
                created_at=row["created_at"],
                attachments=tuple(by_message.get(row["id"], ())),
            )
            for row in rows
        ]
