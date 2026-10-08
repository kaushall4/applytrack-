# Contributing to ApplyTrack

Thanks for your interest! ApplyTrack is a small, focused project and contributions are
welcome.

## Getting set up

See the [Quick start](README.md#quick-start) in the README. In short:

```bash
# Backend
cd backend && pip install -e ".[dev]"
# Frontend
cd frontend && npm install
```

## Before you open a PR

Please make sure the same checks CI runs pass locally:

```bash
# Backend
cd backend
ruff check .
pytest -q

# Frontend
cd frontend
npm run lint
npm run typecheck
npm run build
```

## Commit messages

This repo uses [Conventional Commits](https://www.conventionalcommits.org/). Examples:

- `feat(classifier): add cue list for assessment invitations`
- `fix(sync): handle messages without a Date header`
- `docs(readme): clarify the OAuth test-user step`
- `test(status): cover offer-after-rejection precedence`

## Guidelines

- Keep German and English first-class everywhere — classifier cues, extracted data, and
  UI strings. Use Swiss German conventions (no "ß").
- Don't log full email bodies; persist snippets only.
- Add or update tests for behaviour changes (classifier and state machine especially).
- Keep the frontend dependency surface small and the components readable.

## Reporting issues

Open a GitHub issue with steps to reproduce. Please **never** paste real email contents,
tokens, or `credentials.json` into an issue.
