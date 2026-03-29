To design an efficient URL shortener system, consider the following key components and their respective implementation details:

### 1. Front-end Functionality

The front-end should provide a simple, user-friendly interface for users to submit URLs. This can be achieved using HTML, CSS, and JavaScript.

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

```javascript
// script.js
const urlInput = document.getElementById('url-input');
const submitBtn = document.getElementById('submit-btn');

submitBtn.addEventListener('click', async () => {
    const longUrl = urlInput.value;

    if (!longUrl) {
        alert('Please enter a URL');
        return;
    }

    try {
        // Validate the input URL
        if (!/^(https?:\/\/)?[\w.-]+(?:\.[\w\.-]+)+$/.test(longUrl)) {
            throw new Error('Invalid URL format');
        }

        const response = await fetch('/shorten', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ longUrl })
        });

        if (response.ok) {
            const data = await response.json();
            console.log(data.shortUrl);
            urlInput.value = '';
        } else {
            throw new Error('Error generating short URL');
        }
    } catch (error) {
        console.error(error);
        alert(error.message);
    }
});
```

### 2. Back-end Functionality

The back-end should be implemented using a programming language such as Node.js and Express.js.

```javascript
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
        console.error(err);
        return;
    }
    console.log('connected as id ' + db.threadId);
});

// API endpoint to handle short URL generation
app.post('/shorten', (req, res) => {
    const longUrl = req.body.longUrl;

    try {
        // Validate the input URL
        if (!/^(https?:\/\/)?[\w.-]+(?:\.[\w\.-]+)+$/.test(longUrl)) {
            throw new Error('Invalid URL format');
        }

        // Generate a unique shortened URL
        const shortUrl = generateShortUrl();

        // Insert the long URL and shortened URL into database
        db.query('INSERT INTO urls SET ?', [longUrl, shortUrl], (err, results) => {
            if (err) {
                throw new Error(`Error inserting data into database: ${err}`);
            } else {
                res.send({ shortUrl: `http://localhost/${shortUrl}` });
            }
        });
    } catch (error) {
        console.error(error);
        res.status(500).send({ message: error.message });
    }
});

// API endpoint to return the original long URL when clicked
app.get('/:shortUrl', (req, res) => {
    const shortUrl = req.params.shortUrl;

    try {
        // Retrieve the original long URL from database
        db.query('SELECT long_url FROM urls WHERE short_url = ?', [shortUrl], (err, results) => {
            if (err || !results[0]) {
                throw new Error(`Error retrieving data from database: ${err}`);
            } else {
                const longUrl = results[0].long_url;
                res.send({ longUrl });
            }
        });
    } catch (error) {
        console.error(error);
        res.status(404).send({ message: 'Not found' });
    }
});

app.listen(3000, () => {
    console.log('Server listening on port 3000');
});
```

### 3. Database Schema

The database schema should store the long URL and its corresponding shortened URL.

```sql
CREATE TABLE urls (
    id INT AUTO_INCREMENT PRIMARY KEY,
    long_url VARCHAR(255) NOT NULL,
    short_url VARCHAR(10) UNIQUE NOT NULL
);
```

### 4.