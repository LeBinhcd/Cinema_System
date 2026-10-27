# MySQL migration readiness

## Current decision

MySQL is the target production database. SQLite remains enabled for tests and
rollback until the compatibility gate is passed. Do **not** change
`DB_ENGINE=mysql` in a production `.env` yet.

## Current blockers

1. Application models use SQLite `?` placeholders; MySQL Connector uses `%s`.
2. Some transactions use `BEGIN IMMEDIATE`, which is SQLite-only.
3. SQLite migrations use `PRAGMA`, `sqlite_master`, and `ALTER TABLE` behavior
   that cannot run against MySQL.
4. The current MySQL schema does not yet match the live SQLite contract. The
   application requires `users.email`, `users.user_code`, `tickets.booking_code`,
   `tickets.price`, `tickets.checked_in_at`, `payments.booking_id`,
   `payments.payment_method`, `counter_sales`, `refund_requests`, `saved_cards`,
   and the expanded AI draft columns.
5. SQLite and MySQL return rows differently; the adapter must expose mapping-like
   rows consistently.
6. SQLite and MySQL use different integrity-error classes and transaction APIs.

## Safe migration phases

### Phase A — schema contract

Create a MySQL schema that matches the **live SQLite schema and application
queries**, not only the older design document. Use InnoDB, `utf8mb4`, foreign
keys, unique constraints, and indexes. Do not use cascade deletes for tickets,
payments, or refund records.

### Phase B — database adapter

Add one adapter responsible for:

- placeholder conversion;
- transaction begin/commit/rollback;
- mapping rows to dictionary-like objects;
- `lastrowid` access;
- backend-specific integrity errors.

Services and models must stop branching on SQLite/MySQL details.

### Phase C — migration and verification

Export SQLite data to a separate MySQL database, then compare row counts and
important business keys for users, movies, rooms, seats, screenings, tickets,
payments, AI drafts, refund requests, and counter sales. Keep the SQLite file
untouched as rollback backup.

### Phase D — controlled cutover

Set only the local `.env` to `DB_ENGINE=mysql` after the adapter, schema, and
integration tests pass. Run login, booking, seat hold, payment, ticket,
refund, Admin, Staff, chatbot RAG, AI description, and revenue tests before
changing the launcher default.

## Required MySQL environment

```env
DB_ENGINE=mysql
DB_HOST=127.0.0.1
DB_PORT=3306
DB_NAME=cinema_system
DB_USER=cinema_app
DB_PASSWORD=change-me
```

Never commit the real password. The existing `.env.example` remains safe to
share and SQLite remains the default until cutover approval.

## Rollback

Rollback is simply restoring:

```env
DB_ENGINE=sqlite
SQLITE_PATH=/absolute/path/to/cinema.db
```

Do not delete `cinema.db` or its verified backup until MySQL has passed a full
business-flow acceptance test.