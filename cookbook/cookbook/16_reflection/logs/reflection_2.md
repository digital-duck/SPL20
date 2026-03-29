Here's the complete code for designing a URL shortener system:

**Front-end**

Create a new file named `index.html` and add the following code:
```html
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

Create a new file named `styles.css` and add the following code:
```css
body {
    font-family: Arial, sans-serif;
}

#url-input {
    width: 50%;
    height: 30px;
    padding: 10px;
    margin-bottom: 20px;
    border: 1px solid #ccc;
}

#submit-btn {
    width: 20%;
    height: 40px;
    background-color: #4CAF50;
    color: #fff;
    border: none;
    cursor: pointer;
}

#result {
    font-size: 18px;
}
```

Create a new file named `script.js` and add the following code:
```javascript
const urlInput = document.getElementById('url-input');
const submitBtn = document.getElementById('submit-btn');

submitBtn.addEventListener('click', async () => {
    const longUrl = urlInput.value;

    if (!longUrl) {
        alert('Please enter a URL');
        return;
    }

    try {
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
            alert('Error generating short URL');
        }
    } catch (error) {
        console.error(error);
    }
});
```

**Back-end**

Create a new file named `server.js` and add the following code:
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

**Database Schema**

Create a new file named `