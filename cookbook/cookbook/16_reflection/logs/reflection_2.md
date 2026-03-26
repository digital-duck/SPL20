import uuid
from flask import Flask, request, jsonify

app = Flask(__name__)

db = {
    'urls': [],
    'url_mappings': []
}

class UrlShortener:
    def __init__(self):
        self.db = db

    def shorten_url(self, original_url):
        # Generate a unique ID for the shortened URL
        id = str(uuid.uuid4())
        
        # Store the shortened URL in the database
        query = 'INSERT INTO urls (original_url, shortened_url) VALUES (%s, %s)'
        self.db['urls'].append((id, f'http://example.com/{id}'))
        self.db.execute(query, (original_url, f'http://example.com/{id}'))
        
        # Return the shortened URL and its ID
        return {'shortened_url': f'http://example.com/{id}', 'id': id}

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
        self.db['url_mappings'].append((original_url_id, shortened_url_id))

@app.route('/shorten', methods=['POST'])
def shorten():
    original_url = request.json['original_url']
    url_shortener = UrlShortener()
    shortened_data = url_shortener.shorten_url(original_url)
    return jsonify(shortened_data)

@app.route('/get-original', methods=['GET'])
def get_original():
    shortened_url = request.args.get('shortened_url')
    url_shortener = UrlShortener()
    original_url = url_shortener.get_original(shortened_url)
    if not original_url:
        return 'URL not found', 404
    return jsonify({'original_url': original_url})

@app.route('/update-mapping', methods=['POST'])
def update_mapping():
    original_url_id = request.json['original_url_id']
    shortened_url_id = request.json['shortened_url_id']
    url_shortener = UrlShortener()
    url_shortener.update_url_mapping(original_url_id, shortened_url_id)
    return jsonify({'message': 'URL mapping updated successfully'})

if __name__ == '__main__':
    app.run(debug=True)