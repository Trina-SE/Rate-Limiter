function makeRequest() {
  fetch("http://localhost:5001/request")
    .then(response => {
      // Log rate-limit headers
      console.log("X-Ratelimit-Remaining:", response.headers.get("X-Ratelimit-Remaining"));
      console.log("X-Ratelimit-Limit:", response.headers.get("X-Ratelimit-Limit"));
      console.log("X-Ratelimit-Retry-After:", response.headers.get("X-Ratelimit-Retry-After"));
      
      // Display the JSON response in the HTML
      return response.json();
    })
    .then(data => {
      document.getElementById("response").innerText = JSON.stringify(data);
    })
    .catch(error => console.error("Error:", error));
}
