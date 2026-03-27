Here is a high-level design for a URL shortener system:

**Overview**

The URL shortener system will take a long URL as input, store it in a database, and return a shortened version of the URL. The system will also keep track of the number of clicks on each shortened URL.

**Components**

1. **Frontend**: Handles user requests to shorten URLs
2. **Backend**: Stores the mapping between shortened URLs and their corresponding long URLs in a database, and keeps track of the click count for each shortened URL using Redis's Pub/Sub mechanism.
3. **Database**: Stores the mapping between shortened URLs and long URLs, along with metadata such as created_at and updated_at timestamps
4. **Hash Algorithm**: Used to generate unique shortened URLs

**Design Pattern: API Gateway with Service-Oriented Architecture (SOA)**

The system will use an API gateway to handle incoming requests, which will delegate tasks to various services:

1. **URL Shortener Service**: Handles requests to shorten URLs and generates shortened URLs.
2. **Database Service**: Stores and retrieves data from the database, using caching to improve performance.

**Database Schema**

The database schema will consist of two tables:

**urls**

* id (primary key)
* original_url
* shortened_url
* click_count
* created_at
* updated_at

**clicks**

* id (primary key)
* shortened_url_id (foreign key referencing the urls table)
* click_timestamp
* ip_address

**API Endpoints**

The system will have two API endpoints:

1. **/shorten**: Accepts a long URL as input, generates a shortened URL, and returns it in JSON format.
2. **/click**: Takes a shortened URL as input, increments its click count using Redis's Pub/Sub mechanism, and updates the associated metadata.

**Hash Algorithm**

The system will use a custom hash algorithm to generate unique shortened URLs. The algorithm should be fast and efficient, and produce a consistent output for each input.

**Security Considerations**

1. **Validation**: Validate user input to prevent malicious requests.
2. **Authentication**: Authenticate users before allowing them to access the API.
3. **IP Address Logging**: Store IP addresses of users who click on shortened URLs for analytics purposes only.
4. **Data Encryption**: Encrypt data stored in the database using a secure encryption algorithm.

**Scalability**

1. **Load Balancing**: Use load balancing to distribute traffic across multiple servers.
2. **Database Sharding**: Shard the database into smaller, more manageable pieces to improve performance under heavy load.
3. **Caching**: Use caching mechanisms such as Redis to reduce the load on the database.

**Performance Optimization**

1. **Optimize Database Queries**: Optimize database queries to reduce the time it takes to retrieve data.
2. **Use Efficient Data Structures**: Use efficient data structures such as hashing tables to improve lookup times.
3. **Leverage Caching**: Leverage caching mechanisms such as Redis to reduce the load on the database.

**Monitoring and Maintenance**

1. **Monitor API Performance**: Monitor API performance using tools such as New Relic or Datadog.
2. **Track Error Rates**: Track error rates and identify areas for improvement.
3. **Perform Regular Backups**: Perform regular backups of the database to prevent data loss in case of an outage.

By following this design, we can create a scalable, secure, and high-performance URL shortener system that meets the needs of our users.