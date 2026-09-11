# HR Department

The HR department automates personnel management and runs training programmes that improve staff stats over time. Good HR reduces the overhead of managing dozens of staff members and keeps morale high.

---

## Tree Structure

```
Recruitment Bureau ($4.5M, max T2)     ← ROOT
├── Payroll Calibration ($6M)          → auto-raise wages
│   └── Rig Procurement ($11M)         → auto-upgrade equipment
├── Executive Headhunting ($8.5M)      → rival team talent poaching
├── Culture & Welfare ($9M)            → morale threshold buffer
│   └── Longevity Center ($13.5M)      → staff peak age extension
├── Performance Analytics ($10.5M)    → stat scouting clarity
│   ├── Talent Exit Review ($7.5M)     → auto-cull underperformers
│   │   └── Succession Optimizer ($19M) → auto-replace underperformers
│   ├── Craft Guild ($14M)             → craftsmanship + composure training
│   └── Tech R&D Academy ($16M)        → engineering stat training
└── Leadership Institute ($12M)        → leadership + communication training
```

---

## Node Reference

### Recruitment Bureau
| Field | Value |
|-------|-------|
| Node ID | `hr_recruitment` |
| Build cost | $4,500,000 |
| Monthly upkeep | $130,000 × tier |
| Staff capacity | 6 / 12 |
| Max tier | **T2 only** |
| Effect | T1: auto-fill open specialist desks if budget surplus ≥ $2,500 / T2: auto-assign interns if surplus ≥ $2,000 |

The root of all HR automation. Note this node caps at **Tier 2** — you cannot upgrade it to T3. Its main value is automating hiring at both specialist and intern levels.

---

### Payroll Calibration
| Field | Value |
|-------|-------|
| Node ID | `hr_payroll` |
| Build cost | $6,000,000 |
| Monthly upkeep | $170,000 × tier |
| Staff capacity | 6 / 12 / 18 |
| Prerequisite | Recruitment Bureau |
| Effect | Auto-raises staff wages to market value when they fall below 95% of market rate |

Prevents morale loss from underpayment without manual intervention each week. At T1, wages are automatically adjusted. Gateway to Rig Procurement.

---

### Rig Procurement
| Field | Value |
|-------|-------|
| Node ID | `hr_equipment_procurement` |
| Build cost | $11,000,000 |
| Monthly upkeep | $310,000 × tier |
| Staff capacity | 10 / 20 / 30 |
| Prerequisite | Payroll Calibration |
| Effect | Auto-upgrades equipment using accumulated department savings |

The HR system monitors department surpluses and automatically purchases equipment upgrades prioritised by ROI. Frees you from manually tracking every equipment upgrade across all facilities.

---

### Executive Headhunting
| Field | Value |
|-------|-------|
| Node ID | `hr_headhunting` |
| Build cost | $8,500,000 |
| Monthly upkeep | $240,000 × tier |
| Staff capacity | 8 / 16 / 24 |
| Prerequisite | Recruitment Bureau |
| Effect | Boosts `hr_quality_mult` used in autonomous hiring decisions; scouts rival paddock for better candidates |

Improves the skill level of autonomously hired staff: `new_skill = min(92, 45 + 8×tier + 5×hr_quality_mult + rand(-3,6))`. Higher HR quality means better auto-hired specialists.

---

### Culture & Welfare
| Field | Value |
|-------|-------|
| Node ID | `hr_teambuilding` |
| Build cost | $9,000,000 |
| Monthly upkeep | $260,000 × tier |
| Staff capacity | 8 / 16 / 24 |
| Prerequisite | Recruitment Bureau |
| Effect | Lowers the underpaid morale threshold: `threshold = 0.85 − 0.06 × teambuilding_tier` (min 0.65 at T3). Also accelerates morale recovery: `morale += 1.0 + 2.0 × teambuilding_tier` per week when adequately paid. |

At T3, the underpaid threshold drops to 65% of market rate — staff will not lose morale unless paid below 65% of their market wage. Also speeds morale recovery from `+1.0` to `+7.0` per week for adequately-paid staff.

