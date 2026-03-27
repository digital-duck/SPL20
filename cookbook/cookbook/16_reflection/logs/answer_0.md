**URL Shortener System Design**

### Overview

A URL shortener is a web service that takes a long, cumbersome URL and converts it into a shorter, more manageable version. This system will provide users with a unique shortened URL for their original link.

### Requirements

* The system must be able to handle an arbitrary number of users and URLs.
* The system must be able to generate short, unique URLs for each submitted link.
* The system must be able to redirect users back to the original URL when they click on the shortened version.

### System Components

1. **Database**: A database will be used to store information about all the URLs that have been submitted and their corresponding shortened URLs. We'll use a combination of MySQL or PostgreSQL for this purpose.
2. **URL Shortener Service**: A service will handle the following tasks:
	* Generate a shortened URL from an original link.
	* Store the original link in the database with its corresponding shortened URL.
	* Redirect users back to the original link when they click on the shortened version.
3. **Frontend Interface**: A user-friendly interface will be created for users to submit URLs and access their shortened versions.

### System Flow

1. User submits a long, cumbersome URL through the frontend interface.
2. The URL shortener service generates a unique shortened URL and stores it in the database along with the original link.
3. When a user clicks on the shortened URL, the system redirects them to the original URL stored in the database.

### System Design

#### Database Schema
```sql
CREATE TABLE urls (
  id INT PRIMARY KEY,
  original_url VARCHAR(255) NOT NULL,
  shortened_url VARCHAR(10) NOT NULL UNIQUE
);

CREATE TABLE url_logs (
  id INT PRIMARY KEY,
  user_id INT,
  original_url_id INT,
  FOREIGN KEY (original_url_id) REFERENCES urls(id)
);
```

#### URL Shortener Service
```python
import sqlite3

class UrlShortenerService:
    def __init__(self, db_name):
        self.conn = sqlite3.connect(db_name)
        self.cursor = self.conn.cursor()

    def generate_shortened_url(self, original_url):
        # Generate a shortened URL (e.g., 5 characters long)
        import random
        shortened_url = ''.join(random.choice('0123456789') for _ in range(5))
        return shortened_url

    def store_url(self, original_url):
        self.cursor.execute("INSERT INTO urls (original_url, shortened_url) VALUES (?, ?)", (original_url, self.generate_shortened_url(original_url)))
        self.conn.commit()

    def redirect_to_original(self, shortened_url):
        # Find the corresponding original URL in the database
        self.cursor.execute("SELECT original_url FROM urls WHERE shortened_url = ?", (shortened_url,))
        result = self.cursor.fetchone()
        if result:
            return result[0]
        else:
            return None

    def close_connection(self):
        self.conn.close()
```

#### Frontend Interface
```html
<!-- index.html -->
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>URL Shortener</title>
</head>
<body>
    <h1>URL Shortener</h1>
    <form id="url-form">
        <input type="text" id="original-url" placeholder="Enter a URL">
        <button id="submit-btn">Submit</button>
    </form>

    <div id="shortened-url-container"></div>

    <script src="script.js"></script>
</body>
</html>
```

```javascript
// script.js
const form = document.getElementById('url-form');
const shortenedUrlContainer = document.getElementById('shortened-url-container');

form.addEventListener('submit', (e) => {
    e.preventDefault();
    const originalUrl = document.getElementById('original-url').value;
    const urlShortenerService = new UrlShortenerService('urls.db');
    urlShortenerService.store_url(originalUrl);
    shortenedUrlContainer.innerHTML += `<p><a href="${urlShortenerService.redirect_to_original(originalUrl)}">${urlShortenerService.generate_shortened_url(originalUrl)}</a></p>`;
});
```

### Testing

To test the system, you can use tools like Postman or cURL to send HTTP requests to the system's endpoint. For example:

*   **GET /shorten**: Send a GET request to `http://localhost:8080/shorten` with an empty body.
*   **POST /urls**: Send a POST request to `http://localhost:8080/urls` with a JSON payload containing the original URL, like this:

    ```json
{
  "original_url": "https://example.com/long/url"
}
```

###