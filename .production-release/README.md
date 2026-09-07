# Production Release Identity

This directory defines the release identity contract used by production
deployment and recovery.

## Required identity

Every production release must have:

- `RELEASE_ID`
- `IMAGE_TAG`

The values must identify one exact release.

Recommended convention:

```text
RELEASE_ID=sha-<immutable-commit-identifier>
IMAGE_TAG=release-<same-immutable-identifier>
```

## Forbidden identities

Production deployment must never use:

- latest
- dev
- test
- current

as the release identity.

## Recovery

Before a production deployment, the recovery authority records:

- previous RELEASE_ID
- previous image reference
- previous Compose configuration identity
- timestamp

Rollback restores the previously recorded artifact.

Rollback must fail closed when the previous artifact cannot be resolved.

## Database policy

Container/application rollback and database schema rollback are separate operations.

The recovery authority MUST NOT automatically execute:

- alembic downgrade

A database rollback requires an independent, explicitly approved procedure.

## Secrets

This directory must never contain:

- passwords
- API keys
- JWT secrets
- access tokens
- private keys
- .env contents

Only release metadata belongs here.
