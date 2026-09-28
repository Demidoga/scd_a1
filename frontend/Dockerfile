# syntax=docker/dockerfile:1
#
# Multi-stage build: Node only exists in the build stage. The runtime image
# contains nothing but the built static assets and nginx (no Node.js,
# node_modules, or TypeScript source) — docs/architecture/frontend.md §5.

FROM node:22-alpine AS builder

WORKDIR /app

# Dependency-first COPY order: `npm ci` only reruns when the lockfile changes.
COPY package.json package-lock.json ./
RUN npm ci

COPY . .
RUN npm run build

FROM nginx:1.27-alpine AS runtime

RUN addgroup -S app && adduser -S app -G app

COPY --from=builder /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf

# nginx needs write access to these paths even when unprivileged.
RUN rm -f /etc/nginx/conf.d/*.conf.default 2>/dev/null; \
    touch /var/run/nginx.pid && \
    chown -R app:app /usr/share/nginx/html /var/cache/nginx /var/run/nginx.pid /etc/nginx/conf.d

USER app

EXPOSE 8080

HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD wget -q -O /dev/null http://localhost:8080/ || exit 1

CMD ["nginx", "-g", "daemon off;"]
