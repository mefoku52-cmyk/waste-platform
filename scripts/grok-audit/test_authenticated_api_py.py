import http.client
import json

LOGIN_REQ = json.dumps({"email": "admin@cmep.dev", "password": "Admin123!"})

conn = http.client.HTTPConnection("localhost", 8001)
conn.request(
    "POST", "/api/v1/auth/login", LOGIN_REQ, {"Content-Type": "application/json"}
)
r = conn.getresponse()
data = json.loads(r.read().decode())
token = data["accessToken"]
print("Login OK, token získaný (nevypisuje sa)")

for path in ["/api/v1/auth/me", "/api/v1/users", "/api/v1/listings"]:
    print(f"\n=== GET {path} ===")
    conn = http.client.HTTPConnection("localhost", 8001)
    conn.request("GET", path, headers={"Authorization": f"Bearer {token}"})
    r = conn.getresponse()
    print(f"HTTP status: {r.status}")
    print(r.read().decode())
    conn.close()
