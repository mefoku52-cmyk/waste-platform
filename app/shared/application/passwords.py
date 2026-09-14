import bcrypt

_MAX_BCRYPT_BYTES = 72


class PasswordService:
    def hash_password(self, raw_password: str) -> str:
        pw_bytes = raw_password.encode("utf-8")[:_MAX_BCRYPT_BYTES]
        return bcrypt.hashpw(pw_bytes, bcrypt.gensalt()).decode("utf-8")

    def verify_password(self, raw_password: str, hashed_password: str) -> bool:
        pw_bytes = raw_password.encode("utf-8")[:_MAX_BCRYPT_BYTES]
        return bcrypt.checkpw(pw_bytes, hashed_password.encode("utf-8"))


password_service = PasswordService()
