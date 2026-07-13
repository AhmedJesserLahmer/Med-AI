# --- deps: rarely changes, cached as long as the lockfile is unchanged ---
FROM node:20-alpine AS deps

WORKDIR /app

COPY package.json package-lock.json ./
RUN npm ci

# --- builder: app source changes on every commit --------------------------
FROM node:20-alpine AS builder

WORKDIR /app

# NEXT_PUBLIC_* vars are inlined into the client bundle at build time,
# so this must be a build ARG, not a runtime environment: entry in compose.
ARG NEXT_PUBLIC_API_URL
ENV NEXT_PUBLIC_API_URL=$NEXT_PUBLIC_API_URL

COPY --from=deps /app/node_modules ./node_modules
COPY . .
RUN npm run build

# --- runner: minimal production image (Next.js standalone output) --------
FROM node:20-alpine AS runner

WORKDIR /app

ENV NODE_ENV=production
ENV PORT=3000

COPY --from=builder /app/public ./public
COPY --from=builder /app/.next/standalone ./
COPY --from=builder /app/.next/static ./.next/static

EXPOSE 3000

CMD ["node", "server.js"]
