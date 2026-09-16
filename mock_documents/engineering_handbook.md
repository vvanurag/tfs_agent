# Engineering Handbook & Sprint Guidelines

## 1. Sprint Lifecycle & Cadence
* All development operates on 2-week sprint cycles (currently in **Sprint 12**).
* Daily standups occur at 09:30 AM EST.
* Sprint retrospectives and sprint planning take place on alternating Fridays.

## 2. Work Item Tracking Standards
* All work items must be logged in Azure DevOps (TFS) with appropriate categorization: `Bug`, `Task`, `User Story`, `Feature`, or `Epic`.
* Severity levels:
  - `1 - Critical`: Immediate blocker affecting production or batch claims processing.
  - `2 - High`: Major functionality impaired with no viable workaround.
  - `3 - Medium`: Moderate issue with existing operational workaround.
  - `4 - Low`: Minor cosmetic or non-functional defect.

## 3. Git Branching & Commit Conventions
* Branch naming format: `feature/<ticket-id>-short-description` or `bugfix/<ticket-id>-short-description`.
* Commit messages must follow Conventional Commits standard (e.g., `feat:`, `fix:`, `docs:`, `test:`).
