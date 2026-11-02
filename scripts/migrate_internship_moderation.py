"""Add moderation columns without dropping existing data. Safe to rerun."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))
from sqlalchemy import inspect, text
from types import SimpleNamespace
from app.modules.internships.moderation import screen
from app.core.database import engine

def migrate():
    columns = {c["name"] for c in inspect(engine).get_columns("internships")}
    definitions = {
        "moderation_status": "VARCHAR(20) NOT NULL DEFAULT 'pending'",
        "auto_flags": "TEXT NULL", "rejection_reason": "TEXT NULL",
        "reviewed_by": "INTEGER NULL", "reviewed_at": "DATETIME NULL", "deleted_at": "DATETIME NULL",
    }
    with engine.begin() as connection:
        for name, definition in definitions.items():
            if name not in columns:
                connection.execute(text(f"ALTER TABLE internships ADD COLUMN {name} {definition}"))
                print("Added", name)
    with engine.begin() as connection:
        rows = connection.execute(text("SELECT id, title, description, requirements, location FROM internships WHERE moderation_status = 'pending' AND deleted_at IS NULL")).mappings().all()
        for row in rows:
            flags = screen(SimpleNamespace(**dict(row)))
            connection.execute(text("UPDATE internships SET auto_flags=:flags WHERE id=:id"), {"flags": flags, "id": row["id"]})
    print("Migration complete. Existing posts require staff/admin approval.")

if __name__ == "__main__": migrate()
