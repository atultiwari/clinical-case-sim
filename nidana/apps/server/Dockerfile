# Nidana's game server (N1.8). Build from the repository root:
#   docker build -f nidana/apps/server/Dockerfile -t nidana-server .
# Configuration comes from the environment at run time (.env.example); nothing secret is baked in.

FROM node:22-slim AS base
ENV PNPM_HOME=/pnpm PATH=/pnpm:$PATH NEXT_TELEMETRY_DISABLED=1
RUN corepack enable
WORKDIR /app
# The workspace manifests pnpm needs to read the lockfile; only the server and its packages are installed.
COPY package.json pnpm-lock.yaml pnpm-workspace.yaml ./
COPY case-library/studio/package.json case-library/studio/
COPY nidana/apps/player/package.json nidana/apps/player/
COPY nidana/tsconfig.base.json nidana/
COPY nidana/packages nidana/packages
COPY nidana/apps/server nidana/apps/server

FROM base AS build
RUN pnpm install --frozen-lockfile --filter "@nidana/server..."
RUN pnpm --filter @nidana/server build

FROM base AS run
ENV NODE_ENV=production
RUN pnpm install --frozen-lockfile --prod --filter "@nidana/server..." && rm -rf /pnpm/store
# Read at start-up: difficulty and scoring settings, and the pinned catalogue (never case bundles;
# the staging and production servers load published bundles from the database).
COPY nidana/configs nidana/configs
COPY nidana/conformance/catalogue nidana/conformance/catalogue
COPY --from=build /app/nidana/apps/server/.next nidana/apps/server/.next
RUN chown -R node:node nidana/apps/server/.next
USER node
WORKDIR /app/nidana/apps/server
EXPOSE 3100
HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
  CMD node -e "fetch('http://127.0.0.1:3100/api/health').then(r=>process.exit(r.ok?0:1)).catch(()=>process.exit(1))"
CMD ["node_modules/.bin/next", "start", "--port", "3100"]
