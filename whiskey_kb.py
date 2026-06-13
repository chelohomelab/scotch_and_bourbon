# whiskey_kb.py — Built-in brand knowledge base
#
# PURPOSE: Enrich UPC lookup results with whiskey-specific fields
# (type, region, country, default ABV) when external APIs don't return them.
#
# HOW TO REVERT: Delete this file and remove the lines marked
# "# [KB]" in routers/barcode.py — nothing else touches this.
#
# STRUCTURE:
#   BRAND_KB         — built-in defaults (edit this file to change base values)
#   kb_overrides.json — user corrections that layer on top (auto-updated by the app)
#   enrich()         — call after API lookup; only fills fields that are still None
#   save_correction() — called by bottles router when user saves edited data

from __future__ import annotations
import json
import os

_OVERRIDES_PATH = os.path.join(os.path.dirname(__file__), "kb_overrides.json")

_ENRICHABLE_FIELDS = {"whiskey_type", "region", "country", "abv"}


def _load_overrides() -> dict:
    try:
        with open(_OVERRIDES_PATH, "r") as f:
            data = json.load(f)
        return {k: v for k, v in data.items() if not k.startswith("_")}
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


def _save_overrides(overrides: dict) -> None:
    existing: dict = {}
    try:
        with open(_OVERRIDES_PATH, "r") as f:
            existing = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        pass
    note = existing.get("_note", "Brand-level corrections that override whiskey_kb.py.")
    merged = {k: v for k, v in existing.items() if not k.startswith("_")}
    for brand, fields in overrides.items():
        merged.setdefault(brand, {}).update(fields)
    merged["_note"] = note
    # keep _note at top
    ordered = {"_note": merged.pop("_note"), **merged}
    with open(_OVERRIDES_PATH, "w") as f:
        json.dump(ordered, f, indent=2)


def save_correction(brand: str | None, corrections: dict) -> None:
    """
    Persist a user correction so future lookups for this brand get the right data.
    Only saves fields that are in _ENRICHABLE_FIELDS.
    Called by the bottles router when a bottle is saved with edited KB fields.
    """
    if not brand:
        return
    key = brand.strip().lower()
    if key not in BRAND_KB:
        # Only learn corrections for brands we already know about
        for kb_key in sorted(BRAND_KB, key=len, reverse=True):
            if kb_key in key or key in kb_key:
                key = kb_key
                break
        else:
            return
    clean = {f: v for f, v in corrections.items() if f in _ENRICHABLE_FIELDS and v is not None}
    if clean:
        _save_overrides({key: clean})

