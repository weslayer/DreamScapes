import pulumi
import pulumi_aws as aws

# Create an S3 bucket
bucket = aws.s3.Bucket("dreamscapeassetbucket",
    acl="private",
    cors_rules=[aws.s3.BucketCorsRuleArgs(
        allowed_headers=["*"],
        allowed_methods=["GET", "POST", "PUT"],
        allowed_origins=["*"],
        max_age_seconds=3000
    )],
    versioning=aws.s3.BucketVersioningArgs(
        enabled=True
    ),
    tags={
        "Environment": "production",
        "Project": "dreamscape"
    }
)

# Export the bucket name
pulumi.export('bucket_name', bucket.id) 