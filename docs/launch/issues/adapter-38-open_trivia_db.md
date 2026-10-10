---
title: "Add an Open Trivia DB adapter for quiz questions"
labels: ["good first issue", "adapter", "hacktoberfest", "toolset:fun"]
---

Open Trivia DB serves multiple-choice and true or false questions across dozens of categories. It lets an agent write a quiz with real questions and a known right answer.

## API

- Docs: https://opentdb.com/api_config.php
- Base URL: `https://opentdb.com`
- It works without a key, token or account.
- Suggested adapter name: `open_trivia_db`, in the `fun` toolset.

## Proposed tools

### `open_trivia_db_get_questions(amount: int = 5, category: int | None = None, difficulty: str | None = None, question_type: str | None = None)`

Get quiz questions. `difficulty` is `easy`, `medium` or `hard`, and `question_type` is `multiple` or `boolean`. Returns the question, the correct answer and the incorrect answers.

### `open_trivia_db_list_categories()`

List the category ids and names.

## Example

```text
GET https://opentdb.com/api.php?amount=2
```

Fields worth returning: `response_code` and `results[]` with `type`, `difficulty`, `category`, `question`, `correct_answer` and `incorrect_answers`. `/api_category.php` returns `trivia_categories[]` with `id` and `name`.

## Acceptance checklist

- [ ] Scaffold it with `make new-adapter NAME=open_trivia_db TOOLSET=fun`.
- [ ] `adapter.yaml` has the real base URL, docs URL, a rate limit that respects the API's policy, and your GitHub handle.
- [ ] Every tool has a description that says what it returns, and every parameter has a description with an example value.
- [ ] Tests cover the catalog, a happy path for each tool, a live smoke test, and one error path: a call made too soon after the last one returns HTTP 429 with `response_code` 5, and an `amount` of 0 or 100 should raise `InvalidInput` before any request.
- [ ] `make record ADAPTER=open_trivia_db` has recorded small cassettes, and you read them before committing.
- [ ] `make test` and `make lint` pass.
- [ ] `make adapters-md` has been run and the updated `ADAPTERS.md` is in the pull request.

## Hints

- The API reports problems in `response_code` and not always in the HTTP status. `0` is success. `1` means not enough questions, `2` an invalid parameter and `5` a rate limit. Map the others to readable errors.
- Text contains HTML entities such as `&amp;`. Use `html.unescape`.
- The API allows about one request every five seconds from one IP. Set `rate_limit_per_minute` to 12 or lower and test the 429 path.

## Claim it

Comment below to claim this. Please take one adapter at a time. Open your pull request with `Closes #<this issue>`, and if you cannot finish, say so here so someone else can pick it up. [CONTRIBUTING.md](https://github.com/sineframe/keyless-mcp/blob/main/CONTRIBUTING.md) has the steps, and [docs/adapter-contract.md](https://github.com/sineframe/keyless-mcp/blob/main/docs/adapter-contract.md) has the rules.
