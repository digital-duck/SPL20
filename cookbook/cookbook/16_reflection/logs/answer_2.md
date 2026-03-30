Here is a design for a URL Shortener System:

**Overview**

The URL Shortener System is designed to shorten long URLs into shorter, unique URLs while preserving the original URL's content. The system will be built using Node.js and Express.js as the backend framework, with MongoDB as the NoSQL database.

**Components**

1.  **Frontend:**
    *   A web interface that allows users to input their URLs and submit them for shortening.
    *   HTML structure for the webpage, including form fields for URL input and a button to submit the URL.
    *   JavaScript code for handling user input, making requests to the backend API, and displaying the shortened URL.
2.  **Backend:**
    *   Handles HTTP requests from the frontend, stores the shortened URLs in the database, and generates unique short URLs.
    *   Uses Node.js and Express.js as the backend framework.
3.  **Database:**
    *   Stores the original and shortened URLs, along with the timestamp when each URL was created.
    *   Uses MongoDB as the NoSQL database.

**System Architecture**

The system architecture will consist of three main components:

1.  **Frontend:** The web interface that allows users to input their URLs and submit them for shortening.
2.  **Backend:** The server-side application that handles HTTP requests, stores data in the database, and generates unique short URLs.
3.  **Database:** The storage system for the original and shortened URLs.

**Database Schema**

The proposed system will use MongoDB as its NoSQL database. The following documents will be stored:

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
        unique: true,
        index: true
    },
    createdAt: {
        type: Date,
        default: Date.now
    }
});

module.exports = mongoose.model('Url', urlSchema);
```

**Backend Endpoints**

The proposed system will have the following endpoints:

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

The proposed system will use a combination of random characters and timestamps to generate unique short URLs. To achieve this, we can use the following algorithm:

```javascript
// utils.js

const crypto = require('crypto');
const shortId = require('shortid');

function generateShortUrl() {
    const timestamp = Date.now();
    const randomString = crypto.randomBytes(6).toString('hex');
    return shortId.generate() + '-' + timestamp + '-' + randomString;
}

module.exports = { generateShortUrl };
```

**Frontend Code**

The proposed system will have the following HTML structure:

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

The proposed system will have the following JavaScript code:

```javascript
// script.js

const form = document.getElementById('shorten-form');
const resultDiv = document.getElementById('result