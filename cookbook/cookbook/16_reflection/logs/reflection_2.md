Based on the provided design for a URL shortener system, here's an implementation in Node.js and Express.js with MongoDB as the NoSQL database.

**Project Structure:**

```bash
url-shortener/
app.js
config/
database.js
routes.js
utils.js
models/
Url.js
public/
script.js
index.html
package.json
```

**Database Configuration:**

Create a `database.js` file in the `config/` directory to configure MongoDB:

```javascript
// config/database.js

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

const Url = mongoose.model('Url', urlSchema);

mongoose.connect('mongodb://localhost/url-shortener', {
    useNewUrlParser: true,
    useUnifiedTopology: true
});

module.exports = Url;
```

**Backend Routes:**

Create a `routes.js` file in the `config/` directory to define backend routes:

```javascript
// config/routes.js

const express = require('express');
const router = express.Router();
const Url = require('./database');

router.post('/shorten', async (req, res) => {
    try {
        const originalUrl = req.body.originalUrl;
        const shortenedUrl = generateShortUrl();

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

**Short URL Generation:**

Create a `utils.js` file in the root directory to generate unique short URLs:

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

**Frontend Code:**

Create an `index.html` file in the `public/` directory to display a form and the shortened URL:

```html
<!-- public/index.html -->

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

**Frontend JavaScript Code:**

Create a `script.js` file in the `static/` directory to handle form submission and display the shortened URL:

```javascript
// static/script.js

const form = document.getElementById('shorten-form');
const resultDiv = document.getElementById('result');

form.addEventListener('submit', async (e) => {
    e.preventDefault();

    const originalUrl = document.getElementById('original-url').value;
    const shortUrl = generateShortUrl();
    fetch('/shorten', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ originalUrl })
    })
        .then((response) => response.json())
        .then((data) => {
            resultDiv.innerHTML += `<p>Shortened URL: ${data.shortUrl}</p>`;
        })
        .catch((error) => console.error(error));
});

// Function to generate short URL
function generateShortUrl() {
    const { generateShortUrl } = require('./utils');
    return generateShortUrl();
}
```

**Start the Server:**

Start the server by running `node app.js` in your terminal:

```bash
