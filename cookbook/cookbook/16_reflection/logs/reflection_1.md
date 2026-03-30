const express = require('express');
const mongoose = require('mongoose');

const app = express();
const port = 3000;

mongoose.connect("mongodb://localhost/shorturl", { useNewUrlParser: true, useUnifiedTopology: true });

app.use(express.json());

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

app.post('/shorten', async (req, res) => {
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

app.get('/:shortUrl', async (req, res) => {
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

function generateShortUrl() {
    const timestamp = Date.now();
    const randomString = crypto.randomBytes(6).toString('hex');
    return shortId.generate() + '-' + timestamp + '-' + randomString;
}

app.listen(port, () => {
    console.log(`Server started on port ${port}`);
});
