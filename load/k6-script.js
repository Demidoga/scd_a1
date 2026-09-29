// Milestone 8 load test (docs/assignment/12-kubernetes-autoscaling.md).
// Drives POST /api/complaints and GET /api/stats + GET /api/complaints hard
// enough, for long enough, to push the backend Deployment's CPU utilization
// past the HPA's 60% target (k8s/base/hpa.yaml) and hold it there while
// replicas come up.
//
// Target defaults to the k3d Ingress published by scripts/k8s/create-cluster.sh
// (http://localhost:8080). Override with -e BASE_URL=... for a different
// cluster/port.
//
// IMPORTANT — read before running: POST /api/complaints is rate-limited per
// client IP (RATE_LIMIT_REQUESTS=10 / RATE_LIMIT_WINDOW_SECONDS=60,
// k8s/base/configmap.yaml). On k3d every request arriving through the
// Ingress shares one source IP after the built-in load balancer rewrites it
// (docs/ENGINEERING-NOTES.md, Milestone 7, "Client IP on k3d") — so with the
// default limit this script gets 429s almost immediately, however many VUs
// you run, and never generates enough CPU load to trip the HPA. Bump
// RATE_LIMIT_REQUESTS to something load-test-sized before running this (see
// the operational guide) and put it back afterwards.
import http from "k6/http";
import { check, sleep } from "k6";
import { Counter } from "k6/metrics";

const BASE_URL = __ENV.BASE_URL || "http://localhost:8080";

const errorCount = new Counter("civicpulse_errors");

const LOCATIONS = [
  "Block 4, Gulshan-e-Iqbal, Karachi",
  "Sector G-9, Islamabad",
  "Model Town, Lahore",
  "Latifabad Unit 7, Hyderabad",
  "Cantt Station Road, Rawalpindi",
];

const COMPLAINT_TEXTS = [
  "No water supply in our street for the past three days, please send a tanker.",
  "Streetlight outside house 12 has been broken for two weeks, it's very dark at night.",
  "Garbage has not been collected from this block in over a week, it's piling up.",
  "Main road has a large pothole that's damaging vehicles near the market.",
  "Frequent power outages every evening between 6pm and 9pm in this area.",
  "Sewage is overflowing onto the street after yesterday's rain.",
];

function randomOf(list) {
  return list[Math.floor(Math.random() * list.length)];
}

export const options = {
  scenarios: {
    // GET traffic is not rate-limited (app/routes/complaints.py,
    // app/routes/stats.py only guard the POST route) so it carries most of
    // the ramp; it still exercises PostgreSQL reads and the Redis stats
    // cache (docs/architecture/cache.md).
    read_traffic: {
      executor: "ramping-vus",
      exec: "readTraffic",
      startVUs: 5,
      stages: [
        { duration: "1m", target: 20 },
        { duration: "2m", target: 50 },
        { duration: "1m30s", target: 50 },
        { duration: "30s", target: 0 },
      ],
      gracefulRampDown: "10s",
    },
    // A small, steady trickle of complaint creation so the triage pipeline
    // (CPU-heavier than a cache read) is represented in the mix without
    // blowing through the per-IP rate limit in the first few seconds.
    write_traffic: {
      executor: "constant-vus",
      exec: "writeTraffic",
      vus: 2,
      duration: "5m",
    },
  },
  thresholds: {
    http_req_failed: ["rate<0.01"],
    http_req_duration: ["p(95)<500"],
  },
};

export function readTraffic() {
  const statsRes = http.get(`${BASE_URL}/api/stats`);
  check(statsRes, { "stats status is 200": (r) => r.status === 200 }) ||
    errorCount.add(1);

  const listRes = http.get(`${BASE_URL}/api/complaints?page=1&page_size=20`);
  check(listRes, { "list status is 200": (r) => r.status === 200 }) ||
    errorCount.add(1);

  sleep(0.5);
}

export function writeTraffic() {
  const payload = JSON.stringify({
    text: randomOf(COMPLAINT_TEXTS),
    location: randomOf(LOCATIONS),
  });
  const res = http.post(`${BASE_URL}/api/complaints`, payload, {
    headers: { "Content-Type": "application/json" },
  });
  check(res, { "create status is 201": (r) => r.status === 201 }) ||
    errorCount.add(1);

  sleep(2);
}
