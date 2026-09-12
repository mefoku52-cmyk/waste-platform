import getpass
import json
import urllib.error
import urllib.request

token = input("TOKEN=").strip().strip('"')
newpass = getpass.getpass("NEWPASS=")
body = json.dumps({"token": token, "newPassword": newpass}).encode()
req = urllib.request.Request(
    "http://127.0.0.1:8001/api/v1/auth/reset-password",
    data=body,
    headers={"Content-Type": "application/json"},
    method="POST",
)
try:
    r = urllib.request.urlopen(req, timeout=20)
    print("HTTP", r.status)
    print("HEAD", r.read().decode()[:160])
except urllib.error.HTTPError as e:
    print("HTTP", e.code)
    print("HEAD", e.read().decode()[:160])
