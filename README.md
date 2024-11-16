# Rate-Limiter
A rate limiter is a service that controls the number of requests that can be made to a server or service within a specific time frame. Rate limiting is used to ensure that systems are stable and secure, and to prevent abuse of resources.
# Project Overview
- Algorithm: Token Bucket
- 3 Layer Architecture: frontend, middleware, and backend layers
- Handle response headers in appropriate scenarios: X-Ratelimit-Remaining, X-Ratelimit-Limit, X-Ratelimit-Retry-After
- Race Condition Handle: Using Lua script in Redis
