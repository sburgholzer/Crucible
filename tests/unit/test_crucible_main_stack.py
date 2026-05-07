import aws_cdk as core
import aws_cdk.assertions as assertions

from stacks.crucible_main_stack import CrucibleMainStack


def test_budget_created():
    app = core.App()
    stack = CrucibleMainStack(app, "TestMain")
    template = assertions.Template.from_stack(stack)

    template.has_resource_properties("AWS::Budgets::Budget", {
        "Budget": {
            "BudgetName": "Crucible-Monthly-50",
            "BudgetType": "COST",
        }
    })
