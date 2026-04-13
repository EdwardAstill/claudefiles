---
name: regex-expert
description: >
  High-performance codebase manipulation using regex. Use when you need to
  perform mass search and replace, refactor symbol names across many files,
  or clean up structured data. Leverages `sd` for intuitive find/replace
  and `ripgrep` (rg) for lightning-fast multi-file search. Much safer and
  faster than `sed` or custom Python scripts for text manipulation.
---

# Regex Expert

Specialist in codebase-wide text manipulation. Uses modern Rust-powered tools
(`sd`, `rg`) to safely and quickly refactor code.

## Core Tools

| Tool | Command | Purpose |
|------|---------|---------|
| `sd` | `sd <old> <new> <path>` | Find and replace using regex (modern `sed`) |
| `rg` | `rg <pattern> <path>` | Find pattern across many files (fastest `grep`) |

## Workflows

### 1. Mass Renaming / Refactoring
When you need to rename a class, function, or variable across the entire project:

1. **Find all occurrences:**
   ```bash
   rg "OldName"
   ```
2. **Perform the replace (dry-run first!):**
   ```bash
   # Dry-run (prints what would change)
   sd "OldName" "NewName" $(rg -l "OldName") --preview
   
   # Actual replace
   sd "OldName" "NewName" $(rg -l "OldName")
   ```

### 2. Complex Regex Replacements
`sd` uses Rust's `regex` crate, which supports standard regex syntax.

```bash
# Replace date format (YYYY-MM-DD to DD/MM/YYYY)
sd "(\d{4})-(\d{2})-(\d{2})" "\$3/\$2/\$1" src/*.log
```

### 3. Cleaning Up Structured Data
If a file has messy spacing or extra characters:

```bash
# Collapse multiple spaces into one
sd " +" " " data.txt

# Remove trailing whitespace from all files in a directory
sd " +$" "" $(find . -type f)
```

## Why `sd` over `sed`?
- **Intuitive syntax:** Uses the same regex syntax as `rg` and the `Skill` agent.
- **Escape safety:** Doesn't require the nightmare escaping rules of `sed`.
- **Performance:** Written in Rust, it's significantly faster for large files.
- **In-place by default:** Modifies the file directly without needing `-i`.

## Best Practices
- **Always `rg` first:** Verify exactly which files and lines you're going to touch.
- **Limit scope:** Don't run on the whole project if you only mean to touch `src/`.
- **Check `.gitignore`:** `rg` respects `.gitignore` by default; ensure you're not missing or hitting hidden files.
- **Verify after replace:** Run a quick `rg` again to ensure the pattern is gone and the new one is present.
- **Tests:** Always run the test suite after a mass-replace to catch any broken logic or accidental symbol collisions.
