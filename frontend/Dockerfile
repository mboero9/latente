FROM node:24-alpine AS build
WORKDIR /app
COPY package*.json ./
RUN npm ci --no-audit --no-fund
COPY . .
ARG VITE_API_BASE_URL=""
ENV VITE_API_BASE_URL=$VITE_API_BASE_URL
RUN npm run build

# Inicializador del volumen compartido: Nginx sirve estos archivos sin Node en producción.
FROM alpine:3.22
COPY --from=build /app/dist /dist
CMD ["sh", "-c", "cp -a /dist/. /output/"]
