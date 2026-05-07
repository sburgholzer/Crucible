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
