**URL Shortener System Design**

### Overview

A URL shortener system is a service that reduces long URLs to shorter, unique URLs. The system should handle the following requirements:

* Store and retrieve shortened URLs from a database
* Generate a unique ID for each shortened URL
* Map the original URL to its corresponding shortened URL
* Handle URL redirects when accessing the shortened URL

### System Design

#### Database Schema

Create a database schema to store shortened URLs.

```sql
CREATE TABLE urls (
    id INT PRIMARY KEY,
    original_url VARCHAR(255) NOT NULL,
    shortened_url VARCHAR(255) UNIQUE NOT NULL
);

CREATE TABLE url_mappings (
    id INT PRIMARY KEY,
    original_url_id INT NOT NULL,
    shortened_url_id INT NOT NULL,
    FOREIGN KEY (original_url_id) REFERENCES urls(id),
    FOREIGN KEY (shortened_url_id) REFERENCES urls(id)
);
```

#### Service Layer

Create a service layer that encapsulates the business logic of the URL shortener.

```python
class UrlShortener:
    def __init__(self, db):
        self.db = db

    def shorten_url(self, original_url):
        # Generate a unique ID for the shortened URL
        id = uuid.uuid4()
        shortened_url = f'http://example.com/{id}'
        
        # Store the shortened URL in the database
        query = 'INSERT INTO urls (original_url, shortened_url) VALUES (%s, %s)'
        self.db.execute(query, (original_url, shortened_url))
        
        # Return the shortened URL and its ID
        return {'shortened_url': shortened_url, 'id': id}

    def get_original_url(self, shortened_url):
        # Retrieve the original URL from the database
        query = 'SELECT original_url FROM urls WHERE shortened_url = %s'
        row = self.db.execute(query, (shortened_url,))
        
        # Return the original URL if found; otherwise, return None
        if row:
            return row[0]['original_url']
        else:
            return None

    def update_url_mapping(self, original_url_id, shortened_url_id):
        # Update the URL mapping in the database
        query = 'INSERT INTO url_mappings (original_url_id, shortened_url_id) VALUES (%s, %s)'
        self.db.execute(query, (original_url_id, shortened_url_id))
```

#### API Endpoints

Create API endpoints to interact with the URL shortener.

```python
from flask import Flask, request, jsonify
app = Flask(__name__)

@app.route('/shorten', methods=['POST'])
def shorten():
    original_url = request.json['original_url']
    url_shortener = UrlShortener(db)
    shortened_data = url_shortener.shorten_url(original_url)
    return jsonify(shortened_data)

@app.route('/get-original', methods=['GET'])
def get_original():
    shortened_url = request.args.get('shortened_url')
    url_shortener = UrlShortener(db)
    original_url = url_shortener.get_original(shortened_url)
    if not original_url:
        return 'URL not found', 404
    return jsonify({'original_url': original_url})

@app.route('/update-mapping', methods=['POST'])
def update_mapping():
    original_url_id = request.json['original_url_id']
    shortened_url_id = request.json['shortened_url_id']
    url_shortener = UrlShortener(db)
    url_shortener.update_url_mapping(original_url_id, shortened_url_id)
    return jsonify({'message': 'URL mapping updated successfully'})

if __name__ == '__main__':
    app.run(debug=True)
```

### Example Use Cases

1. **Shorten a URL**:

```bash
curl -X POST \
  http://localhost:5000/shorten \
  -H 'Content-Type: application/json' \
  -d '{"original_url": "https://www.example.com"}'
```

2. **Get the original URL for a shortened URL**:

```bash
curl -X GET 'http://localhost:5000/get-original?shortened_url=http%3A%2F%2Fexample.com/12345'
```

3. **Update the URL mapping**:

```bash
curl -X POST \
  http://localhost:5000/update-mapping \
  -H 'Content-Type: application/json' \
  -d '{"original_url_id": 1, "shortened_url_id": 2}'
```

### Advantages

* Scalable and efficient storage of shortened URLs
* Unique IDs for each shortened URL to prevent collisions
* Redirections handled automatically when accessing the shortened URL
* Easy integration with APIs and web applications