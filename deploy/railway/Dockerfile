FROM node:24-alpine AS build
WORKDIR /frontend
COPY frontend/package*.json ./
RUN npm ci --no-audit --no-fund
COPY frontend/ ./
# La copia servida por Nginx usa su propio /api. Cloudflare se compila por separado.
RUN npm run build

FROM nginx:1.28-alpine
COPY --from=build /frontend/dist /usr/share/nginx/html
COPY deploy/railway/nginx.conf.template /etc/nginx/latente.conf.template
COPY deploy/railway/start-nginx.sh /usr/local/bin/start-latente
EXPOSE 8080
ENTRYPOINT ["sh", "/usr/local/bin/start-latente"]
