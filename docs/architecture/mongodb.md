# MongoDB migration notes

Not implemented. The file stores are the current database.

## Collections

| Collection | Natural id | Notes |
| --- | --- | --- |
| `stages` | `id` | Static education stages. |
| `grades` | `gradeId` | One document per year, schema version inside the document. |
| `subjects` | `id` | Embedded or referenced units. |
| `units` | `id` | Official BNCC unit plus proposed order. |
| `topics` | `id` | Skills, objectives, prerequisite links. |
| `lessons` | `slug` | Blocks and references. Unique index on `slug`. Index on `topicId`, `status`. |
| `generationTasks` | `id` | Unique index on `idempotencyKey`. |
| `reviews` | `id` | Can stay embedded on the lesson until reviews need their own history. |
| `coverage` | derived | Do not store a second coverage number that can drift. Compute it from published lessons. |

## Rules to keep

- Stable string ids. No renumbering when a database is introduced.
- `schemaVersion` on curriculum documents.
- Lesson blocks remain typed configs. Do not store frontend component source in the database.
- Publication still passes the FastAPI gate. A database write cannot set `published` by itself.
- Backup is a dump of these collections plus the map GeoJSON, which can stay as files or move to object storage with the same license notice.

Indexes to add on migration: `topics.bnccSkillCodes`, `lessons.status + lessons.gradeId`, text index for search only after the Portuguese folding used by the API is reproduced in the query.
