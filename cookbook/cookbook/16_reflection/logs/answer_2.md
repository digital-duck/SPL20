Designing a URL Shortener System
=====================================

Overview
--------

A URL shortener is a service that takes a long, cumbersome URL and converts it into a shorter, more memorable version. This system will provide a user-friendly interface for users to submit their URLs, store them in a database, generate unique shortened URLs, and return the original long URL when clicked.

System Requirements
--------------------

*   Database to store URLs (e.g., MySQL or MongoDB)
*   Web server to host the application (e.g., Apache or Nginx)
*   Front-end framework for user interface (e.g., React or Angular)

System Design
-------------

### 1. User Interface

The front-end will be a simple web page with input fields for users to enter their long URL and an "Submit" button.

```html
<!-- index.html -->
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>URL Shortener</title>
    <link rel="stylesheet" href="styles.css">
</head>
<body>
    <h1>URL Shortener</h1>
    <input id="url-input" type="text" placeholder="Enter your URL">
    <button id="submit-btn">Submit</button>
    <p id="result"></p>

    <script src="script.js"></script>
</body>
</html>
```

### 2. Back-end

The back-end will be a Node.js application using Express.js as the web framework.

```javascript
// server.js
const express = require('express');
const app = express();
const mysql = require('mysql');

// Connect to database
const db = mysql.createConnection({
    host: 'localhost',
    user: 'username',
    password: 'password',
    database: 'url_shortener'
});

db.connect((err) => {
    if (err) {
        console.error('error connecting:', err);
        return;
    }
    console.log('connected as id ' + db.threadId);
});

// API endpoint to handle short URL generation
app.post('/shorten', (req, res) => {
    const longUrl = req.body.longUrl;

    // Generate a unique shortened URL
    const shortUrl = generateShortUrl();

    // Insert the long URL and shortened URL into database
    db.query('INSERT INTO urls SET ?', [longUrl, shortUrl], (err, results) => {
        if (err) {
            console.error(err);
            res.status(500).send({ message: 'Error generating short URL' });
        } else {
            res.send({ shortUrl: `http://localhost/${shortUrl}` });
        }
    });
});

// API endpoint to return the original long URL when clicked
app.get('/:shortUrl', (req, res) => {
    const shortUrl = req.params.shortUrl;

    // Retrieve the original long URL from database
    db.query('SELECT long_url FROM urls WHERE short_url = ?', [shortUrl], (err, results) => {
        if (err || !results[0]) {
            console.error(err);
            res.status(404).send({ message: 'Not found' });
        } else {
            const longUrl = results[0].long_url;
            res.send({ longUrl });
        }
    });
});

// API endpoint to retrieve all shortened URLs
app.get('/urls', (req, res) => {
    db.query('SELECT * FROM urls', (err, results) => {
        if (err) {
            console.error(err);
            res.status(500).send({ message: 'Error retrieving short URLs' });
        } else {
            const shortenedUrls = results.map((row) => row.short_url);
            res.send({ shortenedUrls });
        }
    });
});

app.listen(3000, () => {
    console.log('Server listening on port 3000');
});
```

### 3. Database Schema

The database schema will store the long URL and its corresponding shortened URL.

```sql
CREATE TABLE urls (
    id INT AUTO_INCREMENT PRIMARY KEY,
    long_url VARCHAR(255) NOT NULL,
    short_url VARCHAR(10) UNIQUE NOT NULL
);
```

### 4. Front-end Functionality

The front-end will send a POST request to the `/shorten` API endpoint with the long URL in the request body.

```javascript
// script.js
const urlInput = document.getElementById('url-input');
const submitBtn = document.getElementById('submit-btn');

submitBtn.addEventListener('click', () => {
    const longUrl = urlInput.value;

    if (!longUrl) {
        alert('Please enter a URL');
        return;
    }

    fetch('/shorten', {
        method: 'POST',
        headers: {