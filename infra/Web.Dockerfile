FROM node:24-bookworm-slim AS build
WORKDIR /app
COPY web/package.json web/package-lock.json ./
RUN npm ci
COPY web/app ./app
COPY web/components ./components
COPY web/lib ./lib
COPY web/next.config.ts web/next-env.d.ts web/tsconfig.json ./
ENV FNS_API_ORIGIN=http://api:8000
RUN npm run build
ENV NODE_ENV=production
EXPOSE 3000
USER node
CMD ["node", "node_modules/next/dist/bin/next", "start", "--hostname", "0.0.0.0"]
