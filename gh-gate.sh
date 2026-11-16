#!/usr/bin/env bash
set -euo pipefail
REPO="KrugercoinHF/buddy-computer-forge"
BRANCH="main"
MODE="${1:---plan}"
if [[ "$MODE" != "--plan" && "$MODE" != "--apply" ]]; then echo "Usage: $0 [--plan|--apply]"; exit 2; fi
command -v gh >/dev/null || { echo "GitHub CLI (gh) is required."; exit 2; }
gh auth status >/dev/null
echo "Repository: $REPO"
echo "Target branch: $BRANCH"
echo "Plan: require pull requests, one approving review, dismiss stale approvals, resolve conversations, enforce admins."
echo "Required status contexts must be discovered from successful CI runs before applying; this script does not guess them."
if [[ "$MODE" == "--plan" ]]; then echo "PLAN ONLY. No settings changed."; exit 0; fi
echo "WARNING: this changes branch protection on main."
read -r -p "Type APPLY-PROTECTION to continue: " confirm
[[ "$confirm" == "APPLY-PROTECTION" ]] || { echo "Cancelled."; exit 1; }
gh api --method PUT "repos/$REPO/branches/$BRANCH/protection" -H "Accept: application/vnd.github+json" -f required_status_checks=null -f enforce_admins=true -f required_pull_request_reviews.required_approving_review_count=1 -f required_pull_request_reviews.dismiss_stale_reviews=true -f required_conversation_resolution=true -f restrictions=null
echo "Protection updated. Verify in GitHub settings before relying on it."
