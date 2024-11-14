import time
import requests
import concurrent.futures

# URL of the Flask app's rate-limited endpoint
BASE_URL = "http://localhost:5001/request"

def send_request():
    try:
        response = requests.get(BASE_URL)
        remaining_tokens = response.headers.get("X-Ratelimit-Remaining", "Unknown")
        status_code = response.status_code
        return status_code, remaining_tokens
    except requests.RequestException as e:
        print(f"Request failed: {e}")
        return None, None

def test_concurrent_requests(num_requests):
    with concurrent.futures.ThreadPoolExecutor() as executor:
        futures = [executor.submit(send_request) for _ in range(num_requests)]
        results = [future.result() for future in concurrent.futures.as_completed(futures)]
    
    # Count successful and rate-limited responses
    success_count = sum(1 for result in results if result and result[0] == 200)
    rate_limited_count = sum(1 for result in results if result and result[0] == 429)
    
    print(f"Successful requests: {success_count}")
    print(f"Rate-limited requests: {rate_limited_count}")
    print("X-Ratelimit-Remaining values:", [result[1] for result in results if result])

# Test with different levels of concurrency
if __name__ == "__main__":
    print("Testing with 5 concurrent requests:")
    test_concurrent_requests(5)
    
    print("\nTesting with 50 concurrent requests:")
    test_concurrent_requests(50)
