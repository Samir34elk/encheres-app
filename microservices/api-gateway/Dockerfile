FROM node:20-alpine

WORKDIR /app

# Copy shared code
COPY shared/ ./shared/
RUN cd shared && npm install

# Copy service code
COPY api-gateway/package*.json ./api-gateway/
COPY api-gateway/tsconfig.json ./api-gateway/
COPY api-gateway/src ./api-gateway/src/

# Install dependencies
WORKDIR /app/api-gateway
RUN npm install

# Build TypeScript
RUN npm run build

# Set production environment
ENV NODE_ENV=production
ENV PORT=3000

EXPOSE 3000

CMD ["node", "dist/index.js"]
