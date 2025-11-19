FROM node:20-alpine

# Dépendances pour Puppeteer/Prisma
RUN apk add --no-cache \
    chromium \
    nss \
    freetype \
    harfbuzz \
    ca-certificates \
    ttf-freefont \
    openssl

# Tell Puppeteer to use installed Chromium
ENV PUPPETEER_EXECUTABLE_PATH=/usr/bin/chromium-browser
ENV PUPPETEER_SKIP_CHROMIUM_DOWNLOAD=true

# On travaille dans /app/scraper-service
WORKDIR /app/scraper-service

# Cache npm
COPY scraper-service/package*.json ./
RUN npm install

# Copier le reste du code
COPY scraper-service/ ./

# Copier le code partagé
COPY shared/ ../shared/

# Permettre aux modules partagés de trouver les dépendances
RUN ln -s /app/scraper-service/node_modules /app/node_modules

# Build TypeScript
RUN npm run build

ENV NODE_ENV=production
ENV PORT=3004

EXPOSE 3004

CMD ["node", "dist/scraper-service/src/index.js"]
