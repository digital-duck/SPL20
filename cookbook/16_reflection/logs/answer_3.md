Here's an example of how you could design a URL shortener system:

1.  **System Components:**
    *   **URL Shortener Service:** This service will handle incoming requests for shortening URLs and store the mapping between shortened URLs and original URLs in a database.
    *   **Database:** This is where all the mappings between shortened URLs and original URLs are stored.
    *   **Web Server:** This server will handle incoming HTTP requests from users to shorten their URLs.
    *   **URL Shortener Script:** This script runs on the server-side to shorten URLs.

2.  **System Flow:**
    *   When a user submits a URL for shortening, they enter it in a web form and click the "Shorten" button.
    *   The web server sends this information to the URL shortener service via an HTTP request.
    *   The URL shortener service generates a unique shortened URL and stores the mapping between this shortened URL and the original URL in the database.
    *   The URL shortener service returns the shortened URL to the user's web browser.

3.  **Database Schema:**
    ```sql
CREATE TABLE urls (
    id INT PRIMARY KEY,
    original_url VARCHAR(255) NOT NULL,
    short_url VARCHAR(255) NOT NULL,
    ip_address VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

4.  **URL Shortener Script:**
    Here's an example of how the URL shortener script could be written in Python:
    ```python
import uuid
import hashlib
import sqlite3
from flask import Flask, request, jsonify

app = Flask(__name__)

class UrlShortener:
    def __init__(self, db_name):
        self.db_name = db_name
        self.conn = sqlite3.connect(db_name)
        self.cursor = self.conn.cursor()

    def shorten_url(self, original_url):
        short_url = f"{hashlib.sha256(original_url.encode()).hexdigest()}"
        self.cursor.execute("INSERT INTO urls (original_url, short_url) VALUES (?, ?)", (original_url, short_url))
        self.conn.commit()
        return short_url

    def get_original_url(self, short_url):
        result = self.cursor.execute("SELECT original_url FROM urls WHERE short_url = ?", (short_url,))
        original_url = result.fetchone()[0]
        if original_url is None:
            raise ValueError("Invalid shortened URL")
        return original_url

url_shortener = UrlShortener("urls.db")

@app.route('/shorten', methods=['POST'])
def shorten():
    data = request.get_json()
    original_url = data['original_url']
    short_url = url_shortener.shorten_url(original_url)
    return jsonify({'short_url': short_url})

@app.route('/getOriginalUrl', methods=['GET'])
def get_original_url:
    short_url = request.args.get('short_url')
    try:
        original_url = url_shortener.get_original_url(short_url)
        return jsonify({'original_url': original_url})
    except ValueError as e:
        return jsonify({'error': str(e)}), 400

if __name__ == '__main__':
    app.run(debug=True)

```

5.  **Security Considerations:**
    *   IP Address Verification
    *   Cookie-Based System
    *   HTTPS Encryption

6.  **Scalability:**
    *   Distributed Architecture
    *   Load Balancing
    *   Caching Mechanism