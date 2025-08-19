import http from 'k6/http';
import { sleep } from 'k6';

export let options = {
  stages: [
    { target: 400, duration: '3s'  },
    { target: 400, duration: '27s' },
    { target: 600, duration: '2s'  },
    { target: 600, duration: '18s' },
    { target: 800, duration: '1s'  },
    { target: 800, duration: '9s'  },
  ]
};

function randInt(min, max) {
  return Math.floor(Math.random() * (max - min)) + min;
}

function randChoice(arr) {
  return arr[randInt(0, arr.length)];
}

export default function () {
  const host = randChoice(['alpha', 'beta', 'gamma']);
  const trxType = randChoice(["mudarabah", "musharakah", "murabaha", "qard hasanah", "ijarah", "sukuk"]);
  const account = randInt(10000000, 99999999);
  const fromAccount = randInt(10000000, 99999999);
  const toAccount = randInt(10000000, 99999999);
  const amount = Math.round((Math.random() * 5000000) * 100) / 100;
  const fromAmount = Math.round((Math.random() * 5000000) * 100) / 100;
  const toAmount = Math.round((Math.random() * 5000000) * 100) / 100;
  const time = new Date(Date.now() - Math.random() * 10000000000).toISOString();
  const fromTime = new Date(Date.now() - Math.random() * 10000000000).toISOString();
  const toTime = new Date(Date.now() - Math.random() * 10000000000).toISOString();

  const params = {
    headers: {
      "Host": `${host}.local`,
    }
  };

  const reqType = randInt(0, 3);
  if (reqType === 0) { // GET search req
    const type = randChoice(['transaction', 'account', null]);
    const q = type === 'transaction' ? trxType : account;
    let url = 'http://nginx/search?';
    if (randInt(0, 1))
      url += `q=${q}`;
    if (randInt(0, 1)) {
      if (url[-1] !== '?')
        url += '&';
      url += `type=${type}`;
    }

    http.get(url, params);
  } else if (reqType === 1) { // POST search req
    let body = {}
    if (randInt(0, 1)) body["timeFrom"] = fromTime;
    if (randInt(0, 1)) body["timeTo"] = toTime;
    if (randInt(0, 1)) body["amountFrom"] = fromAmount;
    if (randInt(0, 1)) body["amountTo"] = toAmount;
    if (randInt(0, 1)) body["account"] = account;
    if (randInt(0, 1)) body["trxType"] = trxType;

    http.post('http://nginx/search', JSON.stringify(body), params);
  } else { // POST transfer req
    const body = {
      fromAccount,
      toAccount,
      amount,
      trxType,
      time
    };

    http.post('http://nginx/transfer', JSON.stringify(body), params);
  }

  sleep(1);
}
