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
REFILL_BUFFER = 0.2  # 200 ms buffer to prevent immediate refilling after burst load
LOCK_TTL = 500  # Reduced lock TTL to 500 ms

def rate_limit(client_id):
    current_time = int(time.time())
    key = f"rate_limit:{client_id}"
    lock_key = f"{key}_lock"

    # Lua script for atomic rate limiting in Redis
    lua_script = """
    local key = KEYS[1]
    local lock_key = KEYS[2]
    local max_tokens = tonumber(ARGV[1])
    local refill_rate = tonumber(ARGV[2])
    local current_time = tonumber(ARGV[3])
    local lock_ttl = tonumber(ARGV[4])
    local refill_buffer = tonumber(ARGV[5])

    -- Attempt to acquire the lock
    local lock_acquired = redis.call("SET", lock_key, "locked", "PX", lock_ttl, "NX")
    if not lock_acquired then
        return -2  -- Signal that the lock was not acquired
    end

    -- Initialize or refill token bucket
    local last_refill_time = tonumber(redis.call("HGET", key, "last_refill_time")) or 0
    local tokens = tonumber(redis.call("HGET", key, "tokens")) or max_tokens

    -- Calculate tokens to add based on time since last refill
    local time_since_last_refill = current_time - last_refill_time
    local adjusted_refill_time = last_refill_time + refill_buffer

    if time_since_last_refill > refill_rate and current_time > adjusted_refill_time then
        local refill_tokens = math.min(max_tokens, tokens + math.floor(time_since_last_refill / refill_rate))
        redis.call("HSET", key, "tokens", refill_tokens)
        redis.call("HSET", key, "last_refill_time", current_time)
        tokens = refill_tokens
    end

    -- Decrement token if available
    local result
    if tokens > 0 then
        redis.call("HINCRBY", key, "tokens", -1)
        result = tokens - 1
    else
        result = -1  -- Rate limit exceeded
    end

    -- Release the lock
    redis.call("DEL", lock_key)
    return result
    """

    tokens = redis_client.eval(lua_script, 2, key, lock_key, MAX_TOKENS, REFILL_RATE, current_time, LOCK_TTL, REFILL_BUFFER)
    if tokens >= 0:
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
