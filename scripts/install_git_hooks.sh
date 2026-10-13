#!/usr/bin/env bash
# Install git hooks to prevent pushing private/personal branches to GitHub
HOOK_DIR="$(git rev-parse --git-dir)/hooks"
mkdir -p "$HOOK_DIR"

PRE_PUSH_HOOK="$HOOK_DIR/pre-push"

cat << 'EOF' > "$PRE_PUSH_HOOK"
#!/usr/bin/env bash
# ==============================================================================
# CareerEngine Pre-Push Security Guard
# Strictly prevents pushing private / personal branches to any remote repository
# ==============================================================================

BLOCKED_BRANCHES=("personal" "local" "private" "my-info")

# Read pushed refs from stdin (format: <local ref> <local sha> <remote ref> <remote sha>)
while read local_ref local_sha remote_ref remote_sha; do
    branch_name="${local_ref#refs/heads/}"
    remote_branch="${remote_ref#refs/heads/}"

    for blocked in "${BLOCKED_BRANCHES[@]}"; do
        if [[ "$branch_name" == "$blocked"* ]] || [[ "$remote_branch" == "$blocked"* ]]; then
            echo ""
            echo "======================================================================"
            echo "🚨 [PUSH BLOCKED] Security Guard triggered!"
            echo "🔒 Branch '$branch_name' is designated as PRIVATE / PERSONAL."
            echo "🚫 Pushing this branch to remote repositories is strictly prohibited."
            echo "💡 Please switch to 'main' or your approved feature branch to push."
            echo "======================================================================"
            echo ""
            exit 1
        fi
    done
done

exit 0
EOF

chmod +x "$PRE_PUSH_HOOK"
echo "✅ CareerEngine pre-push security hook successfully installed at: $PRE_PUSH_HOOK"
