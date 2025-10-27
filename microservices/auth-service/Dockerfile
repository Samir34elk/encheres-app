FROM node:20-alpine

# Install OpenSSL for Prisma
RUN apk add --no-cache openssl

WORKDIR /app

# Copy shared code
COPY shared/ ./shared/
RUN cd shared && npm install

# Copy service code
COPY auth-service/package*.json ./auth-service/
COPY auth-service/tsconfig.json ./auth-service/
COPY auth-service/prisma ./auth-service/prisma/
COPY auth-service/src ./auth-service/src/

# Install dependencies
WORKDIR /app/auth-service
RUN npm install

# Build TypeScript (without Prisma generate - will be done at runtime)
RUN npm run build

# Set production environment
ENV NODE_ENV=production
ENV PORT=3001

EXPOSE 3001

# Generate Prisma client at startup and then start service
CMD ["sh", "-c", "npx prisma generate && node dist/index.js"]
