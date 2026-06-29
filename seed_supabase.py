"""
seed_supabase.py — Lê estudo-japones.html e popula Supabase com vocabulário + partículas.
Uso: python seed_supabase.py
"""
import re, json, sys, subprocess

SUPABASE_URL = "https://zhrfhmhhdebcphsqghai.supabase.co"
API_KEY      = "sb_publishable_8Ip9IUf9c0ycsKJKkCOTwA_VmQGnHXy"
HTML_PATH    = r"c:\Users\hamil\OneDrive\Desktop\Nova pasta\estudo-japones.html"

with open(HTML_PATH, "r", encoding="utf-8") as f:
    html = f.read()

# ── helpers ───────────────────────────────────────────────────────
def post_batch(table, rows, label=""):
    if not rows:
        print(f"  {label}: 0 rows — pulando"); return
    url = f"{SUPABASE_URL}/rest/v1/{table}"
    for i in range(0, len(rows), 100):
        batch = rows[i:i+100]
        payload = json.dumps(batch, ensure_ascii=False)
        result = subprocess.run(
            ["curl", "-s", "-o", "/dev/null", "-w", "%{http_code}",
             "-X", "POST", url,
             "-H", f"apikey: {API_KEY}",
             "-H", f"Authorization: Bearer {API_KEY}",
             "-H", "Content-Type: application/json",
             "-H", "Prefer: return=minimal",
             "--data-binary", payload],
            capture_output=True, text=True
        )
        code = result.stdout.strip()
        status = "OK" if code in ("200","201") else f"ERRO {code}: {result.stderr[:80]}"
        print(f"  {label} batch {i//100+1} ({len(batch)} linhas): {status}")

def scan_braces(text, start, open_c='{', close_c='}'):
    """Retorna o índice logo após o bloco que começa em start (já dentro do bloco)."""
    depth = 1; i = start
    while i < len(text) and depth:
        if text[i] == open_c:  depth += 1
        elif text[i] == close_c: depth -= 1
        i += 1
    return i

def scan_brackets(text, start):
    return scan_braces(text, start, '[', ']')

# ── 1. Vocabulário (RAW object) ───────────────────────────────────
print("=== Vocabulário ===")
vocab_rows = []

raw_m = re.search(r'const RAW = \{', html)
if not raw_m:
    sys.exit("ERRO: const RAW não encontrado no HTML")

raw_end  = scan_braces(html, raw_m.end())
raw_block = html[raw_m.end():raw_end-1]

les_matches = list(re.finditer(r'L(\d+):\{', raw_block))
for li, lm in enumerate(les_matches):
    lesson_num = int(lm.group(1))
    les_start  = lm.end()
    les_end    = les_matches[li+1].start() if li+1 < len(les_matches) else len(raw_block)
    les_block  = raw_block[les_start:les_end]

    # Categorias: Verbos:[...] ou "Adjetivos な":[...]
    cat_matches = list(re.finditer(r'(?:"([^"]+)"|(\w[\w\s/]*?)):\[', les_block))
    for ci, cm in enumerate(cat_matches):
        cat_name  = (cm.group(1) or cm.group(2)).strip()
        arr_start = cm.end()
        arr_end   = scan_brackets(les_block, arr_start)
        arr_block = les_block[arr_start:arr_end-1]

        for em in re.finditer(r'"([^"]+\|[^"]*\|[^"]+)"', arr_block):
            parts = em.group(1).split("|")
            if len(parts) == 3:
                kanji, kana, pt = parts
                vocab_rows.append({
                    "kanji":      kanji or None,
                    "kana":       kana  or None,
                    "portuguese": pt,
                    "lesson":     lesson_num,
                    "category":   cat_name,
                })

print(f"  {len(vocab_rows)} entradas encontradas")
post_batch("vocabulary", vocab_rows, "vocab")

# ── 2. Partículas (PARTS array) ───────────────────────────────────
print("\n=== Partículas ===")
parts_rows = []

parts_m = re.search(r'const PARTS = \[', html)
if parts_m:
    parts_end   = scan_brackets(html, parts_m.end())
    parts_block = html[parts_m.end():parts_end-1]

    for pm in re.finditer(r'\{p:"([^"]+)",rom:"([^"]+)",f:\[', parts_block):
        particle = pm.group(1); romaji = pm.group(2)
        f_start  = pm.end()
        f_end    = scan_brackets(parts_block, f_start)
        f_block  = parts_block[f_start:f_end-1]

        # Remove HTML tags in d field for clean storage
        for um in re.finditer(
            r'\{l:(\d+),role:"([^"]+)",d:"([^"]*)",j:"([^"]*)",k:"([^"]*)",t:"([^"]*)"\}',
            f_block
        ):
            desc = re.sub(r'<[^>]+>', '', um.group(3))   # strip <b> etc.
            ex_j = re.sub(r'<[^>]+>', '', um.group(4))
            parts_rows.append({
                "particle":    particle,
                "romaji":      romaji,
                "lesson":      int(um.group(1)),
                "role":        um.group(2),
                "description": desc,
                "example_jp":  ex_j,
                "example_kana": um.group(5),
                "example_pt":  um.group(6),
            })

print(f"  {len(parts_rows)} usos de partículas encontrados")
post_batch("particles", parts_rows, "parts")

print("\nConcluído.")
