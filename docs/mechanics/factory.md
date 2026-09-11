# Engineering & Factory

---

## Car Components

Your car has **7 custom components**, each with its own performance and durability ratings:

| Component | T3 R&D | T2 R&D | T1 R&D |
|-----------|--------|--------|--------|
| FRONT_WING | ✅ | ✅ | ✅ |
| REAR_WING | ❌ | ✅ | ✅ |
| BRAKES | ✅ | ✅ | ✅ |
| ENGINE | ❌ | ✅ (fine-tuning) | ✅ |
| SUSPENSION | ❌ | ✅ | ✅ |
| FLOOR | ❌ | ❌ | ✅ |
| ERS | ❌ | ❌ | ✅ |

**Baseline specs per tier** (approximate):

| Tier | Performance | Durability |
|------|-------------|-----------|
| T3 | 65–75 | 55–65 |
| T2 | 75–85 | 65–75 |
| T1 | 85–95 | 75–85 |

Components reset to the new tier baseline when you are promoted.

---

## Engine Suppliers

- You sign one **engine contract per season** — it is locked for the full season (~10 races).
- The contract sets your ENGINE component's **performance** and **reliability** values.
- At season end you must select a new supplier for the following season.

---

## In-Season R&D (Knowledge System)

Each component has a `knowledge_min` and `knowledge_max` range. R&D from telemetry, staff output, and innovation pitches expands these ranges, improving part performance.

AI teams receive in-season development every **3 race rounds** — they do not stand still.

---

## Next-Gen Chassis R&D

Each week you can allocate **0–80%** of your monthly engineering budget toward next-gen chassis development:

```
weekly_investment = (engineering_budget / 4) × (allocation_% / 100)
points_added = weekly_investment × fac_mult
fac_mult = 1.0 + (sum of relevant facility tiers × 0.08)
```

Accumulated points convert to projected car boosts:

| Boost | Formula |
|-------|---------|
| Performance | pts ÷ 25,000 |
| Reliability | (pts ÷ 30,000) × 1.2 |
| Tyre preservation | min(12.0, pts ÷ 20,000) |
| Fuel efficiency | min(10.0, pts ÷ 25,000) |

These boosts become your car for next season. Under **STATUS_QUO** regulations, they accumulate year-over-year. Under a regulation overhaul, only this season's earned boost survives.

---

## Port-Back Upgrade (Mid-Season)

A one-time option to push next-gen work onto your **current season car**:

- **Window:** Weeks 13–16 only
- **Condition:** Next season must be STATUS_QUO (no regulation changes)
- **Requirement:** At least 10,000 accumulated next-gen points
- **Effect:** Ports **2/3** of your accumulated performance + reliability boost to the current car immediately
- **Cooldown:** 2 weeks of factory lockdown (no R&D progress)
- **Recovery bonus:** 3 weeks of extra reliability: `5% × projected_reliability / 3` per week

This is a powerful mid-season surge tool but comes at the cost of lost development time.

---

## Facility Upgrades

Facilities amplify R&D output, staff quality, and many other systems.

| Upgrade tier | Cost formula |
|-------------|-------------|
| Initial build | base_cost × cost_mult |
| Upgrade to T2 | base_cost × 1.5 × cost_mult |
| Upgrade to T3+ | base_cost × 2.5 × cost_mult |

Some facilities have **unlock prerequisites**:
- Wind Tunnel requires Front Aero OR Rear Aero OR Aero Model Shop to be built first.
- Certain facilities only unlock after promotion to T2 or T1.

---

## Season Regulations

Announced at **Week 9**, regulations take effect next season. A regulation overhaul is triggered if **any one** of these conditions is met:

| Tier | Perf score threshold | Championship lead | Consecutive stable seasons |
|------|---------------------|------------------|---------------------------|
| T3 | > 3,000 | > 35% | 5 |
| T2 | > 6,500 | > 35% | 4 |
| T1 | > 15,000 | > 35% | 3 |

**Regulation packages and what they reset:**

| Package | Components reset |
|---------|----------------|
| MECHANICAL_TWEAKS | BRAKES, SUSPENSION |
| AERO_SHAKEUP | FRONT_WING, REAR_WING, FLOOR |
| POWERTRAIN_DIRECTIVE | ENGINE, ERS |
| MAJOR_OVERHAUL | All 7 components |
| STATUS_QUO | None — boosts accumulate |

> [!WARNING]
> If your team dominates (>35% championship lead), you risk triggering MAJOR_OVERHAUL which resets the entire field. Consider balancing development pace to avoid triggering it prematurely.

---

## Budget Deficit & Surplus

**Deficit:** The game automatically shuts down the lowest-ROI equipment, then lays off the lowest-skill staff to balance the books. Avoid persistent deficits.

**Surplus > $2,000:** Triggers automatic hiring of a new specialist and equipment upgrades if HR automation suites are enabled.
