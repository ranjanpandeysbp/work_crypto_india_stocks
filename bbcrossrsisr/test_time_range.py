import requests
from datetime import datetime, timezone, timedelta

# Request data from recent past (2 hours ago)
end_ts = int((datetime.now(timezone.utc) - timedelta(hours=2)).timestamp())
start_ts = end_ts - (3600 * 72)  # 72 hours back

params = {
    'resolution': '1h',
    'symbol': 'BTCUSD',
    'start': start_ts,
    'end': end_ts
}

print('Testing with recent-past timeframe:')
print(f'Start: {datetime.fromtimestamp(start_ts)} ({start_ts})')
print(f'End: {datetime.fromtimestamp(end_ts)} ({end_ts})')
print('')

r = requests.get('https://api.delta.exchange/v2/history/candles', params=params, timeout=10)
data = r.json()

result_count = len(data.get('result', []))
print(f'Response: success={data.get("success")}, result_count={result_count}')

if data.get('result'):
    print(f'✅ SUCCESS! Got {result_count} candles')
    print(f'First candle: {data["result"][0]}')
else:
    print(f'❌ Still no data - this is the issue!')
