# Deploying kit-registry (site/)

Pure static Astro site — `bun run build` emits fully static HTML into
`dist/`. No server, no runtime, no database. Deploy `dist/` as a static
site (same hosting options as crdt-demo).

## Build

```sh
bun install
bun run build     # static output in dist/
bun run preview   # serve dist/ locally to check
```

## Option A: Netlify

Push the repo and create a **New site → Import an existing project**;
set build command `cd site && bun run build`, publish directory
`site/dist`. Or deploy the built output directly:

```sh
npx netlify-cli deploy --dir=dist --prod
```

## Option B: Render.com

Create a **New + → Static Site**, point it at this repo, build command
`cd site && bun install && bun run build`, publish directory
`site/dist`. Render serves static sites over its CDN automatically.

## Option C: Fly.io

Fly needs an app to serve files — use their static template (Caddy or
nginx serving `dist/`):

```sh
fly launch --image caddy:2            # then mount dist/ or bake it into the image
fly deploy
```

Alternatively convert to a multi-stage Dockerfile (node/bun build stage →
`caddy:2` or `nginx:alpine` runtime stage copying `dist/`), mirroring the
crdt-demo Dockerfile pattern. Serve on `$PORT` and set the health check to
`GET /`.

## DNS

Point `kits.wyattau.dev` at the host (the site URL in
`astro.config.mjs` is the canonical placeholder).
