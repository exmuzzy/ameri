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
    created_at TEXT NOT NULL,
    prompt_tokens INTEGER,
    completion_tokens INTEGER,
    cache_hit_tokens INTEGER,
    harness_version TEXT
);
CREATE TABLE IF NOT EXISTS attachments (
    id INTEGER PRIMARY KEY,
    message_id INTEGER NOT NULL REFERENCES messages(id),
    name TEXT NOT NULL,
    path TEXT NOT NULL,
    size INTEGER NOT NULL,
    sha256 TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS feedback (
    id INTEGER PRIMARY KEY,
    message_id INTEGER NOT NULL REFERENCES messages(id),
    reviewer TEXT NOT NULL,
    rating INTEGER NOT NULL CHECK (rating IN (-1, 1)),
    comment TEXT NOT NULL DEFAULT '',
    corrected_text TEXT NOT NULL DEFAULT '',
    rule_text TEXT NOT NULL DEFAULT '',
    as_example INTEGER NOT NULL DEFAULT 0,
    status TEXT NOT NULL DEFAULT 'reviewed'
        CHECK (status IN ('reviewed', 'proposed', 'applied', 'rejected')),
    commit_sha TEXT,
    created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS onboarding (
    login TEXT NOT NULL,
    step TEXT NOT NULL,
    done_at TEXT NOT NULL,
    PRIMARY KEY (login, step)
);
CREATE INDEX IF NOT EXISTS messages_chat ON messages(chat_id, id);
CREATE INDEX IF NOT EXISTS feedback_message ON feedback(message_id);
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
    prompt_tokens: int | None = None
    completion_tokens: int | None = None
    cache_hit_tokens: int | None = None
    harness_version: str | None = None


@dataclass(frozen=True)
class Feedback:
    id: int
    message_id: int
    reviewer: str
    rating: int
    comment: str
    corrected_text: str
    rule_text: str
    as_example: bool
    status: str
    commit_sha: str | None
    created_at: str
    chat_id: int = 0
    question: str = ""
    answer: str = ""
    chat_owner: str = ""


@dataclass(frozen=True)
class Usage:
    prompt_tokens: int = 0
    completion_tokens: int = 0
    cache_hit_tokens: int = 0


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
        usage: Usage | None = None,
        harness_version: str | None = None,
    ) -> Message:
        now = _now()
        usage = usage or Usage()
        with self._connect() as db:
            cursor = db.execute(
                "INSERT INTO messages (chat_id, author, role, action, content, created_at, "
                "prompt_tokens, completion_tokens, cache_hit_tokens, harness_version) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    chat_id, author, role, action, content, now,
                    usage.prompt_tokens or None, usage.completion_tokens or None,
                    usage.cache_hit_tokens or None, harness_version,
                ),
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
                prompt_tokens=row["prompt_tokens"],
                completion_tokens=row["completion_tokens"],
                cache_hit_tokens=row["cache_hit_tokens"],
                harness_version=row["harness_version"],
            )
            for row in rows
        ]

    # --- Оценки и Исправления Руководителя ---

    def add_feedback(
        self,
        message_id: int,
        *,
        reviewer: str,
        rating: int,
        comment: str = "",
        corrected_text: str = "",
        rule_text: str = "",
        as_example: bool = False,
    ) -> int:
        status = "proposed" if (rule_text.strip() or as_example) else "reviewed"
        with self._connect() as db:
            cursor = db.execute(
                "INSERT INTO feedback (message_id, reviewer, rating, comment, corrected_text, "
                "rule_text, as_example, status, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    message_id, reviewer, rating, comment.strip(), corrected_text.strip(),
                    rule_text.strip(), int(as_example), status, _now(),
                ),
            )
            return int(cursor.lastrowid)

    def _feedback_query(self, where: str, params: list[object]) -> list[Feedback]:
        sql = (
            "SELECT f.*, m.chat_id AS chat_id, m.content AS answer, c.owner AS chat_owner, "
            "(SELECT q.content FROM messages q WHERE q.chat_id = m.chat_id AND q.role = 'user' "
            " AND q.id < m.id ORDER BY q.id DESC LIMIT 1) AS question "
            "FROM feedback f JOIN messages m ON m.id = f.message_id JOIN chats c ON c.id = m.chat_id "
            f"WHERE {where} ORDER BY f.id DESC"
        )
        with self._connect() as db:
            rows = db.execute(sql, params).fetchall()
        return [
            Feedback(
                **{k: row[k] for k in row.keys() if k not in {"as_example", "question"}},
                as_example=bool(row["as_example"]),
                question=row["question"] or "",
            )
            for row in rows
        ]

    def feedback_for_chat(self, chat_id: int) -> dict[int, list[Feedback]]:
        result: dict[int, list[Feedback]] = {}
        for item in self._feedback_query("m.chat_id = ?", [chat_id]):
            result.setdefault(item.message_id, []).append(item)
        return result

    def list_feedback(self, status: str | None = None) -> list[Feedback]:
        if status is None:
            return self._feedback_query("1=1", [])
        return self._feedback_query("f.status = ?", [status])

    def set_feedback_status(self, feedback_id: int, status: str, commit_sha: str | None = None) -> None:
        with self._connect() as db:
            db.execute(
                "UPDATE feedback SET status = ?, commit_sha = COALESCE(?, commit_sha) WHERE id = ?",
                (status, commit_sha, feedback_id),
            )

    # --- Статистика для Руководителя ---

    def stats_by_owner(self) -> list[dict[str, object]]:
        """По каждому автору Чатов: сообщения, ответы Ассистента, оценки, Исправления, токены."""

        sql = """
        SELECT c.owner AS owner,
               COUNT(DISTINCT c.id) AS chats,
               SUM(m.role = 'user') AS user_messages,
               SUM(m.role = 'assistant' AND m.author = 'assistant') AS answers,
               COALESCE(SUM(m.prompt_tokens), 0) AS prompt_tokens,
               COALESCE(SUM(m.completion_tokens), 0) AS completion_tokens,
               COALESCE(SUM(m.cache_hit_tokens), 0) AS cache_hit_tokens,
               MAX(m.created_at) AS last_activity
        FROM chats c LEFT JOIN messages m ON m.chat_id = c.id
        GROUP BY c.owner ORDER BY last_activity DESC
        """
        feedback_sql = """
        SELECT c.owner AS owner, SUM(f.rating = 1) AS likes, SUM(f.rating = -1) AS dislikes,
               SUM(f.corrected_text != '') AS corrections
        FROM feedback f JOIN messages m ON m.id = f.message_id JOIN chats c ON c.id = m.chat_id
        GROUP BY c.owner
        """
        with self._connect() as db:
            rows = [dict(r) for r in db.execute(sql)]
            fb = {r["owner"]: dict(r) for r in db.execute(feedback_sql)}
        for row in rows:
            extra = fb.get(row["owner"], {})
            row["likes"] = extra.get("likes") or 0
            row["dislikes"] = extra.get("dislikes") or 0
            row["corrections"] = extra.get("corrections") or 0
        return rows

    # --- Онбординг ---

    def onboarding_done(self, login: str) -> set[str]:
        with self._connect() as db:
            return {r["step"] for r in db.execute("SELECT step FROM onboarding WHERE login = ?", (login,))}

    def set_onboarding(self, login: str, step: str, done: bool) -> None:
        with self._connect() as db:
            if done:
                db.execute(
                    "INSERT OR IGNORE INTO onboarding (login, step, done_at) VALUES (?, ?, ?)",
                    (login, step, _now()),
                )
            else:
                db.execute("DELETE FROM onboarding WHERE login = ? AND step = ?", (login, step))
