# Stage 1 — build
FROM node:20-alpine AS build
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build

# Stage 2 — serve with nginx
FROM nginx:alpine
COPY --from=build /app/dist /usr/share/nginx/html
RUN printf "server {\n  listen 80;\n  location / {\n    try_files \$uri /index.html;\n  }\n}\n" > /etc/nginx/conf.d/spa.conf
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
