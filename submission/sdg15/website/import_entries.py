#!/usr/bin/env python3
"""Fills the site's entries for indicators 15.2.1 to 15.2.6 from the compendium content
(../evidence-docs/content.json, written by evidence-docs/build.py).

Usage: python3 import_entries.py      (then rebuild the site with node build_site.js)
Entries of 15.1 are written by hand in src/sdg15_data.json and are left untouched.
"""
import json
import os
import re

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "src", "sdg15_data.json")
CONTENT = os.path.join(HERE, "..", "evidence-docs", "content.json")
ASSETS = os.path.join(HERE, "..", "evidence-docs", "assets")

# story key -> (card year label, sort year, full date or period, type)
META = {
    "parambak_2025":      ("2025", 2025, "14 February 2025", "Event"),
    "forest_planting":    ("2025", 2025, "2 July 2025", "Tree planting"),
    "wed_mangrove":       ("2025", 2025, "June 2025", "Mangrove planting"),
    "coconut_greenwall":  ("2025", 2025, "24 July 2025", "Tree planting"),
    "regen_forum":        ("2025", 2025, "19 November 2025", "Forum"),
    "fieldday":           ("2025", 2025, "28 October 2025", "Field day"),
    "idbd_contest":       ("2025", 2025, "Deadline 30 May 2025", "Contest"),
    "planting_continues": ("2024 to 2026", 2026, "9 July 2024, 2 July 2025 and 1 June 2026", "Tree planting"),
    "greenhouse_2025":    ("2025", 2025, "13 May 2025", "Training"),
    "forest_reserve":     ("2025", 2025, "2 July 2025", "Habitat enrichment"),
    "ifp_conservation":   ("2025", 2025, "2025", "Conservation program"),
    "mangrove_nbs":       ("2025", 2025, "2025", "Project"),
    "badoc_mangrove":     ("2025", 2025, "6 December 2025", "Mangrove planting"),
    "pinili_short":       ("2025", 2025, "September 2025", "Bambusetum"),
    "ifp_pna_2026":       ("2026", 2026, "6 June 2026", "News report"),
    "nbs_launch":         ("2024 to 2026", 2026, "1 May 2024 to 30 April 2026", "Project"),
    "bambusetum_2026":    ("2025 to 2026", 2026, "September 2025 and 30 September 2026", "Bambusetum"),
    "hub":                ("2023", 2023, "13 January 2023", "Habitat enrichment"),
    "mangrove_seminar":   ("2025", 2025, "27 to 28 October 2025", "Training"),
    "alukon":             ("2025", 2025, "2 May 2025", "Training"),
    "vintar_caravan":     ("2025", 2025, "3 to 4 December 2025", "Festival"),
    "ifp_learning":       ("2025", 2025, "World Food Day, October 2025", "Learning garden"),
    "soa":                ("2025", 2025, "June to December 2025", "Radio school"),
    "pinili":             ("2025", 2025, "September 2025", "Training"),
    "vermicast":          ("2025", 2025, "2025", "Facility"),
    "onion_training":     ("2025", 2025, "12 November 2025", "Training"),
    "pshs_visit":         ("2025", 2025, "19 September 2025", "School visit"),
    "soil_health":        ("2025", 2025, "March to June 2025", "Research project"),
    "paddy_art_2025":     ("2025", 2025, "7 July to 9 September 2025", "Farm-tourism attraction"),
    "talon":              ("2026", 2026, "15 January 2026", "Project plan"),
    "kpnp":               ("2023", 2023, "29 March 2023", "Appointment"),
}
# stories whose evidence needs a caution
STATUS = {
    "idbd_contest": ("Reported in MMSU's 2025 report", "The announcement or results link still has to be added."),
    "mangrove_nbs": ("Verified on the source page", "The DENR dialogue and the October 2024 agreement come from MMSU's 2025 report; no independent record was found."),
}
INDICATOR_NOTES = {
    "15.2.2": "Draft. THE asks for a policy that food on campus is sustainably farmed. No dated MMSU policy was found; the entries here are 2025 campus farming practice that supports it. Attach the policy, or a Business Directorate sourcing memorandum, before submitting.",
    "15.2.4": "THE gives full credit only to free programmes. State in each training entry whether it was free of charge.",
    "15.2.5": "THE gives full credit only to free programmes. State in each training entry whether it was free of charge.",
    "15.2.6": "Draft. The 2025 entry is a farm-tourism attraction with student guides, and the TALON project is a plan approved in January 2026. Neither is yet a structured training for communities. Add visitor numbers or a community programme with its dates and audience.",
}
ID_RE = re.compile(r"[^a-z0-9]")


