# Example: stuck → absorb

```bash
# 1. You're blocked
python scripts/forge.py stuck "API returns 401 after token refresh" \
  --skills "scavenger-mode" --parent mist-prime

# 2. Work as the printed clone id — open files, run commands, fix it
# 3. Journal on the clone, then:

python scripts/forge.py absorb mist-api-returns-401-after-token-refresh \
  --into mist-prime \
  --lesson "refresh must rotate both access and refresh tokens before retry"
```

Host (`mist-prime`) gains generation + lessons. Husk lands in `archive/`.
