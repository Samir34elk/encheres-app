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

# Build TypeScript (without Prisma generate - will be done at runtime)
RUN npm run build

# Set production environment
ENV NODE_ENV=production
ENV PORT=3002

EXPOSE 3002

# Generate Prisma client at startup and then start service
CMD ["sh", "-c", "npx prisma generate && node dist/index.js"]
