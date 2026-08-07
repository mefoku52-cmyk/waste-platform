import http from "k6/http";
import { check } from "k6";

const BASE_URL = __ENV.BASE_URL || "http://localhost:8000";

export function listCompanies(token = null) {
  const res = http.get(`${BASE_URL}/api/v1/companies?page=1&page_size=20`, {
    headers: token ? { Authorization: `Bearer ${token}` } : {},
  });
  check(res, { "companies endpoint reachable": (r) => [4].includes(r.status) });
  return res;
}
