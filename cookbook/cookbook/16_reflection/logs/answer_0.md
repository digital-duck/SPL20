**URL Shortener System Design**

### Overview

A URL shortener system is a service that takes a long, cumbersome URL and converts it into a shorter, more memorable version. The system should handle the following requirements:

* Store user-generated short URLs in a database
* Map short URLs to their corresponding original URLs
* Handle URL encoding and decoding
* Implement a mechanism for users to submit new URLs
* Provide an option for users to view the statistics of their short URLs

### System Architecture

The system will consist of three primary components:

1. **URL Shortener Service**
	* Handles user requests, including submitting new URLs, mapping short URLs to original URLs, and decoding URLs
	* Utilizes a database to store information about generated short URLs
2. **Database**
	* Stores all short URL mappings and statistics data
3. **Web Interface**
	* Provides a user-friendly interface for users to submit new URLs and view their statistics

### Database Schema

The database schema will consist of the following tables:

#### `short_urls`

| Field Name | Data Type | Description |
| --- | --- | --- |
| id | int | Unique identifier for each short URL |
| original_url | varchar(255) | The original URL associated with the short URL |
| shortened_url | varchar(255) | The shortened version of the original URL |

#### `statistics`

| Field Name | Data Type | Description |
| --- | --- | --- |
| id | int | Unique identifier for each statistics entry |
| user_id | int | Foreign key referencing the users table (assuming a separate users table) |
| total_clicks | int | Total number of clicks for the short URL |
| latest_click_time | datetime | Timestamp of the most recent click |

### Implementation

The implementation will be in Python using Flask as the web framework and MySQL as the database. We'll use Flask-RESTful for API requests.

**urls.py**
```python
from flask import Flask, request, jsonify
from flask_restful import Api, Resource
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
api = Api(app)

# Database configuration
app.config["SQLALCHEMY_DATABASE_URI"] = "mysql://username:password@localhost/db_name"
db = SQLAlchemy(app)
```

**models.py**
```python
from app import db

class ShortUrl(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    original_url = db.Column(db.String(255), unique=True)
    shortened_url = db.Column(db.String(255), unique=True)

class Statistics(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    total_clicks = db.Column(db.Integer)
    latest_click_time = db.Column(db.DateTime)
```

**controllers.py**
```python
from flask import request, jsonify
from models import ShortUrl, Statistics

class URLController(Resource):
    def post(self):
        data = request.get_json()
        original_url = data["original_url"]
        shortened_url = generate_shortened_url(original_url)
        short_url = ShortUrl(original_url=original_url, shortened_url=shortened_url)
        db.session.add(short_url)
        db.session.commit()
        return {"shortened_url": shortened_url}, 201

    def get(self):
        data = request.get_json()
        original_url = data["original_url"]
        short_url = ShortUrl.query.filter_by(original_url=original_url).first()
        if short_url:
            return {"shortened_url": short_url.shortened_url}
        else:
            return {"error": "Short URL not found"}, 404

class StatisticsController(Resource):
    def get(self, user_id):
        data = request.get_json()
        statistics = Statistics.query.filter_by(user_id=user_id).first()
        if statistics:
            return {"total_clicks": statistics.total_clicks, "latest_click_time": statistics.latest_click_time}
        else:
            return {"error": "Statistics not found"}, 404
```

**generate_shortened_url.py**
```python
import hashlib

def generate_shortened_url(original_url):
    hashed_url = hashlib.sha256(original_url.encode()).hexdigest()
    shortened_url = f"{hashed_url[:6]}"
    return shortened_url
```
This design provides a scalable and efficient solution for the URL shortener system, allowing users to submit new URLs, view their statistics, and handle URL encoding and decoding.

**Example Use Cases:**

* Submitting a new URL:
```bash
curl -X POST \
  http://localhost:5000/shorten \
  -H 'Content-Type: application/json' \
  -d '{"original_url": "https://www.example.com/very-long-url"}'
```
* Viewing the shortened URL:
```bash
curl -X GET \
  http://localhost:500