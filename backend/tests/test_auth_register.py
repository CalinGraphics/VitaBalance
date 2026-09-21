"""Înregistrare: cont nou, email deja folosit și adoptarea conturilor vechi fără `password_hash`."""
import unittest
from unittest.mock import patch

from services import auth as auth_module


class FakeQuery:
    """Imită lanțul postgrest folosit de `create_user` (select/insert/update + eq/is_)."""

    def __init__(self, table: "FakeTable", op: str, payload=None):
        self._table = table
        self._op = op
        self._payload = payload
        self._eq = {}
        self._is_null = set()

    def select(self, _columns):
        return self

    def eq(self, column, value):
        self._eq[column] = value
        return self

    def is_(self, column, value):
        assert value == "null"
        self._is_null.add(column)
        return self

    def _matches(self, row):
        for column, value in self._eq.items():
            if row.get(column) != value:
                return False
        return all(row.get(column) is None for column in self._is_null)

    def execute(self):
        if self._op == "select":
            return type("Resp", (), {"data": [dict(r) for r in self._table.rows if self._matches(r)]})()
        if self._op == "insert":
            row = dict(self._payload)
            row.setdefault("id", self._table.next_id())
            self._table.rows.append(row)
            return type("Resp", (), {"data": [dict(row)]})()
        # update
        updated = []
        for row in self._table.rows:
            if self._matches(row):
                row.update(self._payload)
                updated.append(dict(row))
        return type("Resp", (), {"data": updated})()


class FakeTable:
    def __init__(self, rows):
        self.rows = rows
        self._seq = max([r.get("id", 0) for r in rows] or [0])

    def next_id(self):
        self._seq += 1
        return self._seq

    def select(self, columns):
        return FakeQuery(self, "select").select(columns)

    def insert(self, payload):
        return FakeQuery(self, "insert", payload)

    def update(self, payload):
        return FakeQuery(self, "update", payload)


class FakeClient:
    def __init__(self, rows):
        self.users = FakeTable(rows)

    def table(self, name):
        assert name == "users"
        return self.users


class RegisterTests(unittest.TestCase):
    def _client(self, rows):
        client = FakeClient(rows)
        patcher = patch.object(auth_module, "get_supabase_client", return_value=client)
        patcher.start()
        self.addCleanup(patcher.stop)
        return client

    def test_creates_new_account(self):
        client = self._client([])
        result = auth_module.create_user("Nou@Example.COM", "parola-mea", "Ion Popescu")
        self.assertEqual(result["email"], "nou@example.com")
        self.assertEqual(result["fullName"], "Ion Popescu")
        row = client.users.rows[0]
        self.assertEqual(row["email"], "nou@example.com")
        self.assertTrue(auth_module.verify_password("parola-mea", row["password_hash"]))

    def test_rejects_email_with_existing_password(self):
        self._client([
            {"id": 7, "email": "vechi@example.com", "name": "Vechi", "password_hash": auth_module.get_password_hash("alta")}
        ])
        with self.assertRaises(ValueError) as ctx:
            auth_module.create_user("vechi@example.com", "parola-mea", "Altcineva")
        self.assertIn("deja înregistrat", str(ctx.exception))

    def test_sets_password_on_legacy_account_without_hash(self):
        """Conturile din era magic link (`password_hash` NULL) își păstrează id-ul și datele."""
        client = self._client([
            {"id": 32, "email": "vechi@example.com", "name": "Nume Vechi", "password_hash": None, "age": 30}
        ])
        result = auth_module.create_user("Vechi@example.com", "parola-noua", "Nume Nou")

        self.assertEqual(result["email"], "vechi@example.com")
        self.assertEqual(result["fullName"], "Nume Nou")
        self.assertEqual(len(client.users.rows), 1, "nu trebuie creat un rând nou")
        row = client.users.rows[0]
        self.assertEqual(row["id"], 32, "id-ul vechi se păstrează (analizele/recomandările rămân legate)")
        self.assertEqual(row["age"], 30, "restul profilului rămâne neatins")
        self.assertTrue(auth_module.verify_password("parola-noua", row["password_hash"]))

    def test_legacy_account_can_log_in_after_adoption(self):
        client = self._client([{"id": 32, "email": "vechi@example.com", "name": "Nume Vechi", "password_hash": None}])
        self.assertIsNone(auth_module.authenticate_user("vechi@example.com", "parola-noua"))

        auth_module.create_user("vechi@example.com", "parola-noua", "Nume Nou")

        session = auth_module.authenticate_user("vechi@example.com", "parola-noua")
        self.assertIsNotNone(session)
        self.assertEqual(session["email"], "vechi@example.com")
        self.assertIsNone(auth_module.authenticate_user("vechi@example.com", "gresita"))

    def test_second_adoption_is_rejected(self):
        """A doua înregistrare pe același email vechi nu mai poate schimba parola."""
        self._client([{"id": 32, "email": "vechi@example.com", "name": "Nume Vechi", "password_hash": None}])
        auth_module.create_user("vechi@example.com", "prima-parola", "Primul")
        with self.assertRaises(ValueError) as ctx:
            auth_module.create_user("vechi@example.com", "a-doua-parola", "Al Doilea")
        self.assertIn("deja înregistrat", str(ctx.exception))


if __name__ == "__main__":
    unittest.main()
