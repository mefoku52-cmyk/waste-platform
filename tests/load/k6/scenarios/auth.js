import http from "k6/http";
import { check } from "k6";

const BASE_URL = __ENV.BASE_URL || "http://localhost:8000";

export function loginScenario(email, password) {
  const payload = JSON.stringify({ email, password });
  const res = http.post(`${BASE_URL}/api/v1/auth/login`, payload, {
    headers: { "Content-Type": "application/json" },
  });
  check(res, { "login returns expected status": (r) => [4].includes(r.status) });
  if (res.status === 200) {
    const body = res.json();
    return body.access_token || null;
  }
  return null;
}
