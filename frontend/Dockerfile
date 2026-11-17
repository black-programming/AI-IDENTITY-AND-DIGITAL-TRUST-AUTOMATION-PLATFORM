# ==============================================================================
# Stage 1: Build Flutter Web Release Bundle
# ==============================================================================
FROM ghcr.io/cirruslabs/flutter:stable AS builder

WORKDIR /app

# Copy dependency specifications first for layer caching
COPY pubspec.yaml pubspec.lock ./
RUN flutter pub get

# Copy frontend source code and compile web release bundle
COPY . .
RUN flutter build web --release --pwa-strategy=none --web-renderer=canvaskit

# ==============================================================================
# Stage 2: Hardened Nginx Web Server
# ==============================================================================
FROM nginx:1.27-alpine AS runtime

# Remove default nginx static assets
RUN rm -rf /usr/share/nginx/html/*

# Copy built web artifacts from builder stage
COPY --from=builder /app/build/web /usr/share/nginx/html

# Copy custom hardened nginx server block
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Configure unprivileged user permissions
RUN touch /var/run/nginx.pid && \
    chown -R nginx:nginx /var/run/nginx.pid /var/cache/nginx /usr/share/nginx/html

USER nginx

EXPOSE 8080

HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
    CMD wget -q --spider http://127.0.0.1:8080/ || exit 1

CMD ["nginx", "-g", "daemon off;"]
