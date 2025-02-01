FROM redis:latest

# Create directories for data and logs
RUN mkdir -p /data /var/log/redis

# Set permissions
RUN chown -R redis:redis /data /var/log/redis

# Copy custom Redis configuration
COPY docker/redis.conf /usr/local/etc/redis/redis.conf

# Expose the default Redis port
EXPOSE 6379

# Start Redis with configuration
CMD ["redis-server", "/usr/local/etc/redis/redis.conf"] 