def first_sentences(text, limit=300):
    parts = re.split(r"(?<=[.!?])\s+", text.strip())
    out = ""
    for p in parts:
        if out and len(out) + len(p) + 1 > limit:
            break
        out = (out + " " + p).strip()
    return out


def main():
    data = json.load(open(DATA, encoding="utf8"))
    c = json.load(open(CONTENT, encoding="utf8"))
    ind_title = {i["code"]: i["title"] for m in data["metrics"] for i in m["indicators"]}
    docs = {d["code"]: d for d in c["docs"] if d["code"].startswith("15.2.")}

    # where each story appears
    where = {}
    for code, d in docs.items():
        for k in d["stories"] + d.get("continuing", []):
            where.setdefault(k, []).append(code)

    def eid(k):
        return "s" + ID_RE.sub("", k.lower())

    for code in sorted(docs):
        d = docs[code]
        entries = []
        for k in d["stories"] + d.get("continuing", []):
            if k not in META:
                raise SystemExit(f"Add {k} to META")
            s = c["stories"][k]
            years, sort_year, date, typ = META[k]
            photos = []
            for ph in s["photos"]:
                if os.path.exists(os.path.join(ASSETS, ph)):
                    photos.append({"img": os.path.splitext(ph)[0], "caption": c["photos"].get(ph, "")})
            sources = []
            for sk in s["sources"]:
                src = c["sources"][sk]
                sources.append({"label": src["label"], "url": src["url"] or ""})
            status, note = STATUS.get(k, ("Verified on the source page", ""))
            also = [[o, eid(k)] for o in where[k] if o != code]
            first_url = next((x["url"] for x in sources if x["url"]), "")
            first_label = next((x["label"] for x in sources if x["url"]), "")
            entry = {
                "id": eid(k), "years": years, "sortYear": sort_year, "type": typ, "title": s["title"],
                "people": "", "summary": first_sentences(s["paras"][0]),
                "sourceLabel": first_label, "sourceUrl": first_url, "status": status,
                "continuing": k in d.get("continuing", []),
                "detail": {
                    "lead": first_sentences(s["paras"][0], 220),
                    "photos": photos,
                    "facts": [["Date", date], ["Entry type", typ],
                              ["Evidence period", "Continuing implementation" if k in d.get("continuing", []) else "2025"]],
                    "sections": [{"h": "About this entry", "p": s["paras"]}],
                    "also": also,
                    "sources": sources,
                },
            }
            if note:
                entry["note"] = note
            entries.append(entry)
        data["entries"][code] = entries

    for m in data["metrics"]:
        for i in m["indicators"]:
            if i["code"] in INDICATOR_NOTES:
                i["note"] = INDICATOR_NOTES[i["code"]]
                i["noteLabel"] = "Draft" if INDICATOR_NOTES[i["code"]].startswith("Draft") else "Free access"
    json.dump(data, open(DATA, "w", encoding="utf8"), ensure_ascii=False, indent=1)
    n = {k: len(v) for k, v in data["entries"].items()}
    print(n, "total", sum(n.values()))


if __name__ == "__main__":
    main()
