local key = KEYS[1]
local max_tokens = tonumber(ARGV[1])
local refill_rate = tonumber(ARGV[2])
local current_time = tonumber(ARGV[3])

local bucket = redis.call("HGETALL", key)
if #bucket == 0 then
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
    return -1
end
