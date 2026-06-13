# Whiskey Knowledge Base — How It Works & How to Roll Back

## What It Does

When you scan a UPC barcode, `UPCItemDB` returns basic product info (brand, title, images, retail prices).
It often **does not** return whiskey-specific fields like ABV, region, country, or whiskey type.

The knowledge base (`whiskey_kb.py`) fills those gaps using a built-in table of ~130 commercial whiskey brands.
It **only fills fields that are still empty** after the API lookup — it never overrides data the API already returned.

### Fields enriched
| Field | Example |
|---|---|
| `whiskey_type` | Single Malt Scotch |
| `region` | Speyside |
| `country` | Scotland |
| `abv` | 43.0% |

---

## Two Layers of Data

### 1. `whiskey_kb.py` — Base knowledge (edit manually or via Claude)
The main brand database. Contains default values for ~130 brands organized by region:
- Speyside, Highland, Islay, Islands, Campbeltown, Lowland (Single Malt Scotch)
- Blended Scotch, Irish, Bourbon, Rye, Japanese, Canadian

**Important:** ABV values in this file are the most common bottling for each brand.
Some brands bottle at different strengths for different markets (e.g. Balvenie 12yr is 40% US, 43% UK).

### 2. `kb_overrides.json` — User corrections (auto-updated by the app)
When you edit a bottle's type, region, country, or ABV and save it, the app **automatically writes your correction** here.
Next time the same brand is looked up, the corrected value is used instead of the base.

Example `kb_overrides.json`:
```json
{
  "_note": "Brand-level corrections that override whiskey_kb.py.",
  "balvenie": {"abv": 43.0}
}
```

You can also edit this file manually at any time.

---

## How Auto-Learning Works

1. You scan a barcode → form pre-fills with KB data (e.g. Balvenie ABV: 40%)
2. You notice the bottle actually says 43% → you correct it in the form and save
3. The app writes `{"balvenie": {"abv": 43.0}}` to `kb_overrides.json`
4. Next time you scan a Balvenie, it pre-fills 43% automatically

**Only the four enrichable fields trigger a correction:** `whiskey_type`, `region`, `country`, `abv`.
Rating, notes, status, price, etc. are personal and are NOT learned.

---

## Where the Code Lives

| File | Purpose |
|---|---|
| `whiskey_kb.py` | Base KB + `enrich()` + `save_correction()` functions |
| `kb_overrides.json` | Auto-generated user corrections |
| `routers/barcode.py` | Calls `enrich()` after UPC API lookup — lines marked `# [KB]` |
| `routers/bottles.py` | Calls `save_correction()` on PATCH — lines marked `# [KB]` |

---

## How to Roll Back Completely

**Step 1** — Delete the KB files:
```bash
rm /opt/scotch_and_bourbon/whiskey_kb.py
rm /opt/scotch_and_bourbon/kb_overrides.json
```

**Step 2** — Remove the `# [KB]` lines from `routers/barcode.py`:
```python
# Delete this import:
from whiskey_kb import enrich as kb_enrich  # [KB]

# Delete this block (after image download loop):
# [KB] Enrich missing fields from built-in brand knowledge base.
_kb = kb_enrich(brand, title)
if not whiskey_type: whiskey_type = _kb.get("whiskey_type")
if not region:        region       = _kb.get("region")
if not country:       country      = _kb.get("country")
if abv is None:       abv          = _kb.get("abv")

# Delete this block (in the cache-hit path):
# [KB] Enrich cached results that are missing fields
_kb = kb_enrich(resp.get("brand"), resp.get("title"))
for f in ("whiskey_type", "region", "country", "abv"):
    if not resp.get(f): resp[f] = _kb.get(f)
```

**Step 3** — Remove the `# [KB]` lines from `routers/bottles.py`:
```python
# Delete this import:
from whiskey_kb import save_correction as kb_save_correction  # [KB]

# Delete these lines inside patch_bottle():
# [KB] Learn from user corrections to enrichable fields
kb_fields = {f: updates[f] for f in ("whiskey_type", "region", "country", "abv") if f in updates}
if kb_fields:
    kb_save_correction(b.brand, kb_fields)
```

**Step 4** — Restart the service:
```bash
systemctl restart scotch-and-bourbon
```

---

## Adding a New Brand Manually

Edit `whiskey_kb.py` and add a line to `BRAND_KB`:
```python
"glen example": {"whiskey_type": "Single Malt Scotch", "region": "Highlands", "country": "Scotland", "abv": 46.0},
```
Key rules:
- Key must be **lowercase**
- Key should be the shortest unique prefix (e.g. `"glen example"` not `"the glen example distillery"`)
- Longer keys are matched first, so more specific names beat shorter ones

Or just tell Claude: *"Add Glen Example Distillery, Highlands, Single Malt, 46% ABV"* and it will update the file.

---

## Correcting a Wrong Value

**Option A — Let the app learn:** Edit the bottle in the app, change the wrong field, hit save. Done.

**Option B — Edit the override file directly:**
```bash
nano /opt/scotch_and_bourbon/kb_overrides.json
```

**Option C — Tell Claude:** *"The Balvenie ABV should be 43%, not 40%"* and it will update `kb_overrides.json`.
