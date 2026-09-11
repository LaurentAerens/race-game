# Engineering Department

The Engineering department contains the dedicated R&D labs for each car component, plus aerodynamics and simulation tools. **This is the root of the entire factory tree** — nearly all other departments branch from nodes here.

---

## Tree Structure

```
R&D Workshop ($2.2M)                   ← ROOT
├── Brakes Lab ($1.8M)                  → BRAKES R&D
│   └── Thermal Flow Rig ($10M)         → ENGINE, ERS, BRK perf+rel
├── Front Aero Lab ($2.2M)              → FRONT_WING R&D  [Wind Tunnel prereq]
├── Rear Aero Lab ($7.5M)               → REAR_WING R&D   [Wind Tunnel prereq]
│   └── Aero Model Shop ($9.5M)         → aero cross-mult  [Wind Tunnel prereq]
├── Underbody Lab ($8M)                 → FLOOR R&D (T1 only)
├── Suspension Shop ($8.5M)             → SUSPENSION R&D
│   ├── → Kinematics Rig (TESTING dept, $12.5M)
│   └── → 5-Axis CNC Shop (MANUFACTURING dept, $11.5M)
├── Engine Tuning ($9.5M)              → ENGINE R&D (T2+)
│   ├── → Engine Dyno Cells (POWERTRAIN dept, $24M)
│   ├── → Works Engine Lab (POWERTRAIN dept, $85M)
│   └── → Electronics Lab (MANUFACTURING dept, $9.5M)
├── CAD Design Office ($7M)             → +5% R&D innovation success
│   ├── Materials Lab ($11M)            → SUSP, BRK perf+rel
│   └── CFD Supercluster ($14M)         → FW, RW, FLOOR aero cross-mult
│       └── Aero PIV Scanner ($20M)     → FW, RW, FLOOR aero cross-mult
├── Paint & Livery Bay ($7.5M)*         → slight perf boost on composites
└── Wind Tunnel ($38M)                  → FW, RW, FLOOR, SUSP, BRK cross-mult
    [Prereq: Front Aero OR Rear Aero OR Aero Model Shop]
```
*Paint & Livery Bay is tagged as MANUFACTURING department but has `eng_workshop` as parent.

---

## Node Reference

### R&D Workshop
| Field | Value |
|-------|-------|
| Node ID | `eng_workshop` |
| Build cost | $2,200,000 |
| Monthly upkeep | $75,000 × tier |
| Staff capacity | 12 / 24 / 36 |
| Prerequisite | None (root node) |

The entry point to the entire factory. Required before any other engineering or manufacturing facility can be built. Also contributes directly to R&D as a cross-cutting facility for all components.

---

### Brakes Lab
| Field | Value |
|-------|-------|
| Node ID | `eng_brakes` |
| Build cost | $1,800,000 |
| Monthly upkeep | $55,000 × tier |
| Staff capacity | 8 / 16 / 24 |
| Prerequisite | R&D Workshop |
| Enables | BRAKES custom R&D |

The dedicated facility for BRAKES development. Must be at Tier ≥ 1 to earn any BRAKES knowledge from race telemetry. Caliper bite, cooling discs, lockup resistance.

---

### Front Aero Lab
| Field | Value |
|-------|-------|
| Node ID | `eng_wings_front` |
| Build cost | $2,200,000 |
| Monthly upkeep | $65,000 × tier |
| Staff capacity | 10 / 20 / 30 |
| Prerequisite | R&D Workshop |
| Enables | FRONT_WING custom R&D; satisfies Wind Tunnel prereq |

Front wing cascade elements and ground clearance development.

---

### Rear Aero Lab
| Field | Value |
|-------|-------|
| Node ID | `eng_wings_rear` |
| Build cost | $7,500,000 |
| Monthly upkeep | $220,000 × tier |
| Staff capacity | 10 / 20 / 30 |
| Prerequisite | R&D Workshop |
| Enables | REAR_WING custom R&D; satisfies Wind Tunnel prereq |

Rear wing profiles, endplates, and DRS flap channels.

---

### Aero Model Shop
| Field | Value |
|-------|-------|
| Node ID | `eng_aero_model_shop` |
| Build cost | $9,500,000 |
| Monthly upkeep | $280,000 × tier |
| Staff capacity | 10 / 20 / 30 |
| Prerequisite | Rear Aero Lab |
| Enables | Satisfies Wind Tunnel prereq; +8%/tier on FW, RW, FLOOR telemetry |

Precision scale model workshop for wind tunnel correlation and aero verification.

---

