FROM redis:latest

# Create directory for data persistence
RUN mkdir -p /data

# Set permissions
RUN chown -R redis:redis /data

# Copy custom Redis configuration
COPY docker/redis.conf /usr/local/etc/redis/redis.conf

# Expose the default Redis port
EXPOSE 6379

# Start Redis with configuration
CMD ["redis-server", "/usr/local/etc/redis/redis.conf"] 