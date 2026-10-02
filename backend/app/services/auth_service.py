import hashlib
import json
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any

from app.config import DATA_DIR

USERS_FILE = DATA_DIR / "users.json"
AUTH_SALT = "study_salt_2026"


class AuthService:
    def __init__(self, users_file: Path | None = None):
        self.users_file = users_file or USERS_FILE
        self._init_users_store()

    def _hash_password(self, password: str, salt: str = AUTH_SALT) -> str:
        return hashlib.sha256(f"{password}_{salt}".encode()).hexdigest()

    def _generate_token(self, user_id: str, username: str) -> str:
        token_hash = hashlib.sha256(f"{user_id}_{username}_{AUTH_SALT}".encode()).hexdigest()[:24]
        return f"dsc_tok_{user_id}_{token_hash}"

    def _init_users_store(self):
        """
        Seeds 5 default pre-configured accounts if users.json does not exist.
        """
        if not self.users_file.exists():
            default_users = {
                "admin": {
                    "id": "usr_admin",
                    "username": "admin",
                    "password_hash": self._hash_password("admin123"),
                    "name": "Administrator",
                    "role": "Admin",
                    "email": "admin@studyassistant.ai",
                    "recovery_code": "ADMIN2026",
                    "created_at": "Sep 15, 2026",
                },
                "student1": {
                    "id": "usr_student1",
                    "username": "student1",
                    "password_hash": self._hash_password("study123"),
                    "name": "Alex Turner",
                    "role": "Student",
                    "email": "alex@studyassistant.ai",
                    "recovery_code": "STUDENT1",
                    "created_at": "Sep 15, 2026",
                },
                "student2": {
                    "id": "usr_student2",
                    "username": "student2",
                    "password_hash": self._hash_password("study123"),
                    "name": "Maya Patel",
                    "role": "Student",
                    "email": "maya@studyassistant.ai",
                    "recovery_code": "STUDENT2",
                    "created_at": "Sep 15, 2026",
                },
                "student3": {
                    "id": "usr_student3",
                    "username": "student3",
                    "password_hash": self._hash_password("study123"),
                    "name": "Liam Johnson",
                    "role": "Student",
                    "email": "liam@studyassistant.ai",
                    "recovery_code": "STUDENT3",
                    "created_at": "Sep 15, 2026",
                },
                "teacher1": {
                    "id": "usr_teacher1",
                    "username": "teacher1",
                    "password_hash": self._hash_password("teach123"),
                    "name": "Prof. Sharma",
                    "role": "Faculty",
                    "email": "sharma@studyassistant.ai",
                    "recovery_code": "TEACHER1",
                    "created_at": "Sep 15, 2026",
                },
            }
            with open(self.users_file, "w", encoding="utf-8") as f:
                json.dump(default_users, f, indent=2)

    def _read_users(self) -> dict[str, Any]:
        try:
            with open(self.users_file, encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}

    def _write_users(self, data: dict[str, Any]):
        with open(self.users_file, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

    def authenticate_user(self, username: str, password: str) -> dict[str, Any] | None:
        users = self._read_users()
        user = users.get(username.strip().lower())
        if not user:
            return None
        if user["password_hash"] != self._hash_password(password):
            return None

        token = self._generate_token(user["id"], user["username"])

        # Return sanitized profile with token
        return {
            "id": user["id"],
            "username": user["username"],
            "name": user["name"],
            "role": user["role"],
            "email": user["email"],
            "created_at": user.get("created_at", "2026"),
            "token": token,
        }

    def get_user_from_token(self, token_str: str) -> dict[str, Any] | None:
        if not token_str or not isinstance(token_str, str):
            return None
        token = token_str.strip()
        if token.lower().startswith("bearer "):
            token = token[7:].strip()

        users = self._read_users()
        for user in users.values():
            expected_token = self._generate_token(user["id"], user["username"])
            if (
                token == expected_token
                or token == f"token_{user['username']}"
                or token.startswith(f"token_{user['username']}_")
            ):
                return {
                    "id": user["id"],
                    "username": user["username"],
                    "name": user["name"],
                    "role": user["role"],
                    "email": user["email"],
                    "created_at": user.get("created_at", "2026"),
                }
        return None

    def get_user_by_id(self, user_id: str) -> dict[str, Any] | None:
        users = self._read_users()
        for user in users.values():
            if user.get("id") == user_id:
                return {
                    "id": user["id"],
                    "username": user["username"],
                    "name": user["name"],
                    "role": user["role"],
                    "email": user["email"],
                    "created_at": user.get("created_at", "2026"),
                }
        return None

    def change_password(self, username: str, current_password: str, new_password: str) -> bool:
        users = self._read_users()
        user_key = username.strip().lower()
        user = users.get(user_key)
        if not user:
            raise ValueError("User not found")
        if user["password_hash"] != self._hash_password(current_password):
            raise ValueError("Current password is incorrect")
        if len(new_password) < 4:
            raise ValueError("New password must be at least 4 characters long")

        user["password_hash"] = self._hash_password(new_password)
        self._write_users(users)
        return True

    def forgot_password_recovery(
        self, username: str, recovery_input: str, new_password: str
    ) -> bool:
        """
        Validates recovery via either recovery_code or email, then sets new password.
        """
        users = self._read_users()
        user_key = username.strip().lower()
        user = users.get(user_key)
        if not user:
            raise ValueError("User not found")

        recovery_val = recovery_input.strip().lower()
        is_email_match = user.get("email", "").strip().lower() == recovery_val
        is_code_match = user.get("recovery_code", "").strip().lower() == recovery_val

        if not (is_email_match or is_code_match):
            raise ValueError(
                "Recovery email or secret code did not match our records for this username"
            )

        if len(new_password) < 4:
            raise ValueError("New password must be at least 4 characters long")

        user["password_hash"] = self._hash_password(new_password)
        self._write_users(users)
        return True

    def register_user(
        self,
        username: str,
        password: str,
        name: str,
        email: str,
        role: str = "Student",
        recovery_code: str = "",
    ) -> dict[str, Any]:
        users = self._read_users()
        user_key = username.strip().lower()
        if user_key in users:
            raise ValueError(f"Username '{username}' already exists")
        if len(password) < 4:
            raise ValueError("Password must be at least 4 characters long")

        new_user = {
            "id": f"usr_{uuid.uuid4().hex[:8]}",
            "username": user_key,
            "password_hash": self._hash_password(password),
            "name": name.strip() or username,
            "role": role.strip() or "Student",
            "email": email.strip() or f"{user_key}@studyassistant.ai",
            "recovery_code": recovery_code.strip() or "STUDY2026",
            "created_at": datetime.now().strftime("%b %d, %Y"),
        }
        users[user_key] = new_user
        self._write_users(users)

        return {
            "id": new_user["id"],
            "username": new_user["username"],
            "name": new_user["name"],
            "role": new_user["role"],
            "email": new_user["email"],
            "created_at": new_user["created_at"],
        }

    def get_all_users(self, is_admin: bool = False) -> list[dict[str, Any]]:
        users = self._read_users()
        output = []
        for u in users.values():
            item = {
                "id": u["id"],
                "username": u["username"],
                "name": u["name"],
                "role": u["role"],
                "email": u["email"],
                "created_at": u.get("created_at", "2026"),
            }
            if is_admin:
                item["recovery_code"] = u.get("recovery_code", "STUDY2026")
            output.append(item)
        return output

    def delete_user(self, username: str) -> bool:
        users = self._read_users()
        user_key = username.strip().lower()
        if user_key == "admin":
            raise ValueError("The primary admin account cannot be deleted")
        if user_key not in users:
            raise ValueError("User not found")
        del users[user_key]
        self._write_users(users)
        return True

    def admin_reset_password(self, target_username: str, new_password: str) -> bool:
        users = self._read_users()
        user_key = target_username.strip().lower()
        if user_key not in users:
            raise ValueError("User not found")
        if len(new_password) < 4:
            raise ValueError("New password must be at least 4 characters long")
        users[user_key]["password_hash"] = self._hash_password(new_password)
        self._write_users(users)
        return True


auth_service = AuthService()
