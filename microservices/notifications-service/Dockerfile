FROM node:20-alpine

# Pour Prisma
RUN apk add --no-cache openssl

# On travaille dans /app/notifications-service
WORKDIR /app/notifications-service

# On copie d’abord les package.json pour profiter du cache Docker
COPY notifications-service/package*.json ./

# Installer les dépendances du service
RUN npm install

# Copier le reste du code du service (src, prisma, tsconfig, etc.)
COPY notifications-service/ ./

# Copier le code partagé
COPY shared/ ../shared/

# Permettre au code partagé de résoudre les dépendances
RUN ln -s /app/notifications-service/node_modules /app/node_modules

# Build TypeScript
RUN npm run build

ENV NODE_ENV=production
ENV PORT=3005

EXPOSE 3005

# Prisma generate + lancement du vrai index compilé
CMD ["sh", "-c", "npx prisma generate && node dist/notifications-service/src/index.js"]
