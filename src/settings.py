# This file is maintained for backward compatibility
# Additional environment-specific settings
import os

# Explicitly set environment variables
os.environ["AWS_PROFILE"] = "cengage"
os.environ["AWS_REGION"] = "us-east-1"
os.environ["AWS_DEFAULT_REGION"] = "us-east-1"

# Endpoints
NeptuneEndpoint = "neptune-db://contentai-neptune-01-instance-1.crgki0ug6nab.us-east-1.neptune.amazonaws.com:8182"
VectorStoreEndpoint = "aoss://https://1tsv2alzp27po3fu3rmk.us-east-1.aoss.amazonaws.com"
