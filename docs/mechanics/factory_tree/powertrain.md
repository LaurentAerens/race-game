# Powertrain Department

The Powertrain department houses the Engine Dyno, ERS Hybrid Lab, and the pinnacle Works Engine Factory. These nodes are essential for T1 ENGINE and ERS development and provide large cross-cutting reliability and performance bonuses.

> [!NOTE]
> All Powertrain nodes require **Tier 1 (World Super Formula)** to unlock. In T2, ENGINE fine-tuning is handled by the Engine Tuning node in the Engineering department.

---

## Tree Structure

```
Engine Tuning (ENGINEERING, $9.5M)     ← Gateway
├── ERS Hybrid Lab ($9.5M)             → ERS R&D; ENGINE, ERS cross-mult
├── Engine Dyno Cells ($24M)           → ENGINE, ERS perf+rel
│   └── → Exotic Welding (MFG dept, $12M)
└── Works Engine Lab ($85M)            → In-House Works engine at $0/season
```

---

## Node Reference

### ERS Hybrid Lab
| Field | Value |
|-------|-------|
| Node ID | `eng_ers` |
| Build cost | $9,500,000 |
| Monthly upkeep | $260,000 × tier |
| Staff capacity | 12 / 24 / 36 |
| Prerequisite | R&D Workshop (Engineering) |
| Unlock tier | T1 only |
| Enables | ERS custom R&D |

High-voltage battery pack assembly, MGU-K and MGU-H performance maps. Must be at Tier ≥ 1 to earn any ERS knowledge from race telemetry. ERS is not available in T2 or T3 — this lab only matters once you reach World Super Formula.

---

### Engine Dyno Cells
| Field | Value |
|-------|-------|
| Node ID | `eng_dyno` |
| Build cost | $24,000,000 |
| Monthly upkeep | $650,000 × tier |
| Staff capacity | 16 / 32 / 48 |
| Prerequisite | Engine Tuning (Engineering) |
| Unlock tier | T1 only |
| Effect | ENG, ERS: +18%/tier Perf, +22%/tier Rel; ENGINE builds also get +1.5% Rel per tier (extra dyno boost) |

Transient dynamometers and stress testing cells. The single most powerful engine reliability facility in the game (+22% per tier). Also feeds the `dyno_extra` reliability bonus when building a new engine generation (+1.5 per tier directly on the built component). Gateway to Exotic Welding.

---

### Works Engine Lab
| Field | Value |
|-------|-------|
| Node ID | `eng_works_powertrain` |
| Build cost | $85,000,000 |
| Monthly upkeep | $2,400,000 × tier |
| Staff capacity | 35 / 70 / 105 |
| Prerequisite | Engine Tuning (Engineering) |
| Unlock tier | T1 only |
| Enables | "Works In-House V6 Turbo" engine option — $0 seasonal cost |

Full bespoke V6 Turbo and Works Power Unit construction capability. Building this unlocks the **Works In-House V6 Turbo** as a selectable engine supplier at no seasonal fee. The works engine starts at 600 HP but has uncapped development potential — over multiple seasons with STATUS_QUO regulations it can exceed 1,000+ HP.

> [!CAUTION]
> At $85M to build and $2.4M/month upkeep per tier, this is the most expensive node in the entire factory. It only pays off over multiple T1 seasons. Do not build it until your team is financially stable at the top level.

**Works In-House V6 Turbo specs (starting):**
| Stat | Value |
|------|-------|
| Seasonal cost | $0 |
| Base power | 600 HP |
| Fuel efficiency | 92.0 |
| Reliability | 85.0 |
| Philosophy | Unlimited evolution — best long-term ceiling |
