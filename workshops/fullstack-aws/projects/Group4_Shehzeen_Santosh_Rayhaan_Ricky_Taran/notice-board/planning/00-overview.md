# Planning — Overview

This folder is the working plan for the Notice Board deployment
project: goal, research findings, architecture decisions, a tier-by-
tier task plan, a security review, and open risks. It reflects the
system as currently built (`app.py` FastAPI backend, JWT auth, React
frontend, Terraform-managed AWS infra) plus a set of researched,
optional hardening steps not yet applied.

## Files in this folder

| File | Contents |
|---|---|
| `01-research-findings.md` | What current (2026) best-practice guidance says about each technology choice, and where our implementation matches or diverges from it |
| `02-architecture-decisions.md` | The concrete decisions made, why, and the alternatives considered |
| `03-implementation-plan.md` | Tier-by-tier task breakdown with status, matching the assignment's 4 tiers |
| `04-security-plan.md` | Threat-model-style review of the auth system and infra, current posture vs. hardened posture |
| `05-risks-and-open-items.md` | Known gaps, deliberate scope cuts, and things to decide before treating this as production-grade |

## Goal

Ship the Notice Board app (FastAPI + JWT auth backend, React frontend,
Postgres on EC2) through all four assignment tiers — manual deploy,
CI/CD, CDN, observability — using Infrastructure as Code, while
documenting where the implementation takes deliberate shortcuts
appropriate for a class assignment vs. what a production system would
need instead.
