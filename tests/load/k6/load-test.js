import http from "k6/http";
import { check, sleep } from "k6";

export const options = {
  scenarios: {
    ramping_load: {
      executor: "ramping-vus",
      startVUs: 1,
      stages: [
        { duration: "2m", target: 10 },
        { duration: "5m", target: 25 },
        { duration: "5m", target: 50 },
        { duration: "3m", target: 0 },
      ],
      gracefulRampDown: "30s",
    },
  },
  thresholds: {
    http_req_failed: ["rate<0.02"],
    http_req_duration: ["p(95)<1200", "p(99)<2500"],
  },
};

const BASE_URL = __ENV.BASE_URL || "http://localhost:8000";

export default function () {
  const healthRes = http.get(`${BASE_URL}/health`);
  check(healthRes, { "health 200": (r) => r.status === 200 });
  const listingsRes = http.get(`${BASE_URL}/api/v1/listings?page=1&page_size=20`);
  check(listingsRes, { "listings acceptable": (r) => [4].includes(r.status) });
  sleep(1);
}
