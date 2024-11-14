from flask import Flask, request, jsonify
from flask_cors import CORS
import redis
import time

app = Flask(__name__)
CORS(app, expose_headers=["X-Ratelimit-Remaining", "X-Ratelimit-Limit", "X-Ratelimit-Retry-After"])

# Connect to Redis
redis_client = redis.Redis(host='localhost', port=6379, db=0)

# Token Bucket settings
MAX_TOKENS = 10
REFILL_RATE = 1  # Tokens added per second

def rate_limit(client_id):
    current_time = int(time.time())
    key = f"rate_limit:{client_id}"

    # Retrieve token bucket data
    last_refill_time = int(redis_client.hget(key, "last_refill_time") or 0)
    tokens = int(redis_client.hget(key, "tokens") or MAX_TOKENS)

    # Calculate tokens to add based on elapsed time
    time_since_last_refill = current_time - last_refill_time
    if time_since_last_refill >= REFILL_RATE:
        tokens = min(MAX_TOKENS, tokens + time_since_last_refill * REFILL_RATE)
        redis_client.hset(key, "tokens", tokens)
        redis_client.hset(key, "last_refill_time", current_time)

    # Check and decrement tokens if available
    if tokens > 0:
        tokens -= 1
        redis_client.hset(key, "tokens", tokens)  # Update the token count
        return True, tokens
    else:
        return False, None

@app.route('/request', methods=['GET'])
def handle_request():
    client_id = request.remote_addr
    allowed, tokens_left = rate_limit(client_id)

    response = jsonify({"message": "Request allowed" if allowed else "Rate limit exceeded"})
    response.headers["X-Ratelimit-Limit"] = MAX_TOKENS
    response.headers["X-Ratelimit-Remaining"] = tokens_left if tokens_left is not None else 0
    if not allowed:
        response.headers["X-Ratelimit-Retry-After"] = 1  # Retry after 1 second
        return response, 429
    return response, 200

if __name__ == "__main__":
    app.run(port=5001)
