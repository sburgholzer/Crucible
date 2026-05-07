#!/usr/bin/env python3
import os

import aws_cdk as cdk

from stacks.crucible_main_stack import CrucibleMainStack
from stacks.app_stack import AppStack
from stacks.chaos_stack import ChaosStack
from stacks.medic_stack import MedicStack
from stacks.observability_stack import ObservabilityStack


app = cdk.App()

ACCOUNT = os.getenv("CDK_DEFAULT_ACCOUNT", "123456789012")

env_east = cdk.Environment(account=ACCOUNT, region="us-east-1")
env_east = cdk.Environment(account=ACCOUNT, region="us-east-1")

# Deploy the same app stack to both regions
app_east = AppStack(app, "CrucibleApp-East", env=env_east)
app_west = AppStack(app, "CrucibleApp-West", env=env_west)

# Chaos control plane only needs one region
ChaosStack(app, "CrucibleChaos", env=env_east)

app.synth()
