# Factory trial: request-changes veto (do not merge)

A clean T1 change. The gate should PASS and approve it. When the code owner then
requests changes, the review relay re-runs the decide job, and `factory-verdict` must
fail with `owner_changes_requested`. The owner's next approval clears it. Close without
merging.
