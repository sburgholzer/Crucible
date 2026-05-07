#!/usr/bin/env python3
import os

import aws_cdk as cdk

from stacks.crucible_main_stack import CrucibleMainStack
from stacks.app_stack import AppStack
from stacks.chaos_stack import ChaosStack
from stacks.medic_stack import MedicStack
from stacks.observability_stack import ObservabilityStack


app = cdk.App()
CrucibleMainStack(app, "CrucibleMainStack",
    # If you don't specify 'env', this stack will be environment-agnostic.
    # Account/Region-dependent features and context lookups will not work,
    # but a single synthesized template can be deployed anywhere.

    # Uncomment the next line to specialize this stack for the AWS Account
    # and Region that are implied by the current CLI configuration.

    #env=cdk.Environment(account=os.getenv('CDK_DEFAULT_ACCOUNT'), region=os.getenv('CDK_DEFAULT_REGION')),

    # Uncomment the next line if you know exactly what Account and Region you
    # want to deploy the stack to. */

    #env=cdk.Environment(account='123456789012', region='us-east-1'),

    # For more information, see https://docs.aws.amazon.com/cdk/latest/guide/environments.html
    )

app.synth()
