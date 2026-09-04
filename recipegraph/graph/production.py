"""First-stage production graph indexes.

The resolver in this module is intentionally direct and deterministic. It provides the
core reverse lookups needed by the future recursive tree resolver without selecting one
recipe path when multiple valid paths exist.
"""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class RecipeRef:
    recipe_id: str
    recipe_type: str
    status: str
    confidence: float


class ProductionGraph:
    def __init__(self, connection: sqlite3.Connection):
        self.connection = connection

    def recipes_producing(self, item_id: str) -> list[RecipeRef]:
        rows = self.connection.execute(
            """SELECT r.recipe_id, r.recipe_type, r.status, r.confidence
            FROM recipes r JOIN recipe_outputs o ON o.recipe_id = r.recipe_id
            WHERE o.item_id = ? ORDER BY r.recipe_id""",
            (item_id,),
        ).fetchall()
        return [RecipeRef(row[0], row[1], row[2], float(row[3])) for row in rows]

    def recipes_consuming(self, item_id: str) -> list[RecipeRef]:
        rows = self.connection.execute(
            """SELECT DISTINCT r.recipe_id, r.recipe_type, r.status, r.confidence
            FROM recipes r JOIN recipe_inputs i ON i.recipe_id = r.recipe_id
            WHERE i.item_id = ? ORDER BY r.recipe_id""",
            (item_id,),
        ).fetchall()
        return [RecipeRef(row[0], row[1], row[2], float(row[3])) for row in rows]

    def recipe_count(self) -> int:
        row = self.connection.execute("SELECT COUNT(*) FROM recipes").fetchone()
        return int(row[0])

    def item_count(self) -> int:
        row = self.connection.execute("SELECT COUNT(*) FROM items").fetchone()
        return int(row[0])
