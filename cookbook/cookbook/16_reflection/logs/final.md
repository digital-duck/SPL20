# URL Shortener System Design

## Overview

A URL shortener is a service that takes a long URL and returns a shortened version of it. The shortened URL points back to the original URL. This design provides a scalable, secure, and user-friendly URL shortening service.

### Components

1.  **Distributed Database**: Stores information about each URL, including the original URL and its corresponding short code.
2.  **URL Shortening Service**: Generates short codes and stores them in the distributed database.
3.  **Load Balancer**: Distributes incoming requests across multiple servers to ensure efficient performance and reduce single-point failures.
4.  **Frontend**: Handles user requests to shorten URLs and provides the shortened URL.

## Distributed Database Schema

The distributed database schema should store the following information for each URL:

| Field Name | Data Type | Description |
| --- | --- | --- |
| `id` | `int` | Unique identifier for the URL. |
| `original_url` | `varchar(255)` | The original long URL. |
| `short_code` | `varchar(10)` | A unique short code corresponding to the original URL. |

## Load Balancer Configuration

The load balancer configuration should distribute incoming requests across multiple servers as follows:

1.  **IP Hash**: Use IP hashing to ensure that incoming requests from a specific IP address are always routed to the same server.
2.  **Round-Robin**: Implement round-robin routing to ensure that the load balancer distributes incoming requests evenly across all servers.

## URL Shortening Service

### Algorithm

1.  Generate a random short code of 6 characters (e.g., `ABC123`) for each new URL.
2.  Insert a record into the distributed database with the short code and the original URL.

### Code Snippet (Python)

```python
import hashlib
from flask import Flask, request, jsonify

app = Flask(__name__)

# Distributed database configuration
db_config = {
    "Server 1": {"host": "192.168.1.100", "port": 5432},
    "Server 2": {"host": "192.168.1.101", "port": 5433},
}

def generate_short_code(original_url):
    """Generate a random short code using SHA-256 hash of the original URL"""
    return hashlib.sha256(original_url.encode()).hexdigest()[:6]

@app.route('/shorten', methods=['POST'])
def shorten_url():
    original_url = request.json['original_url']
    if not original_url:
        return jsonify({'error': 'Original URL is required'}), 400

    short_code = generate_short_code(original_url)
    # Insert record into distributed database
    db_config[request.remote_addr]['db'].insert_one({
        "id": len(db_config[request.remote_addr]['db']),
        "original_url": original_url,
        "short_code": short_code,
    })
    return jsonify({'short_code': f'/{short_code}'})

if __name__ == '__main__':
    app.run(debug=True)
```

## Frontend Implementation (JavaScript)

### Code Snippet

```javascript
const urlShortenerService = new URLShortener();

function shortenUrl(url) {
    const shortCode = urlShortenerService.shortenUrl(url);
    // Return the shortened URL to the user
    return shortCode;
}

// Example usage:
const originalUrl = "https://www.example.com/very-long-url";
const shortenedUrl = shortenUrl(originalUrl);
console.log(shortenedUrl); // Output: /ABCDEFG123
```

## Security Considerations

1.  **Validate User Input**: Ensure that the input URL is valid and not malicious.
2.  **Use HTTPS**: Use HTTPS to encrypt data in transit.
3.  **Implement Rate Limiting**: Implement rate limiting to prevent abuse.

### Security Measures

*   IP Blocking: To prevent abuse, we can implement IP blocking by storing information about each IP address that has accessed the shortened URL.
*   User Authentication: We should consider implementing user authentication for users who want to share their own short codes with others.
*   CAPTCHA Verification: For users who access our API frequently, we can require them to solve a CAPTCHA challenge.

### Conclusion

This design provides a scalable and secure URL shortening service. By distributing the database across multiple servers, we improve scalability and reliability. Implementing rate limiting and IP blocking ensures that the system is protected from abuse.