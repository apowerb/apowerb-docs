# apowerb-docs

Source of [doc.apowerb.com](https://doc.apowerb.com) — the technical documentation for
the apowerb open-core stack.

Built with [Mintlify](https://mintlify.com). Pages are MDX; navigation and theming live
in `docs.json`.

## Run it locally

```bash
npm i -g mint
mint dev
```

Serves on <http://localhost:3000> and reloads on save.

## Layout

```
docs.json              navigation, theme, tabs
index.mdx              introduction
quickstart.mdx         Docker Compose path
installation.mdx       PyPI and from-source paths
configuration.mdx      every environment variable
concepts/              architecture, editions, agents, orchestration, sessions, tools
guides/                RAG, Text-to-SQL, webhooks, integrations, streaming, scheduler…
self-hosting/          Docker, database, secrets, production checks
ecosystem/             apowerb-ui, th2rag, th2etl, th2pulse
contributing/          contributing, development setup, release process
api-reference/         narrative pages + openapi.json (generated)
logo/                  placeholder wordmark and favicon
```

## The API reference is generated

`api-reference/openapi.json` is **not** hand-written. It is the schema a running
instance publishes at `/openapi.json`, with the commercial-only routes removed
(`/api/billing/*`, `/api/usage/*`, `/api/auth/mfa/*`, prospection and campaigns) so the
reference matches the open-source edition.

Refresh it with:

```bash
./scripts/sync-openapi.sh https://your-instance.example.com
```

## Known gaps

- **The logo is a placeholder.** `logo/*.svg` is a plain wordmark built from the
  product's blue (`#0A1E72`). Replace it with the real brand asset when there is one.
- **The commercial-route filter is a list, not a build.** The honest version generates
  the schema from an open-source build of the core rather than filtering a full
  instance. The filter is in `scripts/sync-openapi.sh`.
- **No screenshots yet.** Guides that describe UI flows ("connect Google from the
  interface") would read better with images.
- **No search analytics, no versioning.** Both are Mintlify features to enable once the
  site is live.

## Conventions

Everything here is written in English, like the rest of the codebase.
