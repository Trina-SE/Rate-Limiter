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
