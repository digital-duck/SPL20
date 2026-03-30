Here's a design for a simple URL shortener system using Node.js, Express.js, and MongoDB.

**System Overview**

The system will consist of the following components:

*   **Frontend:** A web interface that allows users to input their URLs and submit them for shortening.
*     **Backend:** Handles HTTP requests from the frontend, stores the shortened URLs in a database, and generates unique short URLs.
*   **Database:** Stores the original and shortened URLs, along with the timestamp when each URL was created.

**Database Schema**

The MongoDB database will store the following documents:

```javascript
// urlSchema.js

const mongoose = require('mongoose');

const urlSchema = new mongoose.Schema({
    originalUrl: {
        type: String,
        required: true
    },
    shortenedUrl: {
        type: String,
        required: true
    },
    createdAt: {
        type: Date,
        default: Date.now
    }
});

module.exports = mongoose.model('Url', urlSchema);
```

**Backend Endpoints**

The Express.js backend will have the following endpoints:

```javascript
// routes.js

const express = require('express');
const router = express.Router();
const Url = require('./urlSchema');

router.post('/shorten', async (req, res) => {
    try {
        const originalUrl = req.body.originalUrl;
        const shortenedUrl = generateShortUrl();

        // Store the URL in the database
        await Url.create({
            originalUrl,
            shortenedUrl
        });

        return res.json({ shortUrl: shortenedUrl });
    } catch (err) {
        console.error(err);
        res.status(500).json({ message: 'Error shortening URL' });
    }
});

router.get('/:shortUrl', async (req, res) => {
    try {
        const shortUrl = req.params.shortUrl;

        // Find the original URL in the database
        const urlDoc = await Url.findOne({ shortenedUrl: shortUrl });

        if (!urlDoc) {
            return res.status(404).json({ message: 'URL not found' });
        }

        return res.json({ originalUrl: urlDoc.originalUrl });
    } catch (err) {
        console.error(err);
        res.status(500).json({ message: 'Error retrieving URL' });
    }
});

module.exports = router;
```

**Short URL Generation**

The shortened URL is generated using a combination of random characters and timestamps. You can use a library like `shortid` to generate short IDs.

```javascript
// utils.js

const shortId = require('shortid');

function generateShortUrl() {
    return shortId.generate();
}

module.exports = { generateShortUrl };
```

**Frontend Code**

Create an HTML file (`index.html`) with the following code:

```html
<!-- index.html -->

<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>URL Shortener</title>
    <script src="/static/script.js"></script>
</head>
<body>
    <form id="shorten-form">
        <input type="text" id="original-url" placeholder="Enter URL">
        <button type="submit">Shorten URL</button>
    </form>

    <div id="result">
        <!-- Shortened URL will be displayed here -->
    </div>
</body>
</html>
```

Create a JavaScript file (`script.js`) with the following code:

```javascript
// script.js

const form = document.getElementById('shorten-form');
const resultDiv = document.getElementById('result');

form.addEventListener('submit', async (e) => {
    e.preventDefault();

    const originalUrl = document.getElementById('original-url').value;

    try {
        // Send a POST request to the backend endpoint
        const response = await fetch('/shorten', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ originalUrl })
        });

        const data = await response.json();

        resultDiv.textContent = `Shortened URL: ${data.shortUrl}`;
    } catch (err) {
        console.error(err);
        resultDiv.textContent = 'Error shortening URL';
    }
});
```

**Running the System**

1.  Create a new directory for your project and initialize it with Node.js using `npm init`.
2.  Install Express.js, MongoDB, and the required dependencies using `npm install express mongoose`.
3.  Create a new file called `app.js` and add the following code:

```javascript
// app.js

const express = require('express');
const mongoose = require('mongoose');

const app = express();
const port = 3000;

app.use(express.json());

mongoose.connect('mongodb://localhost/