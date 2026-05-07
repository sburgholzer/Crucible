from aws_cdk import (
    Stack,
    aws_budgets as budgets,
    aws_iam as iam,
    aws_sns as sns,
    aws_sns_subscriptions as subs,  # noqa: F401
)
from constructs import Construct
import cdk_nag


class CrucibleMainStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # --- Cost Guardrails ---

        # SNS topic for budget alerts
        budget_topic = sns.Topic(self, "BudgetAlertTopic",
            display_name="Crucible Budget Alerts",
            enforce_ssl=True,
        )

        # Optional: add your email for notifications
        # budget_topic.add_subscription(subs.EmailSubscription("you@example.com"))

        # $50/month hard cap budget filtered to Project=Crucible
        budgets.CfnBudget(self, "CrucibleBudget",
            budget=budgets.CfnBudget.BudgetDataProperty(
                budget_name="Crucible-Monthly-50",
                budget_type="COST",
                time_unit="MONTHLY",
                budget_limit=budgets.CfnBudget.SpendProperty(
                    amount=50,
                    unit="USD",
                ),
                cost_filters={
                    "TagKeyValue": ["user:Project$Crucible"],
                },
            ),
            notifications_with_subscribers=[
                budgets.CfnBudget.NotificationWithSubscribersProperty(
                    notification=budgets.CfnBudget.NotificationProperty(
                        comparison_operator="GREATER_THAN",
                        notification_type="ACTUAL",
                        threshold=80,
                        threshold_type="PERCENTAGE",
                    ),
                    subscribers=[
                        budgets.CfnBudget.SubscriberProperty(
                            address=budget_topic.topic_arn,
                            subscription_type="SNS",
                        ),
                    ],
                ),
                budgets.CfnBudget.NotificationWithSubscribersProperty(
                    notification=budgets.CfnBudget.NotificationProperty(
                        comparison_operator="GREATER_THAN",
                        notification_type="ACTUAL",
                        threshold=100,
                        threshold_type="PERCENTAGE",
                    ),
                    subscribers=[
                        budgets.CfnBudget.SubscriberProperty(
                            address=budget_topic.topic_arn,
                            subscription_type="SNS",
                        ),
                    ],
                ),
            ],
        )

        # --- IAM Foundation ---

        # Role for chaos operations — tightly scoped blast radius
        self.chaos_trigger_role = iam.Role(self, "ChaosTriggerRole",
            role_name="crucible-chaos-trigger",
            assumed_by=iam.ServicePrincipal("lambda.amazonaws.com"),
            description="Used by trigger-fis Lambda and FIS experiments. Scoped to /crucible/* and Project=Crucible tagged resources only.",
        )

        # Allow SSM parameter writes only under /crucible/*
        self.chaos_trigger_role.add_to_policy(iam.PolicyStatement(
            sid="SSMCrucibleOnly",
            actions=[
                "ssm:PutParameter",
                "ssm:GetParameter",
            ],
            resources=[
                f"arn:aws:ssm:*:{self.account}:parameter/crucible/*",
            ],
        ))

        # Allow starting FIS experiments only on Crucible-tagged resources
        self.chaos_trigger_role.add_to_policy(iam.PolicyStatement(
            sid="FISStartExperiment",
            actions=[
                "fis:StartExperiment",
                "fis:GetExperiment",
                "fis:ListExperiments",
            ],
            resources=["*"],
            conditions={
                "StringEquals": {
                    "aws:ResourceTag/Project": "Crucible",
                },
            },
        ))

        # Allow publishing to EventBridge (for ground-truth events)
        self.chaos_trigger_role.add_to_policy(iam.PolicyStatement(
            sid="EventBridgePublish",
            actions=["events:PutEvents"],
            resources=[
                f"arn:aws:events:*:{self.account}:event-bus/crucible-*",
            ],
        ))

        # Inline log permissions instead of AWS managed policy (satisfies AwsSolutions-IAM4)
        self.chaos_trigger_role.add_to_policy(iam.PolicyStatement(
            sid="LambdaLogging",
            actions=[
                "logs:CreateLogGroup",
                "logs:CreateLogStream",
                "logs:PutLogEvents",
            ],
            resources=[
                f"arn:aws:logs:*:{self.account}:log-group:/aws/lambda/crucible-*",
            ],
        ))

        # --- cdk-nag suppressions for intentional wildcards ---
        cdk_nag.NagSuppressions.add_resource_suppressions(
            self.chaos_trigger_role,
            suppressions=[
                cdk_nag.NagPackSuppression(
                    id="AwsSolutions-IAM5",
                    reason="SSM wildcard scoped to /crucible/* path prefix. "
                           "FIS wildcard is constrained by aws:ResourceTag/Project=Crucible condition. "
                           "EventBridge wildcard scoped to crucible-* bus names. "
                           "Logs wildcard scoped to /aws/lambda/crucible-* log groups. "
                           "All wildcards are bounded to project resources only.",
                ),
            ],
            apply_to_children=True,
        )
