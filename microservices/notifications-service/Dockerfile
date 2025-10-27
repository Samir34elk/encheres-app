FROM node:20-alpine

# Install OpenSSL for Prisma
RUN apk add --no-cache openssl

WORKDIR /app

# Copy shared code
COPY shared/ ./shared/
RUN cd shared && npm install

# Copy service code
COPY notifications-service/package*.json ./notifications-service/
COPY notifications-service/tsconfig.json ./notifications-service/
COPY notifications-service/prisma ./notifications-service/prisma/
COPY notifications-service/src ./notifications-service/src/

# Install dependencies
WORKDIR /app/notifications-service
RUN npm install

# Build TypeScript (without Prisma generate - will be done at runtime)
RUN npm run build

# Set production environment
ENV NODE_ENV=production
ENV PORT=3005

EXPOSE 3005

# Generate Prisma client at startup and then start service
CMD ["sh", "-c", "npx prisma generate && node dist/index.js"]