BRAND_KB: dict[str, dict] = {

    # ── Speyside Single Malts ─────────────────────────────────
    "balvenie":         {"whiskey_type": "Single Malt Scotch", "region": "Speyside",     "country": "Scotland",       "abv": 40.0},
    "glenfiddich":      {"whiskey_type": "Single Malt Scotch", "region": "Speyside",     "country": "Scotland",       "abv": 40.0},
    "glenlivet":        {"whiskey_type": "Single Malt Scotch", "region": "Speyside",     "country": "Scotland",       "abv": 40.0},
    "macallan":         {"whiskey_type": "Single Malt Scotch", "region": "Speyside",     "country": "Scotland",       "abv": 40.0},
    "glenfarclas":      {"whiskey_type": "Single Malt Scotch", "region": "Speyside",     "country": "Scotland",       "abv": 40.0},
    "benriach":         {"whiskey_type": "Single Malt Scotch", "region": "Speyside",     "country": "Scotland",       "abv": 43.0},
    "craigellachie":    {"whiskey_type": "Single Malt Scotch", "region": "Speyside",     "country": "Scotland",       "abv": 46.0},
    "aberlour":         {"whiskey_type": "Single Malt Scotch", "region": "Speyside",     "country": "Scotland",       "abv": 40.0},
    "cardhu":           {"whiskey_type": "Single Malt Scotch", "region": "Speyside",     "country": "Scotland",       "abv": 40.0},
    "cragganmore":      {"whiskey_type": "Single Malt Scotch", "region": "Speyside",     "country": "Scotland",       "abv": 40.0},
    "knockando":        {"whiskey_type": "Single Malt Scotch", "region": "Speyside",     "country": "Scotland",       "abv": 43.0},
    "strathisla":       {"whiskey_type": "Single Malt Scotch", "region": "Speyside",     "country": "Scotland",       "abv": 43.0},
    "benrinnes":        {"whiskey_type": "Single Malt Scotch", "region": "Speyside",     "country": "Scotland",       "abv": 43.0},
    "longmorn":         {"whiskey_type": "Single Malt Scotch", "region": "Speyside",     "country": "Scotland",       "abv": 48.0},
    "mortlach":         {"whiskey_type": "Single Malt Scotch", "region": "Speyside",     "country": "Scotland",       "abv": 43.4},
    "glen grant":       {"whiskey_type": "Single Malt Scotch", "region": "Speyside",     "country": "Scotland",       "abv": 40.0},
    "glen moray":       {"whiskey_type": "Single Malt Scotch", "region": "Speyside",     "country": "Scotland",       "abv": 40.0},
    "speyburn":         {"whiskey_type": "Single Malt Scotch", "region": "Speyside",     "country": "Scotland",       "abv": 40.0},
    "tomintoul":        {"whiskey_type": "Single Malt Scotch", "region": "Speyside",     "country": "Scotland",       "abv": 40.0},
    "glentauchers":     {"whiskey_type": "Single Malt Scotch", "region": "Speyside",     "country": "Scotland",       "abv": 43.0},
    "linkwood":         {"whiskey_type": "Single Malt Scotch", "region": "Speyside",     "country": "Scotland",       "abv": 43.0},

    # ── Highland Single Malts ─────────────────────────────────
    "dalmore":          {"whiskey_type": "Single Malt Scotch", "region": "Highlands",    "country": "Scotland",       "abv": 40.0},
    "glenmorangie":     {"whiskey_type": "Single Malt Scotch", "region": "Highlands",    "country": "Scotland",       "abv": 43.0},
    "oban":             {"whiskey_type": "Single Malt Scotch", "region": "Highlands",    "country": "Scotland",       "abv": 43.0},
    "aberfeldy":        {"whiskey_type": "Single Malt Scotch", "region": "Highlands",    "country": "Scotland",       "abv": 40.0},
    "tomatin":          {"whiskey_type": "Single Malt Scotch", "region": "Highlands",    "country": "Scotland",       "abv": 43.0},
    "glendronach":      {"whiskey_type": "Single Malt Scotch", "region": "Highlands",    "country": "Scotland",       "abv": 43.0},
    "glengoyne":        {"whiskey_type": "Single Malt Scotch", "region": "Highlands",    "country": "Scotland",       "abv": 43.0},
    "balblair":         {"whiskey_type": "Single Malt Scotch", "region": "Highlands",    "country": "Scotland",       "abv": 43.0},
    "edradour":         {"whiskey_type": "Single Malt Scotch", "region": "Highlands",    "country": "Scotland",       "abv": 40.0},
    "glenturret":       {"whiskey_type": "Single Malt Scotch", "region": "Highlands",    "country": "Scotland",       "abv": 43.0},
    "clynelish":        {"whiskey_type": "Single Malt Scotch", "region": "Highlands",    "country": "Scotland",       "abv": 46.0},
    "deanston":         {"whiskey_type": "Single Malt Scotch", "region": "Highlands",    "country": "Scotland",       "abv": 46.3},
    "glen ord":         {"whiskey_type": "Single Malt Scotch", "region": "Highlands",    "country": "Scotland",       "abv": 40.0},
    "glen garioch":     {"whiskey_type": "Single Malt Scotch", "region": "Highlands",    "country": "Scotland",       "abv": 48.0},
    "royal lochnagar":  {"whiskey_type": "Single Malt Scotch", "region": "Highlands",    "country": "Scotland",       "abv": 40.0},
    "royal brackla":    {"whiskey_type": "Single Malt Scotch", "region": "Highlands",    "country": "Scotland",       "abv": 40.0},
    "blair athol":      {"whiskey_type": "Single Malt Scotch", "region": "Highlands",    "country": "Scotland",       "abv": 43.0},
    "dalwhinnie":       {"whiskey_type": "Single Malt Scotch", "region": "Highlands",    "country": "Scotland",       "abv": 43.0},
    "glencadam":        {"whiskey_type": "Single Malt Scotch", "region": "Highlands",    "country": "Scotland",       "abv": 46.0},
    "ardmore":          {"whiskey_type": "Single Malt Scotch", "region": "Highlands",    "country": "Scotland",       "abv": 40.0},
    "fettercairn":      {"whiskey_type": "Single Malt Scotch", "region": "Highlands",    "country": "Scotland",       "abv": 40.0},
    "glen deveron":     {"whiskey_type": "Single Malt Scotch", "region": "Highlands",    "country": "Scotland",       "abv": 40.0},

    # ── Islay Single Malts ────────────────────────────────────
    "laphroaig":        {"whiskey_type": "Single Malt Scotch", "region": "Islay",        "country": "Scotland",       "abv": 40.0},
    "ardbeg":           {"whiskey_type": "Single Malt Scotch", "region": "Islay",        "country": "Scotland",       "abv": 46.0},
    "lagavulin":        {"whiskey_type": "Single Malt Scotch", "region": "Islay",        "country": "Scotland",       "abv": 43.0},
    "bowmore":          {"whiskey_type": "Single Malt Scotch", "region": "Islay",        "country": "Scotland",       "abv": 40.0},
    "bruichladdich":    {"whiskey_type": "Single Malt Scotch", "region": "Islay",        "country": "Scotland",       "abv": 50.0},
    "caol ila":         {"whiskey_type": "Single Malt Scotch", "region": "Islay",        "country": "Scotland",       "abv": 43.0},
    "bunnahabhain":     {"whiskey_type": "Single Malt Scotch", "region": "Islay",        "country": "Scotland",       "abv": 46.3},
    "kilchoman":        {"whiskey_type": "Single Malt Scotch", "region": "Islay",        "country": "Scotland",       "abv": 46.0},
    "port charlotte":   {"whiskey_type": "Single Malt Scotch", "region": "Islay",        "country": "Scotland",       "abv": 50.0},
    "octomore":         {"whiskey_type": "Single Malt Scotch", "region": "Islay",        "country": "Scotland",       "abv": 59.0},

    # ── Islands Single Malts ──────────────────────────────────
    "highland park":    {"whiskey_type": "Single Malt Scotch", "region": "Islands",      "country": "Scotland",       "abv": 40.0},
    "talisker":         {"whiskey_type": "Single Malt Scotch", "region": "Islands",      "country": "Scotland",       "abv": 45.8},
    "jura":             {"whiskey_type": "Single Malt Scotch", "region": "Islands",      "country": "Scotland",       "abv": 40.0},
    "tobermory":        {"whiskey_type": "Single Malt Scotch", "region": "Islands",      "country": "Scotland",       "abv": 46.3},
    "ledaig":           {"whiskey_type": "Single Malt Scotch", "region": "Islands",      "country": "Scotland",       "abv": 46.3},
    "arran":            {"whiskey_type": "Single Malt Scotch", "region": "Islands",      "country": "Scotland",       "abv": 46.0},
    "scapa":            {"whiskey_type": "Single Malt Scotch", "region": "Islands",      "country": "Scotland",       "abv": 40.0},

    # ── Campbeltown Single Malts ──────────────────────────────
    "springbank":       {"whiskey_type": "Single Malt Scotch", "region": "Campbeltown",  "country": "Scotland",       "abv": 46.0},
    "longrow":          {"whiskey_type": "Single Malt Scotch", "region": "Campbeltown",  "country": "Scotland",       "abv": 46.0},
    "hazelburn":        {"whiskey_type": "Single Malt Scotch", "region": "Campbeltown",  "country": "Scotland",       "abv": 46.0},
    "kilkerran":        {"whiskey_type": "Single Malt Scotch", "region": "Campbeltown",  "country": "Scotland",       "abv": 46.0},
    "glen scotia":      {"whiskey_type": "Single Malt Scotch", "region": "Campbeltown",  "country": "Scotland",       "abv": 46.0},

    # ── Lowland Single Malts ──────────────────────────────────
    "auchentoshan":     {"whiskey_type": "Single Malt Scotch", "region": "Lowlands",     "country": "Scotland",       "abv": 40.0},
    "glenkinchie":      {"whiskey_type": "Single Malt Scotch", "region": "Lowlands",     "country": "Scotland",       "abv": 43.0},
    "bladnoch":         {"whiskey_type": "Single Malt Scotch", "region": "Lowlands",     "country": "Scotland",       "abv": 46.7},
    "annandale":        {"whiskey_type": "Single Malt Scotch", "region": "Lowlands",     "country": "Scotland",       "abv": 46.0},
    "rosebank":         {"whiskey_type": "Single Malt Scotch", "region": "Lowlands",     "country": "Scotland",       "abv": 43.0},

    # ── Blended Scotch ────────────────────────────────────────
    "johnnie walker":   {"whiskey_type": "Blended Scotch",     "region": "Scotland",     "country": "Scotland",       "abv": 40.0},
    "chivas regal":     {"whiskey_type": "Blended Scotch",     "region": "Speyside",     "country": "Scotland",       "abv": 40.0},
    "dewar's":          {"whiskey_type": "Blended Scotch",     "region": "Highlands",    "country": "Scotland",       "abv": 40.0},
    "dewars":           {"whiskey_type": "Blended Scotch",     "region": "Highlands",    "country": "Scotland",       "abv": 40.0},
    "famous grouse":    {"whiskey_type": "Blended Scotch",     "region": "Scotland",     "country": "Scotland",       "abv": 40.0},
    "monkey shoulder":  {"whiskey_type": "Blended Malt Scotch","region": "Speyside",     "country": "Scotland",       "abv": 40.0},
    "grant's":          {"whiskey_type": "Blended Scotch",     "region": "Scotland",     "country": "Scotland",       "abv": 40.0},
    "ballantine's":     {"whiskey_type": "Blended Scotch",     "region": "Scotland",     "country": "Scotland",       "abv": 40.0},
    "ballantines":      {"whiskey_type": "Blended Scotch",     "region": "Scotland",     "country": "Scotland",       "abv": 40.0},
    "black bottle":     {"whiskey_type": "Blended Scotch",     "region": "Islay",        "country": "Scotland",       "abv": 40.0},
    "compass box":      {"whiskey_type": "Blended Malt Scotch","region": "Scotland",     "country": "Scotland",       "abv": 46.0},
    "cutty sark":       {"whiskey_type": "Blended Scotch",     "region": "Scotland",     "country": "Scotland",       "abv": 40.0},
    "j&b":              {"whiskey_type": "Blended Scotch",     "region": "Scotland",     "country": "Scotland",       "abv": 40.0},
    "label 5":          {"whiskey_type": "Blended Scotch",     "region": "Scotland",     "country": "Scotland",       "abv": 40.0},
    "teacher's":        {"whiskey_type": "Blended Scotch",     "region": "Scotland",     "country": "Scotland",       "abv": 40.0},
    "isle of skye":     {"whiskey_type": "Blended Scotch",     "region": "Scotland",     "country": "Scotland",       "abv": 40.0},
    "black dog":        {"whiskey_type": "Blended Scotch",     "region": "Scotland",     "country": "Scotland",       "abv": 42.8},

    # ── Irish Whiskey ─────────────────────────────────────────
    "jameson":          {"whiskey_type": "Irish Whiskey",      "region": "Cork",         "country": "Ireland",        "abv": 40.0},
    "bushmills":        {"whiskey_type": "Irish Whiskey",      "region": "Antrim",       "country": "Ireland",        "abv": 40.0},
    "redbreast":        {"whiskey_type": "Irish Whiskey",      "region": "Cork",         "country": "Ireland",        "abv": 40.0},
    "green spot":       {"whiskey_type": "Irish Whiskey",      "region": "Cork",         "country": "Ireland",        "abv": 40.0},
    "yellow spot":      {"whiskey_type": "Irish Whiskey",      "region": "Cork",         "country": "Ireland",        "abv": 46.0},
    "red spot":         {"whiskey_type": "Irish Whiskey",      "region": "Cork",         "country": "Ireland",        "abv": 46.0},
    "midleton":         {"whiskey_type": "Irish Whiskey",      "region": "Cork",         "country": "Ireland",        "abv": 40.0},
    "teeling":          {"whiskey_type": "Irish Whiskey",      "region": "Dublin",       "country": "Ireland",        "abv": 46.0},
    "powers":           {"whiskey_type": "Irish Whiskey",      "region": "Cork",         "country": "Ireland",        "abv": 40.0},
    "tullamore":        {"whiskey_type": "Irish Whiskey",      "region": "Offaly",       "country": "Ireland",        "abv": 40.0},
    "connemara":        {"whiskey_type": "Irish Whiskey",      "region": "Galway",       "country": "Ireland",        "abv": 40.0},
    "knappogue":        {"whiskey_type": "Irish Whiskey",      "region": "Clare",        "country": "Ireland",        "abv": 40.0},
    "tyrconnell":       {"whiskey_type": "Irish Whiskey",      "region": "Donegal",      "country": "Ireland",        "abv": 40.0},
    "dingle":           {"whiskey_type": "Irish Whiskey",      "region": "Kerry",        "country": "Ireland",        "abv": 46.5},
    "slane":            {"whiskey_type": "Irish Whiskey",      "region": "Meath",        "country": "Ireland",        "abv": 40.0},
    "writer's tears":   {"whiskey_type": "Irish Whiskey",      "region": "Ireland",      "country": "Ireland",        "abv": 40.0},
    "writers tears":    {"whiskey_type": "Irish Whiskey",      "region": "Ireland",      "country": "Ireland",        "abv": 40.0},
    "kilbeggan":        {"whiskey_type": "Irish Whiskey",      "region": "Westmeath",    "country": "Ireland",        "abv": 40.0},
    "glendalough":      {"whiskey_type": "Irish Whiskey",      "region": "Wicklow",      "country": "Ireland",        "abv": 42.0},
    "roe & co":         {"whiskey_type": "Irish Whiskey",      "region": "Dublin",       "country": "Ireland",        "abv": 45.0},
    "paddy":            {"whiskey_type": "Irish Whiskey",      "region": "Cork",         "country": "Ireland",        "abv": 40.0},
    "sexton":           {"whiskey_type": "Irish Whiskey",      "region": "Antrim",       "country": "Ireland",        "abv": 40.0},

    # ── Bourbon ───────────────────────────────────────────────
    "jack daniel":      {"whiskey_type": "Tennessee Whiskey",  "region": "Tennessee",    "country": "United States",  "abv": 40.0},
    "george dickel":    {"whiskey_type": "Tennessee Whiskey",  "region": "Tennessee",    "country": "United States",  "abv": 40.0},
    "jim beam":         {"whiskey_type": "Bourbon",            "region": "Kentucky",     "country": "United States",  "abv": 40.0},
    "maker's mark":     {"whiskey_type": "Bourbon",            "region": "Kentucky",     "country": "United States",  "abv": 45.0},
    "makers mark":      {"whiskey_type": "Bourbon",            "region": "Kentucky",     "country": "United States",  "abv": 45.0},
    "wild turkey":      {"whiskey_type": "Bourbon",            "region": "Kentucky",     "country": "United States",  "abv": 40.5},
    "woodford reserve": {"whiskey_type": "Bourbon",            "region": "Kentucky",     "country": "United States",  "abv": 43.2},
    "buffalo trace":    {"whiskey_type": "Bourbon",            "region": "Kentucky",     "country": "United States",  "abv": 40.0},
    "four roses":       {"whiskey_type": "Bourbon",            "region": "Kentucky",     "country": "United States",  "abv": 40.0},
    "knob creek":       {"whiskey_type": "Bourbon",            "region": "Kentucky",     "country": "United States",  "abv": 50.0},
    "elijah craig":     {"whiskey_type": "Bourbon",            "region": "Kentucky",     "country": "United States",  "abv": 47.0},
    "eagle rare":       {"whiskey_type": "Bourbon",            "region": "Kentucky",     "country": "United States",  "abv": 45.0},
    "blanton's":        {"whiskey_type": "Bourbon",            "region": "Kentucky",     "country": "United States",  "abv": 46.5},
    "blantons":         {"whiskey_type": "Bourbon",            "region": "Kentucky",     "country": "United States",  "abv": 46.5},
    "weller":           {"whiskey_type": "Bourbon",            "region": "Kentucky",     "country": "United States",  "abv": 45.0},
    "old forester":     {"whiskey_type": "Bourbon",            "region": "Kentucky",     "country": "United States",  "abv": 43.0},
    "evan williams":    {"whiskey_type": "Bourbon",            "region": "Kentucky",     "country": "United States",  "abv": 43.0},
    "larceny":          {"whiskey_type": "Bourbon",            "region": "Kentucky",     "country": "United States",  "abv": 46.0},
    "heaven hill":      {"whiskey_type": "Bourbon",            "region": "Kentucky",     "country": "United States",  "abv": 40.0},
    "pappy van winkle": {"whiskey_type": "Bourbon",            "region": "Kentucky",     "country": "United States",  "abv": 45.0},
    "van winkle":       {"whiskey_type": "Bourbon",            "region": "Kentucky",     "country": "United States",  "abv": 45.0},
    "angel's envy":     {"whiskey_type": "Bourbon",            "region": "Kentucky",     "country": "United States",  "abv": 43.3},
    "angels envy":      {"whiskey_type": "Bourbon",            "region": "Kentucky",     "country": "United States",  "abv": 43.3},
    "booker's":         {"whiskey_type": "Bourbon",            "region": "Kentucky",     "country": "United States",  "abv": 62.0},
    "bookers":          {"whiskey_type": "Bourbon",            "region": "Kentucky",     "country": "United States",  "abv": 62.0},
    "baker's":          {"whiskey_type": "Bourbon",            "region": "Kentucky",     "country": "United States",  "abv": 53.5},
    "basil hayden":     {"whiskey_type": "Bourbon",            "region": "Kentucky",     "country": "United States",  "abv": 40.0},
    "old crow":         {"whiskey_type": "Bourbon",            "region": "Kentucky",     "country": "United States",  "abv": 40.0},
    "old grand-dad":    {"whiskey_type": "Bourbon",            "region": "Kentucky",     "country": "United States",  "abv": 40.0},
    "henry mckenna":    {"whiskey_type": "Bourbon",            "region": "Kentucky",     "country": "United States",  "abv": 50.0},
    "rebel yell":       {"whiskey_type": "Bourbon",            "region": "Kentucky",     "country": "United States",  "abv": 40.0},
    "fighting cock":    {"whiskey_type": "Bourbon",            "region": "Kentucky",     "country": "United States",  "abv": 51.5},
    "noah's mill":      {"whiskey_type": "Bourbon",            "region": "Kentucky",     "country": "United States",  "abv": 57.15},
    "rowan's creek":    {"whiskey_type": "Bourbon",            "region": "Kentucky",     "country": "United States",  "abv": 50.05},
    "michter's":        {"whiskey_type": "Bourbon",            "region": "Kentucky",     "country": "United States",  "abv": 45.7},
    "michters":         {"whiskey_type": "Bourbon",            "region": "Kentucky",     "country": "United States",  "abv": 45.7},
    "1792":             {"whiskey_type": "Bourbon",            "region": "Kentucky",     "country": "United States",  "abv": 46.85},
    "barton":           {"whiskey_type": "Bourbon",            "region": "Kentucky",     "country": "United States",  "abv": 40.0},
    "very old barton":  {"whiskey_type": "Bourbon",            "region": "Kentucky",     "country": "United States",  "abv": 43.0},

    # ── Rye Whiskey ───────────────────────────────────────────
    "whistlepig":       {"whiskey_type": "Rye Whiskey",        "region": "Vermont",      "country": "United States",  "abv": 50.0},
    "rittenhouse":      {"whiskey_type": "Rye Whiskey",        "region": "Kentucky",     "country": "United States",  "abv": 50.0},
    "high west":        {"whiskey_type": "Rye Whiskey",        "region": "Utah",         "country": "United States",  "abv": 46.0},
    "sazerac rye":      {"whiskey_type": "Rye Whiskey",        "region": "Kentucky",     "country": "United States",  "abv": 45.0},
    "templeton":        {"whiskey_type": "Rye Whiskey",        "region": "Iowa",         "country": "United States",  "abv": 40.0},
    "pikesville":       {"whiskey_type": "Rye Whiskey",        "region": "Kentucky",     "country": "United States",  "abv": 55.0},
    "old overholt":     {"whiskey_type": "Rye Whiskey",        "region": "Kentucky",     "country": "United States",  "abv": 40.0},
    "redemption":       {"whiskey_type": "Rye Whiskey",        "region": "Indiana",      "country": "United States",  "abv": 46.0},
    "george washington":{"whiskey_type": "Rye Whiskey",        "region": "Virginia",     "country": "United States",  "abv": 45.0},

    # Note: Bulleit defaults to Bourbon; if title contains "rye", the title
    # parser in barcode.py catches it first and this entry is not used for type.
    "bulleit":          {"whiskey_type": "Bourbon",            "region": "Kentucky",     "country": "United States",  "abv": 45.0},

    # ── Japanese Whisky ───────────────────────────────────────
    "yamazaki":         {"whiskey_type": "Japanese Whisky",    "region": "Osaka",        "country": "Japan",          "abv": 43.0},
    "hakushu":          {"whiskey_type": "Japanese Whisky",    "region": "Yamanashi",    "country": "Japan",          "abv": 43.0},
    "hibiki":           {"whiskey_type": "Japanese Whisky",    "region": "Japan",        "country": "Japan",          "abv": 43.0},
    "toki":             {"whiskey_type": "Japanese Whisky",    "region": "Japan",        "country": "Japan",          "abv": 43.0},
    "yoichi":           {"whiskey_type": "Japanese Whisky",    "region": "Hokkaido",     "country": "Japan",          "abv": 45.0},
    "miyagikyo":        {"whiskey_type": "Japanese Whisky",    "region": "Miyagi",       "country": "Japan",          "abv": 45.0},
    "nikka":            {"whiskey_type": "Japanese Whisky",    "region": "Japan",        "country": "Japan",          "abv": 40.0},
    "suntory":          {"whiskey_type": "Japanese Whisky",    "region": "Japan",        "country": "Japan",          "abv": 40.0},
    "chita":            {"whiskey_type": "Japanese Whisky",    "region": "Aichi",        "country": "Japan",          "abv": 43.0},
    "akashi":           {"whiskey_type": "Japanese Whisky",    "region": "Hyogo",        "country": "Japan",          "abv": 40.0},
    "mars":             {"whiskey_type": "Japanese Whisky",    "region": "Nagano",       "country": "Japan",          "abv": 40.0},
    "fuji":             {"whiskey_type": "Japanese Whisky",    "region": "Shizuoka",     "country": "Japan",          "abv": 46.0},
    "togouchi":         {"whiskey_type": "Japanese Whisky",    "region": "Hiroshima",    "country": "Japan",          "abv": 40.0},
    "chichibu":         {"whiskey_type": "Japanese Whisky",    "region": "Saitama",      "country": "Japan",          "abv": 50.5},
    "kirin":            {"whiskey_type": "Japanese Whisky",    "region": "Japan",        "country": "Japan",          "abv": 40.0},
    "white oak":        {"whiskey_type": "Japanese Whisky",    "region": "Hyogo",        "country": "Japan",          "abv": 40.0},

    # ── Canadian Whisky ───────────────────────────────────────
    "crown royal":      {"whiskey_type": "Canadian Whisky",    "region": "Manitoba",     "country": "Canada",         "abv": 40.0},
    "canadian club":    {"whiskey_type": "Canadian Whisky",    "region": "Ontario",      "country": "Canada",         "abv": 40.0},
    "forty creek":      {"whiskey_type": "Canadian Whisky",    "region": "Ontario",      "country": "Canada",         "abv": 40.0},
    "wiser's":          {"whiskey_type": "Canadian Whisky",    "region": "Ontario",      "country": "Canada",         "abv": 40.0},
    "wisers":           {"whiskey_type": "Canadian Whisky",    "region": "Ontario",      "country": "Canada",         "abv": 40.0},
    "pike creek":       {"whiskey_type": "Canadian Whisky",    "region": "Ontario",      "country": "Canada",         "abv": 40.0},
    "lot no. 40":       {"whiskey_type": "Canadian Whisky",    "region": "Ontario",      "country": "Canada",         "abv": 43.0},
    "alberta premium":  {"whiskey_type": "Canadian Whisky",    "region": "Alberta",      "country": "Canada",         "abv": 40.0},
    "canadian mist":    {"whiskey_type": "Canadian Whisky",    "region": "Ontario",      "country": "Canada",         "abv": 40.0},
    "caribou crossing": {"whiskey_type": "Canadian Whisky",    "region": "Canada",       "country": "Canada",         "abv": 40.0},
    "seagram":          {"whiskey_type": "Canadian Whisky",    "region": "Canada",       "country": "Canada",         "abv": 40.0},
    "gibsons":          {"whiskey_type": "Canadian Whisky",    "region": "Canada",       "country": "Canada",         "abv": 40.0},
    "black velvet":     {"whiskey_type": "Canadian Whisky",    "region": "Alberta",      "country": "Canada",         "abv": 40.0},
    "pendleton":        {"whiskey_type": "Canadian Whisky",    "region": "Canada",       "country": "Canada",         "abv": 40.0},
}


def enrich(brand: str | None, title: str | None) -> dict:
    """
    Look up missing whiskey fields from the knowledge base.
    Base values come from BRAND_KB; user corrections in kb_overrides.json layer on top.
    Longer keys are tried first to prefer more specific matches
    (e.g. 'highland park' before 'highland').
    Returns a dict of fields — caller decides which ones to apply.
    """
    if not brand and not title:
        return {}

    haystack = f"{brand or ''} {title or ''}".lower()
    overrides = _load_overrides()

    for key in sorted(BRAND_KB, key=len, reverse=True):
        if key in haystack:
            result = dict(BRAND_KB[key])
            if key in overrides:
                result.update({f: v for f, v in overrides[key].items() if f in _ENRICHABLE_FIELDS})
            return result

    return {}
