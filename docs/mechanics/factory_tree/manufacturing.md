# Manufacturing Department

The Manufacturing department covers composite construction, metal machining, electronics, and finishing. Nodes here act as **cross-cutting multipliers** on telemetry knowledge — they do not replace dedicated component labs but stack multiplicatively on top of them.

> [!NOTE]
> All Manufacturing nodes require **Tier 1 (World Super Formula)** to unlock. These are late-game investments.

---

## Tree Structure

```
R&D Workshop (ENGINEERING root)
├── Autoclave Suite ($10.5M)           → FW, RW, FLOOR, SUSP perf/rel
│   ├── Pre-Preg Freezers ($8.5M)      → sub-zero carbon storage
│   │   └── Monocoque Jig ($21M)       → structural rigidity for chassis builds
│   │       └── → Torsional Rig (TESTING dept, $16M)
│   └── Rapid Tooling ($10M)           → master composite molds for all aero
├── Paint & Livery Bay ($7.5M)         → slight perf boost on composites
└── Engine Tuning (ENGINEERING)
    ├── Electronics Lab ($9.5M)         → ENG, ERS perf/rel
    │   └── → QA & NDT Lab (TESTING dept, $9M)
    └── Engine Dyno Cells (POWERTRAIN)
        └── Exotic Welding ($12M)       → ENG, ERS perf/rel

Suspension Shop (ENGINEERING)
└── 5-Axis CNC Shop ($11.5M)           → SUSP, BRK, ENG perf
    ├── Rapid Prototyping ($11M)        → +8% innovation success
    └── Metal 3D Printing ($18M)        → SUSP, BRK, ERS perf
```

---

## Node Reference

### Autoclave Suite
| Field | Value |
|-------|-------|
| Node ID | `mfg_cleanroom_autoclave` |
| Build cost | $10,500,000 |
| Monthly upkeep | $300,000 × tier |
| Staff capacity | 14 / 28 / 42 |
| Prerequisite | R&D Workshop |
| Unlock tier | T1 only |
| Effect | FW, RW, FLOOR, SUSP: +12%/tier Perf; −5%/tier Rel (lightweighting strain) |

Carbon pre-preg layup and lightweight composite chassis. The performance gain is high but it does reduce composite component reliability slightly. The QA & NDT Lab (Testing) counteracts this reliability penalty.

---

### Pre-Preg Freezers
| Field | Value |
|-------|-------|
| Node ID | `mfg_prepreg_freezer` |
| Build cost | $8,500,000 |
| Monthly upkeep | $240,000 × tier |
| Staff capacity | 10 / 20 / 30 |
| Prerequisite | Autoclave Suite |
| Unlock tier | T1 only |

Sub-zero climate-controlled carbon roll storage and CNC ultrasonic ply cutting. Prerequisite for the Monocoque Jig.

---

### Monocoque Jig
| Field | Value |
|-------|-------|
| Node ID | `mfg_monocoque_jig` |
| Build cost | $21,000,000 |
| Monthly upkeep | $580,000 × tier |
| Staff capacity | 14 / 28 / 42 |
| Prerequisite | Pre-Preg Freezers |
| Unlock tier | T1 only |

Ground-anchored steel alignment jigs for carbon safety cell bonding. Gateway to the Torsional Rig (Testing dept).

---

### Rapid Tooling
| Field | Value |
|-------|-------|
| Node ID | `mfg_rapid_tooling` |
| Build cost | $10,000,000 |
| Monthly upkeep | $280,000 × tier |
| Staff capacity | 12 / 24 / 36 |
| Prerequisite | Autoclave Suite |
| Unlock tier | T1 only |

High-speed dense foam routers creating master composite molds for all aero surfaces. Cross-cutting benefit to FW and RW component builds.

---

### Paint & Livery Bay
| Field | Value |
|-------|-------|
| Node ID | `mfg_paint_bay` |
| Build cost | $7,500,000 |
| Monthly upkeep | $210,000 × tier |
| Staff capacity | 8 / 16 / 24 |
| Prerequisite | R&D Workshop |
| Unlock tier | T1 only |
| Effect | FW, RW, FLOOR, SUSP: +8%/tier Perf; −3%/tier Rel |

Specialized boundary-layer topcoats and lightweight liveries. Small performance boost on composite parts at a slight reliability cost.

---

### 5-Axis CNC Shop
| Field | Value |
|-------|-------|
| Node ID | `mfg_cnc_machining` |
| Build cost | $11,500,000 |
| Monthly upkeep | $330,000 × tier |
| Staff capacity | 14 / 28 / 42 |
| Prerequisite | Suspension Shop (Engineering) |
| Unlock tier | T1 only |
| Effect | SUSP, BRK, ENG: +10%/tier Perf |

5-axis milling of suspension uprights, wishbones, and solid alloy components. Gateway to Rapid Prototyping and Metal 3D Printing.

---

### Rapid Prototyping
| Field | Value |
|-------|-------|
| Node ID | `mfg_rapid_proto` |
| Build cost | $11,000,000 |
| Monthly upkeep | $310,000 × tier |
| Staff capacity | 10 / 20 / 30 |
| Prerequisite | 5-Axis CNC Shop |
| Unlock tier | T1 only |
| Effect | +8%/tier to creative invention success chance |

Additive manufacturing of scaled test parts for rapid design iteration. One of the highest innovation success-rate bonuses in the game, second only to QA & NDT Lab.

---

### Metal 3D Printing
| Field | Value |
|-------|-------|
| Node ID | `mfg_additive_metal` |
| Build cost | $18,000,000 |
| Monthly upkeep | $500,000 × tier |
| Staff capacity | 12 / 24 / 36 |
| Prerequisite | 5-Axis CNC Shop |
| Unlock tier | T1 only |
| Effect | SUSP, BRK, ERS: +9%/tier Perf |

Direct metal laser sintering of hollow titanium and Inconel components.

---

### Electronics Lab
| Field | Value |
|-------|-------|
| Node ID | `mfg_electronics` |
| Build cost | $9,500,000 |
| Monthly upkeep | $270,000 × tier |
| Staff capacity | 10 / 20 / 30 |
| Prerequisite | Engine Tuning (Engineering) |
| Unlock tier | T1 only |
| Effect | ENG, ERS: +14%/tier Perf, +15%/tier Rel |

MIL-SPEC sealed looms, ECUs, sensor arrays, and telemetry hardware. Strongest reliability booster for powertrain components alongside the Dyno. Gateway to QA & NDT Lab (Testing).

---

### Exotic Welding
| Field | Value |
|-------|-------|
| Node ID | `mfg_exotic_welding` |
| Build cost | $12,000,000 |
| Monthly upkeep | $340,000 × tier |
| Staff capacity | 10 / 20 / 30 |
| Prerequisite | Engine Dyno Cells (Powertrain) |
| Unlock tier | T1 only |
| Effect | ENG, ERS: +13%/tier Perf, +14%/tier Rel |

Argon-purged cleanrooms for paper-thin Inconel exhaust manifolds. Stacks with Electronics Lab and Dyno for comprehensive powertrain reliability.
