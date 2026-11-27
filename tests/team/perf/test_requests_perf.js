import http from 'k6/http';
import { check, sleep } from 'k6';

const BASE_URL = __ENV.BASE_URL || 'http://localhost:8081';
const VUS = parseInt(__ENV.TARGET_VUS || '1', 10);
const DURATION = __ENV.TARGET_DURATION || '60s';

export const options = {
  scenarios: {
    constant_load: {
      executor: 'constant-vus',
      vus: VUS,
      duration: DURATION,
    },
  },
  thresholds: {
    http_req_failed: ['rate<=0.001'], // unexpected failure rate <= 0.1%
    http_req_duration: ['p(95)<=250'], // p95 latency <= 250ms
  },
};

export function setup() {
  // Authenticate as Bob Manager before load generation starts
  const loginRes = http.post(
    `${BASE_URL}/api/auth/login`,
    JSON.stringify({ email: 'bob@acme.com', password: 'password123' }),
    { headers: { 'Content-Type': 'application/json' } }
  );

  check(loginRes, {
    'setup login succeeded': (r) => r.status === 200,
  });

  const body = JSON.parse(loginRes.body);
  return { token: body.token };
}

export default function (data) {
  const headers = {
    Authorization: `Bearer ${data.token}`,
    Accept: 'application/json',
  };

  const res = http.get(`${BASE_URL}/api/requests`, { headers: headers });

  check(res, {
    'status is 200': (r) => r.status === 200,
    'has content': (r) => {
      try {
        const json = JSON.parse(r.body);
        return json && Array.isArray(json.content);
      } catch (e) {
        return false;
      }
    },
  });

  // Short realistic pause between user reads
  sleep(0.05);
}
