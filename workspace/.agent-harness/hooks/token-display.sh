#!/usr/bin/env zsh
# Shows token usage after each turn. Reads local JSONL only — zero API calls.

HOOK_INPUT=$(cat)

HOOK_INPUT="$HOOK_INPUT" python3 << 'PYEOF'
import json, os, glob, sys

# Rates per 1M tokens: (input, cache_write, cache_read, output).
# Cache write is 1.25x input and cache read 0.1x input across the current lineup;
# Fable's read rate is a documented exception, not that ratio.
RATES = {
    'opus-5':     (5.00,  6.25, 0.50, 25.00),
    'opus-4-8':   (5.00,  6.25, 0.50, 25.00),
    'opus-4-7':   (5.00,  6.25, 0.50, 25.00),
    'opus-4-6':   (5.00,  6.25, 0.50, 25.00),
    'sonnet-5':   (2.00,  2.50, 0.20, 10.00),
    'sonnet-4-6': (3.00,  3.75, 0.30, 15.00),
    'haiku-4-5':  (1.00,  1.25, 0.10,  5.00),
    'fable-5-1':  (10.00, 12.50, 0.25, 50.00),
    'fable-5':    (10.00, 12.50, 0.25, 50.00),
}
DEFAULT = RATES['opus-5']

def rates_for(model):
    if not model:
        return DEFAULT
    for key, r in RATES.items():
        if key in model:
            return r
    return DEFAULT

# Prefer the transcript this Stop hook fired for. Globbing for the newest file
# across all projects reports another session's numbers whenever two run at once.
hook = {}
try:
    hook = json.loads(os.environ.get('HOOK_INPUT') or '{}')
except Exception:
    pass

path = hook.get('transcript_path')
if not path or not os.path.exists(path):
    projects = os.path.expanduser("~/.claude/projects")
    files = sorted(glob.glob(f"{projects}/**/*.jsonl", recursive=True), key=os.path.getmtime, reverse=True)
    if not files:
        sys.exit(0)
    path = files[0]

entries = []
for line in open(path):
    try:
        d = json.loads(line)
        if d.get('type') == 'assistant' and isinstance(d.get('message'), dict):
            m = d['message']
            u = m.get('usage', {})
            if u and (u.get('output_tokens', 0) > 0 or u.get('input_tokens', 0) > 0):
                entries.append((u, m.get('model', '')))
    except Exception:
        pass

if not entries:
    sys.exit(0)

def cost(u, model):
    ri, rcw, rcr, ro = rates_for(model)
    return (u.get('input_tokens', 0) * ri
            + u.get('cache_creation_input_tokens', 0) * rcw
            + u.get('cache_read_input_tokens', 0) * rcr
            + u.get('output_tokens', 0) * ro) / 1_000_000

def total(key): return sum(u.get(key, 0) for u, _ in entries)

last, last_model = entries[-1]
li  = last.get('input_tokens', 0)
lcr = last.get('cache_read_input_tokens', 0)
lo  = last.get('output_tokens', 0)

si, scr, so = total('input_tokens'), total('cache_read_input_tokens'), total('output_tokens')

lc = cost(last, last_model)
sc = sum(cost(u, m) for u, m in entries)

models = {m.split('-2')[0].replace('claude-', '') for _, m in entries if m}
label = ','.join(sorted(models)) or 'unknown'

print(f"── tokens ───────────────────────────────────────────────────────")
print(f"  turn    ↑{li:>6,} in  💾{lcr:>7,} cache-hit  ↓{lo:>5,} out  ~${lc:.4f}")
print(f"  session ↑{si:>6,} in  💾{scr:>7,} cache-hit  ↓{so:>5,} out  ~${sc:.4f}  ({len(entries)} turns, {label})")
print(f"─────────────────────────────────────────────────────────────────")
PYEOF
