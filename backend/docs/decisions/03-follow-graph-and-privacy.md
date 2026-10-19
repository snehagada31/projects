# Decision Record 03: Follow Graph and Privacy

**Decision:**
Desired-state idempotent follow operations backed by a compound primary key `(follower_id, following_id)`, a database CHECK constraint preventing self-follow, and immediate public follow transitions.

**Options considered:**
1. *Toggle follow endpoint (`POST /follow`)*: A toggle flips state on each call. If network latency triggers a mobile retry, the user unintentionally unfollows.
2. *Desired-state endpoints (`PUT /follow` and `DELETE /follow` - Chosen)*:
   - `PUT /users/{id}/follow`: "Make me following X".
   - `DELETE /users/{id}/follow`: "Make me not following X".
   - Idempotent: repeating the request 50 times produces the exact same outcome.
3. *Application-level self-follow check alone*: Prone to race conditions if two threads execute without database-level protection.
4. *Database CHECK constraint (Chosen)*: `CONSTRAINT no_self_follow CHECK (follower_id <> following_id)`. Impossible to bypass even with raw SQL.

**State Machine:**

```
                  PUT /users/{id}/follow (Actor)
      [NOT FOLLOWING] ──────────────────────────► [FOLLOWING]
              ▲                                        │
              │                                        │
              └────────────────────────────────────────┘
                 DELETE /users/{id}/follow (Actor)
```

- **Illegal transitions:**
  - Self-follow (`follower_id == following_id`): Rejected with `422 Unprocessable Entity` (and blocked by DB constraint).
  - Following inactive/deactivated user: Rejected with `404 Not Found`.
  - Duplicate follows: Handled seamlessly via `INSERT ... ON CONFLICT DO NOTHING`.

**Test proving it:**
- `backend/tests/test_follow.py::test_desired_state_idempotence`
- `backend/tests/test_follow.py::test_concurrent_50_duplicate_follows_checkpoint`
- `backend/tests/test_follow.py::test_self_follow_rejected`
