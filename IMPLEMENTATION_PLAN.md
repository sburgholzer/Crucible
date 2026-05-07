# Crucible — Implementation Plan

Multi-region resilience playground + AI on-call copilot.

---

## Phase 1: Foundation & Project Setup

1. **Initialize CDK project**
   - `npx cdk init app --language python`
   - Set up multi-stack structure: `NetworkStack`, `AppStack`, `ObservabilityStack`, `ChaosStack`, `CopilotStack`
   - Configure CDK for multi-region deployment (us-east-1, us-west-2)

2. **Set up CI/CD**
   - Create GitHub repo
   - Add GitHub Actions workflow: lint → cdk-nag → cdk synth → deploy
   - Add Infracost integration for PR cost comments

3. **Configure cost guardrails**
   - Create AWS Budget ($50/mo hard cap)
   - Wire EventBridge rule → Lambda to disable chaos-api on budget breach
   - Tag all resources with `Project=Crucible` for cost tracking

4. **IAM foundation**
   - Design least-privilege roles per stack
   - Create `chaos-trigger` role scoped to `arn:...:parameter/crucible/*` and FIS actions on `Project=Crucible` tagged resources only

---

## Phase 2: Target Application (Multi-Region)

5. **DynamoDB Global Table**
   - Create on-demand table for the url-shortener app
   - Enable Global Tables replication between us-east-1 and us-west-2

6. **Lambda — url-shortener + /health**
   - Write a simple URL shortener Lambda (create short link, redirect)
   - Add `/health` endpoint that reads SSM Parameter Store `/crucible/regions/{region}/healthy`
   - Deploy to both regions

7. **API Gateway HTTP API (regional)**
   - Create regional HTTP API in each region
   - Route to url-shortener Lambda
   - Enable access logging

8. **Route 53 failover routing**
   - Create hosted zone
   - Add health checks pointing at each region's `/health`
   - Configure failover routing policy (primary: us-east-1, secondary: us-west-2)

9. **SSM Parameter Store**
   - Create `/crucible/regions/us-east-1/healthy` = "true"
   - Create `/crucible/regions/us-west-2/healthy` = "true"

---

## Phase 3: Observability

10. **CloudWatch Alarms (per region)**
    - p95 latency on API Gateway
    - 5xx error rate
    - DynamoDB throttle events
    - Canary failure alarm

11. **CloudWatch Synthetics Canaries (per region)**
    - Create canary that hits the regional API Gateway `/health` endpoint
    - Set 5-min interval (or on-demand trigger from chaos panel)

12. **X-Ray tracing**
    - Enable active tracing on Lambda functions
    - Enable X-Ray on API Gateway

13. **CloudWatch Dashboard**
    - Live RTO metric
    - Region health status
    - Copilot accuracy (added later in Phase 6)

---

## Phase 4: Chaos Control Plane

14. **S3 + CloudFront — Chaos Panel SPA**
    - Create S3 bucket for static hosting
    - Set up CloudFront distribution with OAI
    - Scaffold React app with buttons: "Kill us-east-1", "Throttle DDB", "Latency 500ms"

15. **API Gateway — chaos-api**
    - Create HTTP API for chaos operations
    - Add routes: `POST /chaos/trigger`, `POST /chaos/reset`

16. **Lambda — trigger-fis**
    - Accept chaos action from API
    - Start corresponding FIS experiment template
    - Publish ground-truth event to EventBridge chaos-events bus

17. **EventBridge — chaos-events bus**
    - Create custom event bus
    - Add rule to write ground-truth events to DynamoDB

18. **FIS experiment templates**
    - "Kill region" — `aws:ssm:start-automation-execution` to flip SSM `/healthy` param to "false"
    - "Throttle DDB" — inject DynamoDB throttle errors via Lambda chaos extension
    - "Latency 500ms" — inject latency into Lambda via FIS Lambda actions (tag-targeted)

19. **Lambda — reset**
    - Rolls back all chaos: reset SSM params, stop FIS experiments
    - Wired to "Reset" button in SPA

---

## Phase 5: Detection & Ground Truth

20. **EventBridge alarm-rule**
    - Rule matching CloudWatch Alarm state changes
    - Targets: SNS (ops-alerts) + copilot-orchestrator Lambda

