import time
import requests
import concurrent.futures
from redis import Redis

# Redis setup
redis_client = Redis(host='localhost', port=6379, db=0)

# Lua script for rate limiting with a lock
RATE_LIMITER_SCRIPT = """
local key = KEYS[1]
local lock_key = KEYS[2]
local max_tokens = tonumber(ARGV[1])
local refill_interval = tonumber(ARGV[2])  -- Expiration in seconds
local current_time = tonumber(ARGV[3])  -- Current time in seconds
local lock_ttl = tonumber(ARGV[4])  -- Lock time-to-live in milliseconds

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
if time_since_last_refill > 0 then
    local refill_tokens = math.min(max_tokens, tokens + math.floor(time_since_last_refill / refill_interval))
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
    result = -1
end

-- Release the lock
redis.call("DEL", lock_key)
return result

"""

def rate_limited_request():
    max_tokens = 10
    refill_interval = 60
    lock_ttl = 1000  # 1000 milliseconds
    current_time = int(time.time() * 1000)  # Current time in milliseconds
    
    while True:
        remaining_tokens = redis_client.eval(
            RATE_LIMITER_SCRIPT,
            2,  # Number of keys
            "token_count", "rate_limit_lock",
            max_tokens, refill_interval, current_time, lock_ttl
        )
        
        if remaining_tokens >= 0:
            return 200, remaining_tokens  # Successful response
        elif remaining_tokens == -1:
            return 429, 0  # Rate-limited response
        else:
            # Lock not acquired, wait briefly and retry
            time.sleep(0.01)

def send_request():
    status_code, remaining = rate_limited_request()
    return status_code, remaining

def test_concurrent_requests(num_requests):
    with concurrent.futures.ThreadPoolExecutor() as executor:
        futures = [executor.submit(send_request) for _ in range(num_requests)]
        results = [future.result() for future in concurrent.futures.as_completed(futures)]
    
    # Count successful and rate-limited responses
    success_count = sum(1 for result in results if result[0] == 200)
    rate_limited_count = sum(1 for result in results if result[0] == 429)
    
    print(f"Successful requests: {success_count}")
    print(f"Rate-limited requests: {rate_limited_count}")
    print("X-Ratelimit-Remaining values:", [result[1] for result in results])

# Test with different levels of concurrency
if __name__ == "__main__":
    print("Testing with 5 concurrent requests:")
    test_concurrent_requests(5)
    
    print("\nTesting with 50 concurrent requests:")
    test_concurrent_requests(50) 