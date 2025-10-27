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

# Build TypeScript (without Prisma generate - will be done at runtime)
RUN npm run build

# Set production environment
ENV NODE_ENV=production
ENV PORT=3003

EXPOSE 3003

# Generate Prisma client at startup and then start service
CMD ["sh", "-c", "npx prisma generate && node dist/index.js"]
