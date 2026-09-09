# Contributing to apowerb-docs

This repository is the source of [docs.apowerb.com](https://docs.apowerb.com). It is a
[Mintlify](https://mintlify.com) project: pages are MDX, navigation and theming live in
`docs.json`.

By contributing, you agree that your contribution is licensed under the
[MIT License](./LICENSE), like the rest of the apowerb stack. You keep the copyright on
what you write.

The published guide — how a change is proposed across the whole project — is at
[docs.apowerb.com/contributing/contributing](https://docs.apowerb.com/contributing/contributing).
What follows is specific to *this* repository.

## Preview your change

```bash
npm i -g mint
mint dev
```

Serves on <http://localhost:3000> and reloads on save.

## Run what CI runs

`.github/workflows/ci.yml` runs these on every pull request. Running them before you
push saves a round trip:

```bash
mint validate       # strict build
mint broken-links
```

`mint validate` is the one that catches structural MDX errors — an unbalanced
`<Steps>` tag, a malformed frontmatter block. It also catches something
`broken-links` cannot: a `docs.json` navigation entry pointing at a file that does not
exist. There is no link to follow, so the link checker sees nothing, and the page
answers 404 on the live site. Four entries survived that way before `validate` was
added to CI.

## Two things that will surprise you

**A merge does not publish.** Mintlify does not build on push: the live site changes
only when someone triggers *Manual update* from the Mintlify dashboard. Merging your PR
is not the last step — see
[the release process](https://docs.apowerb.com/contributing/releases).

**`api-reference/openapi.json` is generated — do not hand-edit it.** It is produced by
importing the FastAPI app from an open-source build of the core, via
`./scripts/sync-openapi.sh`. Nothing breaks when it goes stale: the JSON stays valid and
Mintlify keeps serving it, so the reference drifts silently. Diff the `paths` to check
it, never `info.version`.

## Commits and branches

Branch as `<type>/<slug>` — `docs/kubernetes-step-by-step`, `fix/docs-live-frontmatter`,
`ci/check-docs-live`.

Commit messages follow [Conventional Commits](https://www.conventionalcommits.org/).
The types in use here are `docs`, `fix`, `ci` and `style`; append `!` for a breaking
change. Write the subject in the lowercase, no-trailing-period style of the history, and
describe what the documentation now says rather than the edit you made:

```
docs(kubernetes): chart 0.4.2, close port 80, and the superadmin without a password
fix(ci): a witness that proves something
```

## Security

Do not report a vulnerability through an issue or a pull request. Use
[GitHub Security Advisories](https://github.com/apowerb/apowerb/security/advisories/new)
on the core repository.
