# Automation

## What runs today

From `backend/`:

```bash
python3 -m app.automation.cli validate
python3 -m app.automation.cli dry-run
python3 -m app.automation.cli window-check
python3 -m app.automation.cli generate-one --packet ../content/packets/ef04ma09.json
python3 -m app.automation.cli next --grade ef-5
python3 -m app.automation.cli generate-one
```

`generate-one`, `generate-five`, `continue`, `until-budget`, and `regenerate` exit with code 2 when no research packet is provided. They do not write a lesson. `until-budget` also refuses to start when `NAESCOLA_MONTHLY_BUDGET_USD` is empty, and it stops if a task records unknown usage instead of inventing token counts.

`window-check` is true on calendar days 1, 2, and 3 in `Europe/Berlin`, including daylight-saving time. The check is tested. It does not start generation.

## What is not operational

Unattended monthly lesson generation is not operational.

- No provider credential was configured.
- Cursor subscription usage, agent quotas, and API tokens are not read and are not treated as the same budget.
- `.github/workflows/validation.yml` can validate and dry-run on GitHub-hosted runners, including a cron at 04:00 UTC on days 1–4. The job then asks the Berlin window check what the local day is. The job does not publish lessons.
- That workflow file has not been observed running on GitHub from the environment that added it. A cron in a pull request does not run until the workflow is on the default branch and GitHub accepts the schedule.

## When the computer is off

A GitHub-hosted runner can execute the validation workflow without the personal computer. That only checks the repository. It cannot draft new lessons until a provider and a budget are configured as secrets and the job is changed to call them. A scheduler on the Windows machine stops when the machine sleeps. Neither option is a running generator today.
