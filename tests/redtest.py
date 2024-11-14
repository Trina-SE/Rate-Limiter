import time
import requests
from redlock import Redlock
from redis import Redis
import concurrent.futures

# Redis setup
redis_client = Redis(host='localhost', port=6379, db=0)
lock_manager = Redlock([{"host": "localhost", "port": 6379, "db": 0}])

# Rate limiting parameters
MAX_TOKENS = 10
WINDOW_INTERVAL = 60  # Rate limit window in seconds
LOCK_TTL = 500  # Lock time-to-live in milliseconds

# URL of the rate-limited endpoint
URL = "http://localhost:5001/request"

# Clear any pre-existing token_count key in Redis to prevent WRONGTYPE errors
redis_client.delete("token_count")

def rate_limited_request():
    # Acquire a lock for modifying the token count
    lock = lock_manager.lock("rate-limit-lock", LOCK_TTL)

    if lock:
        try:
            # Retrieve or initialize current token count
            current_count = redis_client.get("token_count")
            if current_count is None:
                # Initialize token count and set expiration for the window interval
                redis_client.set("token_count", MAX_TOKENS - 1, ex=WINDOW_INTERVAL)
                remaining_tokens = MAX_TOKENS - 1
            else:
                # Convert the token count to an integer
                current_count = int(current_count)
                if current_count > 0:
                    # Decrement token count
                    redis_client.decr("token_count")
                    remaining_tokens = current_count - 1
                else:
                    # No tokens left, rate limit exceeded
                    remaining_tokens = 0
                    return 429, remaining_tokens  # Rate-limited response

            # Return successful response with remaining tokens
            return 200, remaining_tokens

        finally:
            # Release the lock after processing the request
            lock_manager.unlock(lock)

    else:
        # If lock not acquired, wait briefly and retry
        time.sleep(0.01)
        return rate_limited_request()

def send_request():
    status_code, remaining = rate_limited_request()
    return status_code, remaining

def test_concurrent_requests(num_requests, delay=0.01):
    with concurrent.futures.ThreadPoolExecutor() as executor:
        futures = [executor.submit(send_request) for _ in range(num_requests)]
        results = [future.result() for future in concurrent.futures.as_completed(futures)]
        
        # Adding a slight delay to space out requests can help with testing
        time.sleep(delay)


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
    
    print("\nTesting with 100 concurrent requests:")
    test_concurrent_requests(100)
