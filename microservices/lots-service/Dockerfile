FROM node:20-alpine

# Install OpenSSL for Prisma
RUN apk add --no-cache openssl

WORKDIR /app

# Copy shared code
COPY shared/ ./shared/
RUN cd shared && npm install

# Copy service code
COPY lots-service/package*.json ./lots-service/
COPY lots-service/tsconfig.json ./lots-service/
COPY lots-service/prisma ./lots-service/prisma/
COPY lots-service/src ./lots-service/src/

# Install dependencies
WORKDIR /app/lots-service
RUN npm install

# Generate Prisma client
RUN npx prisma generate

# Build TypeScript
RUN npm run build && ls -laR dist/ | head -50

# Set production environment
ENV NODE_ENV=production
ENV PORT=3002

EXPOSE 3002

# Start service (no migrations - shared database with Python backend)
CMD ["node", "dist/index.js"]
