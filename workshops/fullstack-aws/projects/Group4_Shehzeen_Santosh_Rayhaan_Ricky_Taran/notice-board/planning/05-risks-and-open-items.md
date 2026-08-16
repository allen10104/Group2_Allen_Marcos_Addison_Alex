# Risks and Open Items

## Unresolved — needs an answer before Tier 1 can actually deploy

1. **EC2 Postgres networking.** Neither the assignment nor this
   project's prior context specifies whether the EC2 Postgres instance
   from the earlier lab is reachable via a public IP + security group,
   or only from inside its VPC. `terraform/variables.tf` supports both
   (`lambda_vpc_subnet_ids`/`lambda_vpc_security_group_ids`, empty by
   default), but the right values can't be filled in without checking
   the actual EC2 instance's networking. **Action:** check the EC2
   instance's VPC/subnet/security-group config before running
   `terraform apply`.

2. **AWS region.** `terraform/variables.tf` defaults `aws_region` to
   `us-east-1`, matching the assignment's GitHub Secrets example. If
   the EC2 Postgres instance lives in a different region, either move
   it or set `aws_region` to match — cross-region Lambda-to-EC2 calls
   add latency and, depending on VPC setup, may not even be routable.

3. **Naming convention for `<your-name>`.** The assignment says
   prefix resources with `student-<your-name>` but doesn't specify
   exact formatting (case, separators). Confirm against the grading
   rubric if one exists.

## Deliberate scope cuts (documented, not oversights)

These are called out in more detail in `02-architecture-decisions.md`
and `04-security-plan.md`; listed here as a single "known gaps" index:

- No notice-ownership model (any logged-in user can delete any notice)
- No refresh tokens / short-lived-access-token rotation
- JWT stored in `localStorage`, not an HttpOnly cookie
- No database migration tool (schema managed by idempotent
  `CREATE TABLE IF NOT EXISTS` in application code)
- Static AWS access keys in GitHub Actions rather than OIDC
- Local Terraform state rather than an S3 remote backend

None of these block the assignment's stated acceptance criteria. All
are flagged so a future pass (or a grader asking "why not X") has a
documented answer rather than silence.

## Recommended follow-up work (optional, ranked by effort-to-value)

1. **Set `lifespan="off"` on Mangum explicitly** — one-line change,
   removes a hypothetical foot-gun even though we have no lifespan
   handlers today. Lowest effort, do this first.
2. **Scope the GitHub Actions IAM deploy user to least privilege** —
   `lambda:UpdateFunctionCode`, `s3:PutObject`/`DeleteObject`/`ListBucket`
   on this project's specific resources only, plus
   `cloudfront:CreateInvalidation` once Tier 3 is live. Should be done
   regardless of the OIDC question below — a scoped static key is
   still better than a broad one.
3. **Migrate GitHub Actions auth to OIDC** — removes the two static
   key secrets entirely. Moderate effort (new `aws_iam_openid_connect_provider`
   + trust policy resources, workflow permissions block, IAM role
   ARN as the new secret). Worth doing if this project outlives the
   assignment.
4. **Move Terraform state to an S3 backend with `use_lockfile = true`**
   — only matters once more than one person/machine touches this
   state, or if losing the local `.tfstate` file would be costly.
   Not urgent for a single-student assignment.
5. **Refresh-token rotation** — highest effort of this list, and the
   lowest value for this specific app (a public notice board with no
   sensitive data). Only worth doing if this evolves into something
   handling real user accounts/PII.
