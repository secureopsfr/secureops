# Multi-stage build pour le frontend Next.js (CI : target builder, prod : runner).
FROM node:20-alpine AS deps
WORKDIR /app
COPY package*.json ./
RUN npm ci

FROM node:20-alpine AS builder
WORKDIR /app
COPY --from=deps /app/node_modules ./node_modules
COPY . .

# Variables requises au build pour le prerender (Cognito). Valeurs de repli pour la CI.
ARG NEXT_PUBLIC_AWS_REGION=eu-west-3
ARG NEXT_PUBLIC_AWS_USER_POOL_ID=eu-west-3_CIPlaceholder
ARG NEXT_PUBLIC_AWS_CLIENT_ID=cipalaceholder
ARG NEXT_PUBLIC_AWS_COGNITO_DOMAIN=placeholder.auth.eu-west-3.amazoncognito.com
ENV NEXT_PUBLIC_AWS_REGION=${NEXT_PUBLIC_AWS_REGION} \
    NEXT_PUBLIC_AWS_USER_POOL_ID=${NEXT_PUBLIC_AWS_USER_POOL_ID} \
    NEXT_PUBLIC_AWS_CLIENT_ID=${NEXT_PUBLIC_AWS_CLIENT_ID} \
    NEXT_PUBLIC_AWS_COGNITO_DOMAIN=${NEXT_PUBLIC_AWS_COGNITO_DOMAIN}

ENV NEXT_TELEMETRY_DISABLED=1
RUN npm run build

FROM node:20-alpine AS runner
WORKDIR /app
ENV NODE_ENV=production
ENV NEXT_TELEMETRY_DISABLED=1
COPY --from=builder /app/.next ./.next
COPY --from=builder /app/public ./public
COPY --from=builder /app/package.json ./package.json
COPY --from=builder /app/node_modules ./node_modules
EXPOSE 3000
CMD ["npm", "run", "start"]
