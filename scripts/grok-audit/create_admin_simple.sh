#!/usr/bin/env bash
set -u

cd ~/waste-platform

echo "=== 1. Schema tabulky users ==="
python3 <<'PY'
from sqlalchemy import create_engine, inspect

engine = create_engine("sqlite:///./var/cmep.db")
inspector = inspect(engine)

print("Tabulky v DB:")
for table_name in inspector.get_table_names():
    print(f"  - {table_name}")

print("
Stlpce tabulky 'users':")
for col in inspector.get_columns("users"):
    print(f"  {col['name']}: {col['type']}")
PY

echo ""
echo "=== 2. Ci uz existuje nejaky pouzivatel ==="
python3 <<'PY'
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

engine = create_engine("sqlite:///./var/cmep.db")
Session = sessionmaker(bind=engine)
session = Session()

result = session.execute(text("SELECT id, email, first_name, last_name FROM users LIMIT 5")).fetchall()
if result:
    print("Existujuci pouzivatelia:")
    for row in result:
        print(f"  id={row[0]}, email={row[1]}, name={row[2]} {row[3]}")
else:
    print("Ziadny pouzivatel v DB")
PY

echo ""
echo "=== 3. Vytvorenie admina so spravnymi stlpcami ==="
python3 <<'PY'
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
import hashlib
import secrets
from datetime import datetime, timezone

engine = create_engine("sqlite:///./var/cmep.db")
Session = sessionmaker(bind=engine)
session = Session()

# Zisti presne stlpce
from sqlalchemy import inspect
inspector = inspect(engine)
columns = [col['name'] for col in inspector.get_columns("users")]
print(f"Dostupne stlpce: {columns}")

# Skontroluj ci uz existuje admin
result = session.execute(text("SELECT id, email FROM users WHERE email = 'admin@cmeplatform.com'")).fetchone()
if result:
    print(f"Admin uz existuje: id={result[0]}, email={result[1]}")
else:
    # Vytvor jednoduche heslo (v realite pouzi PasswordService)
    import uuid
    
    # Priprav data podla dostupnych stlpcov
    user_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc).isoformat()
    
    # Bezpecne hashovanie hesla (jednoducha verzia)
    salt = secrets.token_hex(16)
    password = "Admin123!"
    pwd_hash = f"$scrypt${salt}${hashlib.scrypt(password.encode(), salt=salt.encode(), n=32768, r=8, p=1, dklen=32).hex()}"
    
    # Dynamicky zostav INSERT
    insert_cols = ["id", "email", "password_hash", "first_name", "last_name", "created_at"]
    for col in ["is_active", "is_email_verified", "is_email_verified"]:
        if col in columns:
            insert_cols.append(col)
    
    placeholders = ", ".join([":" + c for c in insert_cols])
    cols_str = ", ".join(insert_cols)
    
    sql = f"INSERT INTO users ({cols_str}) VALUES ({placeholders})"
    
    params = {
        "id": user_id,
        "email": "admin@cmeplatform.com",
        "password_hash": pwd_hash,
        "first_name": "Admin",
        "last_name": "User",
        "created_at": now,
    }
    if "is_active" in columns:
        params["is_active"] = 1
    if "is_email_verified" in columns:
        params["is_email_verified"] = 1
    
    print(f"SQL: {sql}")
    print(f"Params: {params}")
    
    session.execute(text(sql), params)
    session.commit()
    print(f"
Created admin: {user_id}")
PY

echo ""
echo "=== 4. Login test ==="
curl -X POST http://localhost:8001/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@cmeplatform.com","password":"Admin123!"}' 2>&1 | python3 -m json.tool
