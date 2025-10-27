FROM node:20-alpine

# Install OpenSSL for Prisma
RUN apk add --no-cache openssl

WORKDIR /app

# Copy shared code
COPY shared/ ./shared/
RUN cd shared && npm install

# Copy service code
COPY sales-service/package*.json ./sales-service/
COPY sales-service/tsconfig.json ./sales-service/
COPY sales-service/prisma ./sales-service/prisma/
COPY sales-service/src ./sales-service/src/

# Install dependencies
WORKDIR /app/sales-service
RUN npm install

# Generate Prisma client
RUN npx prisma generate

# Build TypeScript
RUN npm run build

# Set production environment
ENV NODE_ENV=production
ENV PORT=3003

EXPOSE 3003

# Start service (no migrations - shared database with Python backend)
CMD ["node", "dist/index.js"]
