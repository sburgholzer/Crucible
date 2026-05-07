# Crucible — Implementation Plan

Multi-region resilience playground + AI on-call medic.

---

## Phase 1: Foundation & Project Setup

- [X] **Initialize CDK project**
  - [x] `npx cdk init app --language python`
  - [x] Set up multi-stack structure: `NetworkStack`, `AppStack`, `ObservabilityStack`, `ChaosStack`, `MedicStack`
  - [x] Configure CDK for multi-region deployment (us-east-1, us-west-2)

- [x] **Set up CI/CD**
  - [x] Create GitHub repo
  - [x] Add GitHub Actions workflow: lint → cdk-nag → cdk synth → deploy
  - [x] Add Infracost integration for PR cost comments

- [x] **Configure cost guardrails**
  - [x] Create AWS Budget ($50/mo hard cap)
  - [x] Tag all resources with `Project=Crucible` for cost tracking

- [x] **IAM foundation**
  - [ ] Design least-privilege roles per stack (happens naturally as we build, cdk creates scoped roles automatically)
  - [x] Create `chaos-trigger` role scoped to `arn:...:parameter/crucible/*` and FIS actions on `Project=Crucible` tagged resources only

---

## Phase 2: Target Application (Multi-Region)

- [ ] **DynamoDB Global Table**
  - [ ] Create on-demand table for the url-shortener app
  - [ ] Enable Global Tables replication between us-east-1 and us-west-2

- [ ] **Lambda — url-shortener + /health**
  - [ ] Write a simple URL shortener Lambda (create short link, redirect)
  - [ ] Add `/health` endpoint that reads SSM Parameter Store `/crucible/regions/{region}/healthy`
  - [ ] Deploy to both regions

- [ ] **API Gateway HTTP API (regional)**
  - [ ] Create regional HTTP API in each region
  - [ ] Route to url-shortener Lambda
  - [ ] Enable access logging

- [ ] **Route 53 failover routing**
  - [ ] Create hosted zone
  - [ ] Add health checks pointing at each region's `/health`
  - [ ] Configure failover routing policy (primary: us-east-1, secondary: us-west-2)

- [ ] **SSM Parameter Store**
  - [ ] Create `/crucible/regions/us-east-1/healthy` = "true"
  - [ ] Create `/crucible/regions/us-west-2/healthy` = "true"

---

## Phase 3: Observability

- [ ] **CloudWatch Alarms (per region)**
  - [ ] p95 latency on API Gateway
  - [ ] 5xx error rate
  - [ ] DynamoDB throttle events
  - [ ] Canary failure alarm

- [ ] **CloudWatch Synthetics Canaries (per region)**
  - [ ] Create canary that hits the regional API Gateway `/health` endpoint
  - [ ] Set 5-min interval (or on-demand trigger from chaos panel)

- [ ] **X-Ray tracing**
  - [ ] Enable active tracing on Lambda functions
  - [ ] Enable X-Ray on API Gateway

- [ ] **CloudWatch Dashboard**
  - [ ] Live RTO metric
  - [ ] Region health status
  - [ ] Medic accuracy (added later in Phase 6)

---

## Phase 4: Chaos Control Plane

- [ ] **S3 + CloudFront — Chaos Panel SPA**
  - [ ] Create S3 bucket for static hosting
  - [ ] Set up CloudFront distribution with OAI
  - [ ] Scaffold React app with buttons: "Kill us-east-1", "Throttle DDB", "Latency 500ms"

- [ ] **API Gateway — chaos-api**
  - [ ] Create HTTP API for chaos operations
  - [ ] Add routes: `POST /chaos/trigger`, `POST /chaos/reset`

- [ ] **Lambda — trigger-fis**
  - [ ] Accept chaos action from API
  - [ ] Start corresponding FIS experiment template
  - [ ] Publish ground-truth event to EventBridge chaos-events bus

- [ ] **EventBridge — chaos-events bus**
  - [ ] Create custom event bus
  - [ ] Add rule to write ground-truth events to DynamoDB

- [ ] **FIS experiment templates**
  - [ ] "Kill region" — `aws:ssm:start-automation-execution` to flip SSM `/healthy` param to "false"
  - [ ] "Throttle DDB" — inject DynamoDB throttle errors via Lambda chaos extension
  - [ ] "Latency 500ms" — inject latency into Lambda via FIS Lambda actions (tag-targeted)

- [ ] **Lambda — reset**
  - [ ] Rolls back all chaos: reset SSM params, stop FIS experiments
  - [ ] Wired to "Reset" button in SPA

- [ ] **Budget auto-disable**
  - [ ] Wire EventBridge rule → Lambda to disable chaos-api on budget breach

---

## Phase 5: Detection & Ground Truth

