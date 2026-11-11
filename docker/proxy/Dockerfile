FROM node:24-alpine AS swissfy-build

WORKDIR /app

COPY --from=swissfy package*.json ./

RUN npm ci

COPY --from=swissfy index.html jsconfig.json vite.config.js ./
COPY --from=swissfy src ./src
COPY --from=swissfy public ./public
COPY --from=core . /core

RUN npm run build

FROM node:24-alpine AS docs-build

WORKDIR /app

COPY --from=docs package*.json ./

RUN npm ci

COPY --from=docs index.html jsconfig.json vite.config.js ./
COPY --from=docs src ./src
COPY --from=docs public ./public
COPY --from=core . /core

RUN npm run build

FROM caddy:2-alpine

COPY --from=swissfy-build /app/dist /srv/swissfy
COPY --from=docs-build /app/dist /srv/docs
COPY Caddyfile /etc/caddy/Caddyfile
COPY Caddyfile.edge /etc/caddy/Caddyfile.edge
