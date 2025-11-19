FROM node:20-alpine

# Pour Prisma
RUN apk add --no-cache openssl

# On travaille dans /app/lots-service
WORKDIR /app/lots-service

# On copie d’abord les package.json pour profiter du cache Docker
COPY lots-service/package*.json ./

# Installer les dépendances du service (y compris jsonwebtoken qu’on vient d’ajouter)
RUN npm install

# Copier le reste du code du service (src, prisma, tsconfig, etc.)
COPY lots-service/ ./

# Copier le code partagé (qui est compilé dans dist/shared par tsc)
COPY shared/ ../shared/

# Permettre aux fichiers partagés de résoudre les dépendances Node situées dans ce service
RUN ln -s /app/lots-service/node_modules /app/node_modules

# Build TypeScript
RUN npm run build

ENV NODE_ENV=production
ENV PORT=3002

EXPOSE 3002

# Prisma generate + lancement du vrai index compilé
CMD ["sh", "-c", "npx prisma generate && node dist/lots-service/src/index.js"]
