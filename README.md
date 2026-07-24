# AltSalt — backend (previous architecture)

Django backend serving the GraphQL API behind AltSalt, a community website for independent creators.

> **Status: decommissioned.** This served AltSalt in production until [DATE], when I migrated the platform to WordPress. See [Why this was retired](#why-this-was-retired). Paired with [`altsalt-frontend`](https://github.com/artemiomorales/altsalt-frontend).

## What was here

- **`catalog/`** — core domain models and API layer. [ONE LINE: what the catalog models represent]
- **`altsalt_backend/`** — project configuration, settings, and routing.
- **Heroku deployment** — `Procfile`, `runtime.txt`, and `requirements.txt` for a reproducible dyno build.

## Notable engineering

- **GraphQL schema design** — Schema handled publishing and displaying user content.

## Why this was retired

I built this as a decoupled Next.js and Django stack, ran it in production, and then migrated the platform to WordPress. The headless architecture, while flexible, caused too much overhead for the project's actual requirements.

- **Editorial workflow.** Publishing required a code deploy or a bespoke admin surface where an off-the-shelf CMS already solved it.
- **Two services, one developer.** Maintaining separate deploy pipelines, schemas, and dependency trees cost more than the decoupling returned.
- **Ecosystem evolution.** In WordPress, the stabilization of Gutenberg for creating editorial pages, as well as the Interactivity API for frontend interaction, made WordPress a better choice going forward.

The tradeoff a headless split buys — independent scaling, multi-client consumption, framework freedom — presumes constraints AltSalt didn't have.

Kept public as a record of the architecture and of the reasoning behind unwinding it.

## Stack

Python · Django · GraphQL · PostgreSQL · Heroku · AWS · Stripe · New Relic

## Author

Built and maintained solo by [Artemio Morales](https://github.com/artemiomorales). 186 commits, 2020–2025.
