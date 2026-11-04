# GitHub Actions storage policy

- Development downloads must use Actions artifacts with explicit `retention-days: 7`.
- Upload only final distributables and required runtime/licensing files. Never upload the checkout, dependency caches, intermediate build directories, evidence, or acquisition output.
- Package development downloads only on explicit manual dispatch. Keep useful automated build/tests, avoid duplicate feature-push plus PR runs, and keep historical milestone packaging manual.
- Official releases and their assets are durable records: preserve them. Do not apply the seven-day development policy to release assets.
- Never create or overwrite releases as a side effect of a pull request. Official publication needs a separately reviewed release workflow or explicit operator action.
- Do not delete artifacts, releases, or assets, overwrite published assets, or alter application source without explicit approval.
- Workflow changes must be reviewed on separate branches; do not merge automatically.
- Existing artifacts retain their existing lifecycle; this change does not perform cleanup or change account billing/settings.