---

### Longevity Center
| Field | Value |
|-------|-------|
| Node ID | `hr_wellness_center` |
| Build cost | $13,500,000 |
| Monthly upkeep | $380,000 × tier |
| Staff capacity | 10 / 20 / 30 |
| Prerequisite | Culture & Welfare |
| Effect | Extends staff peak performance age to 54 and reduces post-50 stat degradation by 60% |

The staff equivalent of the Physio Clinic for drivers. Keeps high-skill veteran staff productive for longer — particularly useful for elite department heads who are difficult to replace.

---

### Performance Analytics
| Field | Value |
|-------|-------|
| Node ID | `hr_performance_review` |
| Build cost | $10,500,000 |
| Monthly upkeep | $300,000 × tier |
| Staff capacity | 10 / 20 / 30 |
| Prerequisite | Recruitment Bureau |
| Effect — Stat Clarity | T0: ±18 pts uncertainty / T1: ±10 pts / T2: ±4 pts / T3: exact |

Removes the fog-of-war on staff stats. At T3 you see exact numbers. This is essential for making informed hiring decisions and knowing which specialists are actually your best performers. Gateway to the training facilities and cull nodes.

---

### Talent Exit Review
| Field | Value |
|-------|-------|
| Node ID | `hr_performance_cull` |
| Build cost | $7,500,000 |
| Monthly upkeep | $210,000 × tier |
| Staff capacity | 8 / 16 / 24 |
| Prerequisite | Performance Analytics |
| Effect | Auto-releases staff whose skill falls significantly below the age-curve bell-curve expectation (peaks at age 50, sigma=14, peak=75) |

Automated trimming of underperformers. Works alongside Succession Optimizer for a full auto-replacement pipeline.

---

### Succession Optimizer
| Field | Value |
|-------|-------|
| Node ID | `hr_workforce_optimizer` |
| Build cost | $19,000,000 |
| Monthly upkeep | $520,000 × tier |
| Staff capacity | 12 / 24 / 36 |
| Prerequisite | Talent Exit Review |
| Effect | Auto-replaces underperformers with superior candidates at the same or lower salary (+10 skill minimum) |

The full automation pipeline for staff quality. Combined with Headhunting and Performance Analytics, your team continuously improves its average staff skill without manual intervention.

---

### Leadership Institute
| Field | Value |
|-------|-------|
| Node ID | `hr_leadership_institute` |
| Build cost | $12,000,000 |
| Monthly upkeep | $340,000 × tier |
| Staff capacity | 10 / 20 / 30 |
| Prerequisite | Recruitment Bureau |
| Effect | Weekly: `+0.18 × tier` to `leadership`; `+0.14 × tier` to `communication` (Department Heads and Category Directors only) |

Targeted leadership development for your management tier. Leadership directly controls the `coordination_rating` and `head_mult` in the facility output formula — improving it reduces diminishing returns and amplifies every specialist's contribution.

---

### Craft Guild
| Field | Value |
|-------|-------|
| Node ID | `hr_craft_workshop` |
| Build cost | $14,000,000 |
| Monthly upkeep | $390,000 × tier |
| Staff capacity | 10 / 20 / 30 |
| Prerequisite | Performance Analytics |
| Effect | Weekly: `+0.12 × tier` to `stat_craftsmanship`; `+0.08 × tier` to `stat_composure` for all staff |

Training programme for manufacturing and testing staff. Composure directly affects output: `composure_factor = 0.90 + (stat_composure / 100) × 0.20`.

---

### Tech R&D Academy
| Field | Value |
|-------|-------|
| Node ID | `hr_tech_academy` |
| Build cost | $16,000,000 |
| Monthly upkeep | $440,000 × tier |
| Staff capacity | 12 / 24 / 36 |
| Prerequisite | Performance Analytics |
| Effect | Weekly: `+0.12 × tier` to `stat_engineering` for all staff |

Engineering skill development programme. Benefits all ENGINEERING and POWERTRAIN department staff, raising the primary stat that drives their output in R&D facilities.
