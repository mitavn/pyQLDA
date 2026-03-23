---
description: Push code to git after completing changes
---

# Push Git Workflow

After completing code changes and confirming they work correctly, follow these steps:

// turbo-all

1. Stage all changes:
```
git add -A
```

2. Commit with a descriptive message in Vietnamese:
```
git commit -m "<mô tả ngắn gọn những thay đổi>"
```

3. Push to remote (if remote is configured):
```
git push
```

## Notes
- Always run this workflow after finishing code changes that are working correctly.
- Commit messages should be concise and descriptive in Vietnamese.
- If there's no remote configured, skip the push step.
