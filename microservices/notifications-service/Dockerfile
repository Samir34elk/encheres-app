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

# Generate Prisma client
RUN npx prisma generate

# Build TypeScript
RUN npm run build

# Set production environment
ENV NODE_ENV=production
ENV PORT=3005

EXPOSE 3005

# Run migrations and start
CMD npx prisma migrate deploy && node dist/index.js
