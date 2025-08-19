import http from 'k6/http';
import { sleep } from 'k6';

export let options = {
  stages: [
    { target: 400, duration: '3s'  },
    // { target: 400, duration: '27s' },
    { target: 600, duration: '2s'  },
    // { target: 600, duration: '18s' },
    { target: 800, duration: '1s'  },
    // { target: 800, duration: '9s' },
  ]
};

export default function () {
  http.get('http://nginx/search');  // target your nginx service in docker-compose
  sleep(1);
}