### Underbody Lab
| Field | Value |
|-------|-------|
| Node ID | `eng_floor` |
| Build cost | $8,000,000 |
| Monthly upkeep | $220,000 × tier |
| Staff capacity | 12 / 24 / 36 |
| Prerequisite | R&D Workshop |
| Enables | FLOOR custom R&D (Tier 1 only) |

Venturi tunnel and ground-effect downforce development. FLOOR R&D is only unlocked in T1. The lab at T1 starts at entry capability; T2 and T3 are required for peak downforce levels.

---

### Suspension Shop
| Field | Value |
|-------|-------|
| Node ID | `eng_suspension` |
| Build cost | $8,500,000 |
| Monthly upkeep | $240,000 × tier |
| Staff capacity | 12 / 24 / 36 |
| Prerequisite | R&D Workshop |
| Enables | SUSPENSION custom R&D |

Mechanical grip, kerb ride, and tyre wear reduction. Gateway to Kinematics Rig (Testing) and CNC Shop (Manufacturing).

---

### Engine Tuning
| Field | Value |
|-------|-------|
| Node ID | `eng_tuning` |
| Build cost | $9,500,000 |
| Monthly upkeep | $260,000 × tier |
| Staff capacity | 10 / 20 / 30 |
| Prerequisite | R&D Workshop |
| Enables | ENGINE fine-tuning R&D (T2); gateway to Dyno & Works Factory |

ECU mapping and high-boost calibration. In T2 adds +1.5 to +4.5 HP per build (up to ~20 HP over a season). Also applies +15%/tier on ENGINE performance during telemetry, but with a −6%/tier reliability stress penalty. Gateway to Engine Dyno Cells, Works Engine Lab, and Electronics Lab.

---

### CAD Design Office
| Field | Value |
|-------|-------|
| Node ID | `eng_cad_office` |
| Build cost | $7,000,000 |
| Monthly upkeep | $200,000 × tier |
| Staff capacity | 10 / 20 / 30 |
| Prerequisite | R&D Workshop |
| Effect | +5%/tier to all innovation pitch success rates |

Structural stress FEA modeling and chassis packaging. One of the most cost-effective early investments if you intend to use creative innovation pitches.

---

### Materials Lab
| Field | Value |
|-------|-------|
| Node ID | `eng_comp_materials` |
| Build cost | $11,000,000 |
| Monthly upkeep | $320,000 × tier |
| Staff capacity | 10 / 20 / 30 |
| Prerequisite | CAD Design Office |
| Effect | SUSP, BRK: +15%/tier perf, +18%/tier rel |

Microstructures, custom carbon weaves, and exotic alloys. Best cross-cutting facility for mechanical components.

---

### CFD Supercluster
| Field | Value |
|-------|-------|
| Node ID | `eng_cfd` |
| Build cost | $14,000,000 |
| Monthly upkeep | $420,000 × tier |
| Staff capacity | 12 / 24 / 36 |
| Prerequisite | CAD Design Office |
| Effect | FW, RW, FLOOR: +12%/tier aero perf |

Virtual airflow simulation for aerodynamic surfaces. Very high return on investment for aero parts.

---

### Aero PIV Scanner
| Field | Value |
|-------|-------|
| Node ID | `eng_aero_scanning` |
| Build cost | $20,000,000 |
| Monthly upkeep | $550,000 × tier |
| Staff capacity | 12 / 24 / 36 |
| Prerequisite | CFD Supercluster |
| Effect | FW, RW, FLOOR: +10%/tier aero perf |

Particle Image Velocimetry and laser boundary layer mapping. Stacks multiplicatively with CFD.

---

### Thermal Flow Rig
| Field | Value |
|-------|-------|
| Node ID | `eng_thermal_rig` |
| Build cost | $10,000,000 |
| Monthly upkeep | $290,000 × tier |
| Staff capacity | 10 / 20 / 30 |
| Prerequisite | Brakes Lab |
| Effect | ENG, ERS, BRK: +11%/tier perf, +12%/tier rel |

Internal radiator airflow and brake duct thermal dissipation. Cross-cuts three components.

---

### Wind Tunnel
| Field | Value |
|-------|-------|
| Node ID | `eng_windtunnel` |
| Build cost | $38,000,000 |
| Monthly upkeep | $950,000 × tier |
| Staff capacity | 18 / 36 / 54 |
| Prerequisite | Front Aero Lab **OR** Rear Aero Lab **OR** Aero Model Shop |
| Effect | FW, RW, FLOOR, SUSP, BRK: +8%/tier perf; +8%/tier innovation success |

The most expensive engineering node. Cross-affects **five** components simultaneously. Also boosts innovation pitch success chance by +8% per tier. Requires any one of three aero nodes first — it does not need all three.
