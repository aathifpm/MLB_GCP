FROM mongo:latest

# Create directories for data and logs
RUN mkdir -p /data/db /var/log/mongodb

# Set permissions
RUN chown -R mongodb:mongodb /data/db /var/log/mongodb

# Expose the default MongoDB port
EXPOSE 27017

# Set environment variables
ENV MONGO_INITDB_DATABASE=mlb_storyteller

# Add custom MongoDB configuration
COPY docker/mongod.conf /etc/mongod.conf

# Start MongoDB with configuration
CMD ["mongod", "--config", "/etc/mongod.conf"] 