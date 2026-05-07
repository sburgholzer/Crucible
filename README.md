# Crucible
Trigger real chaos in AWS, watch active-active failover happen, and let a Bedrock Agent diagnose what broke. Multi-region serverless resilience playground built with CDK.

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### Silence Node.js version warning

CDK hasn't been tested against Node v25 yet. Everything works fine, but to suppress the warning banner:

```bash
export JSII_SILENCE_WARNING_UNTESTED_NODE_VERSION=1
```

Add to your shell profile (`.bashrc` / `.zshrc`) to make it permanent.

## Naming

The AI diagnosis component is called **Medic** (not "Copilot"). The original architecture used "copilot" but we renamed it to avoid confusion with Microsoft's Copilot branding. "Medic" fits the theme better anyway — chaos breaks things, the medic diagnoses what went wrong.

## CI/CD

GitHub Actions runs on every PR:
- **Lint** (ruff) → **CDK Synth** → **CDK Nag** (AWS best practice checks) → **Infracost** (cost estimate comment)

### Infracost setup

Infracost posts a cost breakdown comment on every PR so you can see the dollar impact of infrastructure changes before merging.

1. Get a free API key at [infracost.io](https://www.infracost.io/)
2. Add it as a GitHub repo secret: **Settings → Secrets → Actions → `INFRACOST_API_KEY`**

That's it — the workflow handles the rest.

## IAM Strategy

**Least-privilege by default.** CDK generates scoped IAM roles automatically when you use grant methods (e.g. `table.grant_read_write_data(fn)`). Each stack's resources get their own narrowly-scoped roles — no shared "god" roles.

**`crucible-chaos-trigger` role** (defined in `CrucibleMainStack`) is the security boundary for chaos operations:

- `ssm:PutParameter` / `ssm:GetParameter` — only on `parameter/crucible/*`
- `fis:StartExperiment` — only on resources tagged `Project=Crucible`
- `events:PutEvents` — only to `crucible-*` event buses

This means even if the chaos Lambda is misconfigured, it physically cannot touch resources outside the Crucible project.
