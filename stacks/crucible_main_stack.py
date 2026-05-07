from aws_cdk import (
    Stack,
    aws_budgets as budgets,
    aws_sns as sns,
    aws_sns_subscriptions as subs,
)
from constructs import Construct


class CrucibleMainStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # --- Cost Guardrails ---

        # SNS topic for budget alerts
        budget_topic = sns.Topic(self, "BudgetAlertTopic",
            display_name="Crucible Budget Alerts",
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