21. **SNS — ops-alerts**
    - Topic for alarm notifications
    - (Optional) email subscription for demo visibility

22. **DynamoDB — ground-truth table**
    - Schema: `{ run_id, what_was_broken, alarms_fired, copilot_diagnosis, was_correct }`
    - Written to by chaos-events bus (what was broken) and slack-notifier (diagnosis)

23. **Lambda — eval-api**
    - Scans ground-truth table
    - Returns aggregated eval metrics (precision, accuracy over time)

24. **Eval tab in Chaos Panel SPA**
    - Add tab to React app
    - Calls eval-api to display copilot accuracy metrics

---

## Phase 6: On-Call Copilot (Bedrock Agent)

25. **S3 — runbooks bucket**
    - Upload markdown runbooks (common failure modes, remediation steps)
    - These serve as the knowledge base for the search-kb tool

26. **Bedrock Titan Embeddings + FAISS**
    - Lambda `search-kb` embeds query via Bedrock Titan
    - Loads FAISS index from S3 into `/tmp` on cold start
    - Returns relevant runbook chunks

27. **Lambda — query-logs**
    - Runs CloudWatch Logs Insights queries
    - Returns recent error patterns

28. **Lambda — query-metrics**
    - Calls CloudWatch GetMetricData
    - Returns relevant metric snapshots (latency, error rates, throttles)

29. **Lambda — recent-deploys**
    - Queries for recent deployment activity (CloudFormation events, CodeDeploy, etc.)
    - Provides change correlation context

30. **Bedrock Agent — sre-copilot**
    - Create agent with Claude Haiku model
    - Define Action Group with tools: query-logs, query-metrics, search-kb, recent-deploys
    - Set token budget per invocation
    - Add Bedrock Guardrails

31. **Lambda — copilot-orchestrator**
    - Triggered by EventBridge alarm-rule
    - Invokes Bedrock Agent with alarm context
    - Passes diagnosis to slack-notifier

32. **Lambda — slack-notifier**
    - Reads Slack webhook URL from Secrets Manager
    - Posts diagnosis JSON to Slack #oncall-crucible
    - Writes diagnosis back to ground-truth table

33. **Secrets Manager**
    - Store Slack webhook URL

---

## Phase 7: Polish & Demo Readiness

34. **End-to-end smoke test**
    - Trigger chaos from SPA → verify alarm fires → verify copilot diagnosis arrives in Slack
    - Check ground-truth table has complete row
    - Validate eval tab shows correct/incorrect classification

35. **CloudWatch Dashboard — final**
    - Add copilot accuracy widget
    - Add RTO tracking (time from chaos trigger to alarm fire)

36. **Documentation**
    - Architecture decision records (why no OpenSearch, why no ALB, etc.)
    - README with demo walkthrough
    - Cost breakdown and budget justification

37. **Demo script**
    - Write a repeatable demo flow:
      1. Open Chaos Panel
      2. Click "Kill us-east-1"
      3. Show Route 53 failover in action
      4. Show alarm firing in CloudWatch
      5. Show Bedrock Agent diagnosis in Slack
      6. Click "Reset"
      7. Show eval tab with accuracy metrics

---

## Suggested Implementation Order

```
Week 1:  Phase 1 (setup) + Phase 2 (target app)
Week 2:  Phase 3 (observability) + Phase 4 (chaos control plane)
Week 3:  Phase 5 (detection/ground truth) + Phase 6 (copilot)
Week 4:  Phase 7 (polish, demo, docs)
```

---

## Key Risks & Mitigations

| Risk | Mitigation |
|------|-----------|
| Bedrock Agent latency too high for "real-time" feel | Token budget + Haiku model; async Slack delivery is acceptable |
| FIS experiments affect other workloads | IAM scoped to `Project=Crucible` tag; SSM params under `/crucible/*` only |
| Canary costs creep up | Default to on-demand trigger from SPA; 5-min interval only during active demos |
| Cold start on search-kb Lambda (FAISS load) | Keep runbook corpus small; use provisioned concurrency if needed ($) |
| Budget breach during experimentation | Hard cap + auto-disable; monitor daily in first week |
