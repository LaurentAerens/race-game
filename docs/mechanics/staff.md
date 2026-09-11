# Staff System

---

## Hierarchy Overview

Each facility node has a defined staff structure:

| Role | Count |
|------|-------|
| Department Head | 1 per facility |
| Specialists (STAFF) | Up to 3 (T1) / 6 (T2) / 10 (T3) per facility |
| Intern (6-Month Tryout) | 1 per facility |
| Category Directors | 7 total (ENGINEERING, COMMERCIAL, TRACKSIDE, POWERTRAIN, MANUFACTURING, TESTING, HR) |
| Team Principal (CEO) | 1 |

---

## Stat Domains

Each department uses a primary stat for output calculations:

| Department | Primary Stat |
|-----------|-------------|
| ENGINEERING, POWERTRAIN | `stat_engineering` |
| MANUFACTURING, TESTING, TRACKSIDE | `stat_craftsmanship` |
| COMMERCIAL | `stat_marketing` |
| HR, other | `stat_communication` |

---

## Facility Output Calculation

Output is calculated as a `staff_mult` (0.0–5.0) through a layered formula:

**Step 1 — Coordination Rating:**
```
coordination = max(0.15, min(1.0, (head_leadership × 0.45 + avg_staff_leadership × 0.20 + avg_staff_communication × 0.35) / 100))
```

**Step 2 — Diminishing Returns Exponent (γ):**
```
γ = 0.55 − 0.40 × coordination_rating
```
Range: 0.55 (poor coordination) → 0.15 (elite coordination). A great head with good communication nearly eliminates diminishing returns.

**Step 3 — Per-specialist contribution:**
- Slot weight = `1.0 / (slot_index ^ γ)` — best staff sorted first
- `base_score = (effective_stat / 100) × composure_factor × morale_factor`
- `composure_factor = 0.90 + (stat_composure / 100) × 0.20`
- `morale_factor = max(0.40, min(1.15, morale / 100))`
- Specialty match: **1.50×** if the specialist's domain matches the facility; 1.00× otherwise
- Mentor penalty: **0.85×** if this specialist is mentoring the current intern

**Step 4 — Department Head multiplier:**
```
head_mult = 0.70 + (lead_factor × 0.40) + (head_domain_boost × 0.35)  →  range ~0.75× to 1.55×
```

**Step 5 — Category Director synergy:**
```
dir_mult = 0.85 + (director_leadership × 0.22) + (director_core_stat × 0.18)
```
A **vacant director slot** applies a **0.90× drag** on the entire department.

**Step 6 — Intern contribution:**
`+0.25 × intern_morale` (morale capped 0.5–1.1)

**Final:** `staff_mult = max(0.0, min(5.0, raw_staff_score × head_mult × dir_mult))`

> [!WARNING]
> Leaving a **Category Director seat vacant** applies a permanent 10% output penalty across that whole department until filled.

---

## Morale

Staff morale directly multiplies output (0.40× at minimum morale, 1.15× at maximum).

**Underpaid threshold:** `salary < market_value × (0.85 − 0.06 × teambuilding_tier)`
At max Teambuilding facility tier, the threshold drops to 65% of market value.

| Condition | Weekly morale change |
|-----------|---------------------|
| Underpaid | −2.5 × max(0.3, 1.0 − 0.22 × teambuilding_tier) (floor: 15.0) |
| Adequately paid | +1.0 + 2.0 × teambuilding_tier (cap: 100.0) |

---

## Stat Scouting (Fog of War)

Actual staff stats are hidden until you invest in the HR Performance Review facility:

| HR Review Tier | Stat uncertainty |
|----------------|-----------------|
| Not built (T0) | ±18 points |
| Tier 1 | ±10 points |
| Tier 2 | ±4 points |
| Tier 3 | Exact — 100% clarity |

---

## Weekly Training Bonuses (Facility Tiers)

| Facility | Stat boosted | Gain per week |
|---------|-------------|---------------|
| Tech Academy | `stat_engineering` (all staff) | +0.12 × tier |
| Craft Workshop | `stat_craftsmanship` (all staff) | +0.12 × tier |
| Craft Workshop | `stat_composure` (all staff) | +0.08 × tier |
| Leadership Institute | `leadership` (heads & directors) | +0.18 × tier |
| Leadership Institute | `communication` (heads & directors) | +0.14 × tier |
| Boardroom | `leadership` (all staff) | +0.15 × tier + equipment bonus |

---

## Intern Tryout (6-Month Programme)

- One intern slot per facility.
- The programme ticks **1 month per week** (6 weeks total).
- At graduation the intern receives: **+12 engineering, +12 craftsmanship, +12 marketing, +12 communication, +10 leadership, +10 composure** (all capped at 98).
- **Intern ratings:** ≥90 = STAR PRODIGY · ≥75 = SOLID PROSPECT · <75 = DEVELOPMENT TALENT
- The specialist assigned as mentor works at **85%** output during the mentoring period.
- With **HR Recruitment T2 + auto-pipeline policy**: if the intern result meets the minimum threshold, they are auto-signed for $2,000/month; otherwise auto-released.

---

## Management Boardroom — Leadership Aura

The Boardroom facility adds a flat leadership bonus to all staff:
```
mgmt_lead_bonus = boardroom_tier × 5.0  (capped at 100)
```
Equipment bonuses add on top: War Room +1.5/level, Executive Telemetry +1.0/level, Board Display +1.5/level.

---

## Automated HR Suites

Once unlocked, HR suites automate routine personnel tasks:

| Suite | Effect |
|-------|--------|
| Recruitment T1 | Auto-fills open specialist desks when budget surplus ≥ $2,500 |
| Recruitment T2 | Auto-assigns interns when budget surplus ≥ $2,000 |
| Payroll T1 | Auto-raises wages to market value when staff fall below 95% of market rate |
| Equipment Procurement T1 | Auto-upgrades equipment from department savings |
| Performance Cull T1 | Releases staff significantly below their age-curve expected skill |
| Workforce Optimizer T1 | Auto-replaces underperformers with better candidates at same/lower salary (+10 skill minimum) |

---

## Applicant Pool

- 15% chance per week of a new applicant appearing (if fewer than 4 applications are pending).
- New intern candidates: age 19–22, base stats 22–38, potential 62–85.
- 28% of new interns are prodigies with potential 90–98.
