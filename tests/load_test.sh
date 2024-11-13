#!/bin/bash

# Load test with Apache Benchmark
# -n 100 requests, -c 10 concurrent requests
ab -n 100 -c 10 http://localhost:5001/request
