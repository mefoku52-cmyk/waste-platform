import http from "k6/http";
import { check, sleep } from "k6";

export const options = {
  scenarios: {
    breakpoint: {
      executor: "ramping-arrival-rate",
      startRate: 5,
      timeUnit: "1s",
      preAllocatedVUs: 20,
      maxVUs: 300,
      stages: [
        { target: 20, duration: "2m" },
        { target: 50, duration: "2m" },
        { target: 100, duration: "2m" },
        { target: 150, duration: "2m" },
      ],
    },
  },
  thresholds: {
    http_req_failed: ["rate<0.05"],
    http_req_duration: ["p(95)<2500"],
  },
};

const BASE_URL = __ENV.BASE_URL || "http://localhost:8000";

export default function () {
  const res = http.get(`${BASE_URL}/health`);
  check(res, { "status 200": (r) => r.status === 200 });
  sleep(0.2);
}
