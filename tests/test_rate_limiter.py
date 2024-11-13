import unittest
import requests

class TestRateLimiter(unittest.TestCase):

    def test_request_allowed(self):
        response = requests.get("http://localhost:5001/request")
        self.assertEqual(response.status_code, 200)
        self.assertIn("X-Ratelimit-Remaining", response.headers)

    def test_rate_limit_exceeded(self):
        for _ in range(15):  # Exceed the limit deliberately
            response = requests.get("http://localhost:5001/request")
        self.assertEqual(response.status_code, 429)
        self.assertIn("X-Ratelimit-Retry-After", response.headers)

if __name__ == "__main__":
    unittest.main()
