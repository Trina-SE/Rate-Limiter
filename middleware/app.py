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

    # Lua script for atomic rate limiting in Redis
    lua_script = """
    local key = KEYS[1]
    local max_tokens = tonumber(ARGV[1])
    local refill_rate = tonumber(ARGV[2])
    local current_time = tonumber(ARGV[3])

    local bucket = redis.call("HGETALL", key)
    if table.getn(bucket) == 0 then
        redis.call("HMSET", key, "tokens", max_tokens - 1, "last_refill", current_time)
        return max_tokens - 1
    end

    local tokens = tonumber(bucket[2])
    local last_refill = tonumber(bucket[4])
    local elapsed = current_time - last_refill
    local new_tokens = math.min(max_tokens, tokens + (elapsed * refill_rate))

    if new_tokens > 0 then
        redis.call("HMSET", key, "tokens", new_tokens - 1, "last_refill", current_time)
        return new_tokens - 1
    else
        return -1  -- Rate limit exceeded
    end
    """

    tokens = redis_client.eval(lua_script, 1, key, MAX_TOKENS, REFILL_RATE, current_time)
    if tokens >= 0:
        return True, tokens
    else:
        return False, None

@app.route('/request', methods=['GET'])
def handle_request():
    client_id = request.remote_addr
    allowed, tokens_left = rate_limit(client_id)

    if allowed:
        response = jsonify({"message": "Request allowed"})
        response.headers["X-Ratelimit-Remaining"] = tokens_left
        response.headers["X-Ratelimit-Limit"] = MAX_TOKENS
        return response, 200
    else:
        response = jsonify({"message": "Rate limit exceeded"})
        response.headers["X-Ratelimit-Retry-After"] = 1  # Retry after 1 second
        return response, 429

if __name__ == "__main__":
    app.run(port=5001)
