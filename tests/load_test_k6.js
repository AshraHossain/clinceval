import http from 'k6/http';
import { check, sleep } from 'k6';

export let options = {
  stages: [
    { duration: '30s', target: 5 },   // Ramp up to 5 VUs over 30s
    { duration: '1m', target: 5 },    // Stay at 5 VUs for 1 minute
    { duration: '30s', target: 10 },  // Ramp up to 10 VUs over 30s
    { duration: '1m', target: 10 },   // Stay at 10 VUs for 1 minute
    { duration: '30s', target: 0 },   // Ramp down to 0 VUs
  ],
  thresholds: {
    http_req_duration: ['p(95)<2000', 'p(99)<5000'], // 95th percentile < 2s, 99th < 5s
    http_req_failed: ['rate<0.1'],                    // <10% failure rate
  },
};

const QUERIES = [
  'A 75-year-old female with atrial fibrillation and hypertension needs stroke risk assessment.',
  '65M with pneumonia, respiratory rate 25, BUN 30, systolic BP 110 and altered mental status.',
  'Dyspneic 58yo with leg swelling, recent surgery, and unilateral chest pain.',
  '3-month-old with fall, vomiting, and altered consciousness.',
  '82F on warfarin, INR 2.5, albumin 3.5g/dL, bilirubin 2.1, ascites, no encephalopathy.',
];

export default function () {
  const query = QUERIES[Math.floor(Math.random() * QUERIES.length)];
  const payload = JSON.stringify({ query });

  const params = {
    headers: {
      'Content-Type': 'application/json',
    },
  };

  const res = http.post('http://localhost:8000/api/recommend', payload, params);

  check(res, {
    'status is 200': (r) => r.status === 200,
    'response time < 2s': (r) => r.timings.duration < 2000,
    'has calculator': (r) => r.json('recommendation.calculator') !== null,
    'has rationale': (r) => r.json('recommendation.rationale') !== null,
  });

  sleep(1);
}
