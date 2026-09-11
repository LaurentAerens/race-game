# Factory Tree — Overview

Your factory is divided into **9 departments**. Each department contains a tree of facility nodes you unlock and upgrade from Tier 1 to Tier 3.

---

## Upgrade Cost Formula

| Action | Cost |
|--------|------|
| Build (T1) | `base_cost` |
| Upgrade to T2 | `base_cost × 1.5` |
| Upgrade to T3 | `base_cost × 2.5` |
| Monthly upkeep | `base_upkeep × current_tier` |

Costs scale with your difficulty setting (`cost_mult`). Factory costs are **not** affected by difficulty on Normal — only income and development gains are.

---

## Facility Tier Effect on R&D

Every dedicated component facility has a tier multiplier on telemetry knowledge gain:

| Tier | Knowledge gain multiplier |
|------|--------------------------|
| T0 (not built) | **0× — no R&D progress on that component** |
| T1 | 1.00× |
| T2 | 1.65× |
| T3 | 2.30× |

> [!IMPORTANT]
> If the dedicated facility for a component is not built, **that component earns zero knowledge per race**. This is the primary reason to build facilities early.

---

## Departments at a Glance

| Department | Entry node | Starting cost | What it does |
|-----------|-----------|--------------|--------------|
| [Engineering](engineering.md) | R&D Workshop | $2.2M | Core component R&D labs for all 7 car parts |
| [Manufacturing](manufacturing.md) | Autoclave Suite | $10.5M | Carbon layup, CNC machining, composite construction |
| [Powertrain](powertrain.md) | Engine Tuning → Dyno | $24M | Engine R&D, ERS lab, works power unit |
| [Testing](testing.md) | Kinematics Rig | $12.5M | Dynamic rigs, QA, structural testing |
| [Trackside](trackside.md) | Pit Practice Rig | $2.2M | Pit stops, telemetry, weather, rival intel |
| [Driver Performance](driver.md) | Driver Sim Rig | $2.3M | Driver development, academy, physio |
| [Commercial](commercial.md) | Press & PR Office | $2.4M | Sponsor appeal, fan revenue streams |
| [HR](hr.md) | Recruitment Bureau | $4.5M | Staff automation, training, morale |
| [Management](management.md) | Executive Boardroom | $2.6M | Global leadership aura for all staff |

---

## Cross-Cutting Facility Effects on Components

Multiple facilities influence R&D across departments. Here is the full cross-reference:

| Facility | Components boosted (Perf) | Components boosted (Rel) |
|----------|--------------------------|--------------------------|
| Wind Tunnel | FW, RW, FLOOR, SUSP, BRK (+8%/tier) | — |
| CFD Supercluster | FW, RW, FLOOR (+12%/tier) | — |
| Aero PIV Scanner | FW, RW, FLOOR (+10%/tier) | — |
| Aero Model Shop | FW, RW, FLOOR (+8%/tier) | — |
| Autoclave Suite | FW, RW, FLOOR, SUSP (+12%/tier) | FW, RW, FLOOR, SUSP (−5%/tier — lightweighting strain) |
| Paint & Livery Bay | FW, RW, FLOOR, SUSP (+8%/tier) | FW, RW, FLOOR, SUSP (−3%/tier) |
| Materials Lab | SUSP, BRK (+15%/tier) | SUSP, BRK (+18%/tier) |
| Kinematics Rig | SUSP, BRK (+12%/tier) | — |
| 7-Post Shaker Rig | SUSP, BRK (+15%/tier) | — |
| Torsional Rig | FW, RW, FLOOR (−2%/tier) | SUSP, FLOOR (+14%/tier) |
| 5-Axis CNC Shop | SUSP, BRK, ENG (+10%/tier) | — |
| Metal 3D Printing | SUSP, BRK, ERS (+9%/tier) | — |
| Engine Dyno Cells | ENG, ERS (+18%/tier) | ENG, ERS (+22%/tier) |
| Electronics Lab | ENG, ERS (+14%/tier) | ENG, ERS (+15%/tier) |
| Exotic Welding | ENG, ERS (+13%/tier) | ENG, ERS (+14%/tier) |
| Thermal Flow Rig | ENG, ERS, BRK (+11%/tier) | ENG, ERS, BRK (+12%/tier) |
| QA & NDT Lab | All 7 (−4%/tier Perf) | All 7 (+35%/tier Rel — massive reliability gain) |
| Factory Mission Control | All 7 (+15%/tier Perf) | All 7 (+12%/tier Rel) |
| Engine Tuning | ENG (+15%/tier extra) | ENG (−6%/tier — thermal stress) |

> [!TIP]
> The **QA & NDT Lab** is the single best reliability facility in the game: +35% reliability per tier across all 7 components. The slight performance penalty (−4%/tier) is almost always worth it.
