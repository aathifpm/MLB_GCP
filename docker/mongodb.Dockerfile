FROM mongo:latest

# Create directory for data persistence
RUN mkdir -p /data/db

# Set permissions
RUN chown -R mongodb:mongodb /data/db

# Expose the default MongoDB port
EXPOSE 27017

# Set environment variables
ENV MONGO_INITDB_DATABASE=mlb_storyteller

# Add custom MongoDB configuration
COPY docker/mongod.conf /etc/mongod.conf

# Start MongoDB with configuration
CMD ["mongod", "--config", "/etc/mongod.conf"] 