- [ ] **EventBridge alarm-rule**
  - [ ] Rule matching CloudWatch Alarm state changes
  - [ ] Targets: SNS (ops-alerts) + medic-orchestrator Lambda

- [ ] **SNS — ops-alerts**
  - [ ] Topic for alarm notifications
  - [ ] (Optional) email subscription for demo visibility

- [ ] **DynamoDB — ground-truth table**
  - [ ] Schema: `{ run_id, what_was_broken, alarms_fired, medic_diagnosis, was_correct }`
  - [ ] Written to by chaos-events bus (what was broken) and slack-notifier (diagnosis)

- [ ] **Lambda — eval-api**
  - [ ] Scans ground-truth table
  - [ ] Returns aggregated eval metrics (precision, accuracy over time)

- [ ] **Eval tab in Chaos Panel SPA**
  - [ ] Add tab to React app
  - [ ] Calls eval-api to display medic accuracy metrics

---

## Phase 6: On-Call Medic (Bedrock Agent)

- [ ] **S3 — runbooks bucket**
  - [ ] Upload markdown runbooks (common failure modes, remediation steps)
  - [ ] These serve as the knowledge base for the search-kb tool

- [ ] **Bedrock Titan Embeddings + FAISS**
  - [ ] Lambda `search-kb` embeds query via Bedrock Titan
  - [ ] Loads FAISS index from S3 into `/tmp` on cold start
  - [ ] Returns relevant runbook chunks

- [ ] **Lambda — query-logs**
  - [ ] Runs CloudWatch Logs Insights queries
  - [ ] Returns recent error patterns

- [ ] **Lambda — query-metrics**
  - [ ] Calls CloudWatch GetMetricData
  - [ ] Returns relevant metric snapshots (latency, error rates, throttles)

- [ ] **Lambda — recent-deploys**
  - [ ] Queries for recent deployment activity (CloudFormation events, CodeDeploy, etc.)
  - [ ] Provides change correlation context

- [ ] **Bedrock Agent — sre-medic**
  - [ ] Create agent with Claude Haiku model
  - [ ] Define Action Group with tools: query-logs, query-metrics, search-kb, recent-deploys
  - [ ] Set token budget per invocation
  - [ ] Add Bedrock Guardrails

- [ ] **Lambda — medic-orchestrator**
  - [ ] Triggered by EventBridge alarm-rule
  - [ ] Invokes Bedrock Agent with alarm context
  - [ ] Passes diagnosis to slack-notifier

- [ ] **Lambda — slack-notifier**
  - [ ] Reads Slack webhook URL from Secrets Manager
  - [ ] Posts diagnosis JSON to Slack #oncall-crucible
  - [ ] Writes diagnosis back to ground-truth table

- [ ] **Secrets Manager**
  - [ ] Store Slack webhook URL

---

## Phase 7: Polish & Demo Readiness

- [ ] **End-to-end smoke test**
  - [ ] Trigger chaos from SPA → verify alarm fires → verify medic diagnosis arrives in Slack
  - [ ] Check ground-truth table has complete row
  - [ ] Validate eval tab shows correct/incorrect classification

- [ ] **CloudWatch Dashboard — final**
  - [ ] Add medic accuracy widget
  - [ ] Add RTO tracking (time from chaos trigger to alarm fire)

- [ ] **Documentation**
  - [ ] Architecture decision records (why no OpenSearch, why no ALB, etc.)
  - [ ] README with demo walkthrough
  - [ ] Cost breakdown and budget justification

- [ ] **Demo script**
  - [ ] Write a repeatable demo flow:
    1. Open Chaos Panel
    2. Click "Kill us-east-1"
    3. Show Route 53 failover in action
    4. Show alarm firing in CloudWatch
    5. Show Medic diagnosis in Slack
    6. Click "Reset"
    7. Show eval tab with accuracy metrics

---

## Suggested Implementation Order

```
Week 1:  Phase 1 (setup) + Phase 2 (target app)
Week 2:  Phase 3 (observability) + Phase 4 (chaos control plane)
Week 3:  Phase 5 (detection/ground truth) + Phase 6 (medic)
Week 4:  Phase 7 (polish, demo, docs)
```

---

## Key Risks & Mitigations

| Risk | Mitigation |
|------|-----------|
| Medic latency too high for "real-time" feel | Token budget + Haiku model; async Slack delivery is acceptable |
| FIS experiments affect other workloads | IAM scoped to `Project=Crucible` tag; SSM params under `/crucible/*` only |
| Canary costs creep up | Default to on-demand trigger from SPA; 5-min interval only during active demos |
| Cold start on search-kb Lambda (FAISS load) | Keep runbook corpus small; use provisioned concurrency if needed ($) |
| Budget breach during experimentation | Hard cap + auto-disable; monitor daily in first week |
