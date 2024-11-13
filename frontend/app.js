function makeRequest() {
    fetch("http://localhost:5001/request")
      .then(response => {
        return response.json().then(data => {
          document.getElementById("response").innerText = JSON.stringify(data);
          console.log("X-Ratelimit-Remaining:", response.headers.get("X-Ratelimit-Remaining"));
          console.log("X-Ratelimit-Limit:", response.headers.get("X-Ratelimit-Limit"));
          console.log("X-Ratelimit-Retry-After:", response.headers.get("X-Ratelimit-Retry-After"));
        });
      })
      .catch(error => console.error("Error:", error));
  }
  