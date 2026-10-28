# N3 performance analysis — chat memory path

Source files read:
- app/modules/agent_platform/presentation/chat_router.py (request handler + `_schedule_summary`)
- app/modules/agent_platform/infrastructure/persistence/ai_conversation_repository.py
- app/modules/agent_platform/application/memory/summarizer.py

## 1. Exact DB write sequence per chat turn

Critical path (request session, in handler order):
1. `get_or_create(session_id, …)` — SELECT conversation by session_id; on miss INSERT + commit.
2. `get_messages(conversation_id, limit=20)` — SELECT (read).
3. `get_summary(conversation_id)` — SELECT (read).
4. LLM orchestration (no DB).
5. `append_message(role="user", content=text)` — INSERT message + SELECT conversation to bump `updated_at` + commit.
6. `append_message(role="assistant", content=result.text)` — INSERT message + SELECT conversation + commit.
7. `_schedule_summary(conversation_id)` — `loop.create_task` only (no DB in request path).

Background (detached task, own session):
8. `_summarize_in_background` → `count_messages` (SELECT), and if > THRESHOLD: `summarize_conversation`:
   - `count_messages`, `get_summary`, `get_messages(limit=120)`, LLM generate, `replace_summary` (DELETE summary rows + INSERT summary + SELECT conversation + commit).

So critical path = 3 commits (get_or_create + 2 appends), each `commit()` on the request session. Background path = 1 commit (`replace_summary`) plus reads.

## 2. Critical-path vs background writes

Critical (blocks reply assembly/return): steps 1, 5, 6 — three separate commits, each a round-trip to Postgres and a row lock on `ai_conversations.updated_at`. Step 5 and 6 also each re-SELECT the conversation row (N+1-ish) just to bump `updated_at`.

Background (fire-and-forget): step 8 — runs after reply is assembled; uses `async_session_factory()` and does not block the HTTP response. It can still contend on the same `ai_conversations` row and on the connection pool.

## 3. Root cause of serialization

Each `commit()` is an independent transaction → 3 BEGIN/COMMIT per turn, plus per-statement round trips. Under 20 concurrent requests these commits serialize on the DB (row-level locks on the conversation row + connection pool). Measured: 2674 ms for chat+DB vs 385 ms without DB; ~2.3 s is pure persistence overhead. `get_or_create`'s commit also happens even on the read path (existing conversation) — no, it only commits on insert; but the two appends each commit separately.

## 4. Concrete minimal change (proposed, not applied)

Option A (smallest, highest impact): merge the two appends into ONE commit.
- Add `append_messages_batch(conversation_id, messages: list[(role,content)])` to `AiConversationRepository` that adds both `AiMessageModel` rows + bumps `updated_at` once + single `commit()`.
- Chat router calls it once instead of two `append_message` calls.
- Effect: 3 commits/turn → 2 commits/turn (get_or_create + batched append). Removes one full transaction + one conversation re-SELECT.

Option B: make `append_message` accept `flush`/`commit` flags and defer commit; caller commits once after both appends. Smaller diff but leaks transaction control into router; less clean.

Option C (background): in `_summarize_in_background`, the `replace_summary` commit is already one transaction; reduce read count by reusing the `count_messages` result and skipping `get_summary` re-read when `count <= THRESHOLD` (already done early-return). Minor.

Option D (pool tuning): increase SQLAlchemy pool size / add `pool_pre_ping`; helps concurrency but doesn't fix per-turn commit count. Complementary, not primary.

Recommended: Option A for critical path, plus Option D for pool. Background summarizer stays detached; optionally gate it with a longer threshold or debounce per conversation to reduce LLM cost, but that's a separate concern.

## 5. Estimated impact

- Critical-path commits: 3 → 2 per turn (~33% fewer transactions).
- Conversation-row SELECTs: 2 (one per append) → 1.
- Expected latency: from 2674 ms toward ~1800–2000 ms for the DB portion if commit overhead dominates; if pool contention dominates, Option D needed too. Real gain requires measuring commit vs pool wait time (not captured in current probes).

## 6. Risks

- Batching must preserve "best-effort: never break caller" semantics — wrap in try/except as today.
- If one of the two messages fails to persist, partial state possible; today each append is its own transaction so a failure leaves only the user message. Batched = all-or-nothing for the pair. Acceptable (assistant reply without user msg is worse than losing both).
- `updated_at` bump once is fine; conversation freshness still tracked.
- Background summarizer holds its own session and a per-conversation lock; if it runs concurrently with a critical-path append on the same conversation row, Postgres serializes via row lock — no deadlock risk since lock order is consistent (conversation row then message insert), but adds wait time. Consider skipping summarization when a turn is in flight.
- No schema/migration change; backward compatible.
- Must keep existing tests passing: `tests/unit/test_orchestrator_collected_calls.py`, `test_conversation_repository.py` (Postgres contract probe) assert per-call semantics; batched API needs new tests + keeping old `append_message` for backward compat (or deprecate).
