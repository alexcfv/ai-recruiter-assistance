import json
import uuid

from db.sqlite.connection import get_db

class ProfileRepository:
    def create_profile(self, profile_source: str, profile: dict) -> None:
        profile_uuid = str(uuid.uuid4())

        with get_db() as conn:
            conn.execute(
                "INSERT INTO profiles (uuid, profile_source, profile) VALUES (?, ?, ?)",
                (profile_uuid, profile_source, json.dumps(profile))
            )

    def profile_exists(self, source: str) -> bool:
        with get_db() as conn:
            row = conn.execute(
                "SELECT 1 FROM profiles WHERE profile_source = ? LIMIT 1",
                (source,)
            ).fetchone()
            return row is not None

    def get_all(self) -> list[dict]:
        with get_db() as conn:
            rows = conn.execute("SELECT * FROM profiles").fetchall()
            return [dict(row) for row in rows]

    def get_by_sources(self, sources: list[str]) -> dict[str, dict]:
        if not sources:
            return {}
        placeholders = ",".join("?" for _ in sources)
        with get_db() as conn:
            rows = conn.execute(
                f"SELECT * FROM profiles WHERE profile_source IN ({placeholders})",
                sources
            ).fetchall()
            return {row["profile_source"]: dict(row) for row in rows}
