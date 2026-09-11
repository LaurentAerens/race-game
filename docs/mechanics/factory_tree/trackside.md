# Trackside Department

The Trackside department covers everything that happens at the race circuit: pit stop equipment, live telemetry, rival intelligence, weather forecasting, and setup analytics. It is the cheapest department to start and delivers the most immediate race-day impact.

---

## Tree Structure

```
Pit Practice Rig ($2.2M)                ← ROOT
├── Carbon Guns ($12.5M)                → pit stop time reduction
│   └── Rapid Repair Gantry ($13.5M)   → wing swap & repair time
│       └── Active Jack & Release ($21M) → sub-2.0s stops
└── Track Telemetry ($9.8M)
    ├── Paddock Recon Unit ($11.5M)     → competitor intelligence pitches
    │   └── Optical Telemetry Intercept ($19M) → +35% reverse-engineering
    ├── Doppler Weather Radar ($12M)    → extended rain forecast
    ├── Setup Analytics ($15M)          → recommended setup ranges in FP
    │   └── Virtual FP Solver ($26M)   → pre-weekend synthetic laps
    └── Factory Mission Control ($22M) → +15% all-part telemetry
```

---

## Node Reference

### Pit Practice Rig
| Field | Value |
|-------|-------|
| Node ID | `track_pitrig` |
| Build cost | $2,200,000 |
| Monthly upkeep | $68,000 × tier |
| Staff capacity | 14 / 28 / 42 |
| Prerequisite | None (root node) |

Basic 12-man pit crew reaction and coordination training. Reduces the `base_stop_reduction` used in the pit stop timing formula. **This is the single highest-ROI early purchase** — every fraction of a second saved compounds over a full season. Should be bought on Week 1.

---

### Carbon Guns
| Field | Value |
|-------|-------|
| Node ID | `track_wheelguns` |
| Build cost | $12,500,000 |
| Monthly upkeep | $360,000 × tier |
| Staff capacity | 18 / 36 / 54 |
| Prerequisite | Pit Practice Rig |

Motorised titanium wheel guns with laser nut alignment, targeting 2.1-second stops. Large reduction to base stop time; also boosts innovation success for competitor intelligence pitches (+1.5%/tier).

---

### Rapid Repair Gantry
| Field | Value |
|-------|-------|
| Node ID | `track_fast_repair` |
| Build cost | $13,500,000 |
| Monthly upkeep | $390,000 × tier |
| Staff capacity | 12 / 24 / 36 |
| Prerequisite | Carbon Guns |

Sub-2.5s front wing swaps and rapid composite bonding. Reduces the **Emergency Repairs** box time penalty (normally +14.0s) by 50%. Essential if you frequently need repair stops.

---

### Active Jack & Release
| Field | Value |
|-------|-------|
| Node ID | `track_jack_release` |
| Build cost | $21,000,000 |
| Monthly upkeep | $580,000 × tier |
| Staff capacity | 14 / 28 / 42 |
| Prerequisite | Rapid Repair Gantry |

Sub-0.2s pneumatic lifting and automated green-light traffic gantry. Targets sub-2.0s total base stop times. The pinnacle of pit stop speed investment.

---

### Track Telemetry
| Field | Value |
|-------|-------|
| Node ID | `track_telemetry` |
| Build cost | $9,800,000 |
| Monthly upkeep | $280,000 × tier |
| Staff capacity | 8 / 16 / 24 |
| Prerequisite | Pit Practice Rig |

High-accuracy live weather and race telemetry. Also boosts competitor intelligence pitch success (+3%/tier). Gateway to rival intel, weather radar, setup analytics, and factory mission control. A critical hub node — unlock it to open the rest of the trackside tree.

---

### Paddock Recon Unit
| Field | Value |
|-------|-------|
| Node ID | `track_rival_intel` |
| Build cost | $11,500,000 |
| Monthly upkeep | $330,000 × tier |
| Staff capacity | 10 / 20 / 30 |
| Prerequisite | Track Telemetry |

Trackside rival intelligence gathering — acoustic listening arrays and optical observation. Increases competitor intelligence pitch roll rate (+40%) and success chance (+6%/tier). The most powerful node for generating competitor intelligence pitches consistently.

---

### Optical Telemetry Intercept
| Field | Value |
|-------|-------|
| Node ID | `track_reverse_eng` |
| Build cost | $19,000,000 |
| Monthly upkeep | $520,000 × tier |
| Staff capacity | 12 / 24 / 36 |
| Prerequisite | Paddock Recon Unit |

Pit-straight dynamic LIDAR ride height profiling. Adds +5%/tier to competitor intelligence success chance. Also reduces competitor intelligence pitch lockout duration by 1 week at Tier 2.

---

### Doppler Weather Radar
| Field | Value |
|-------|-------|
| Node ID | `track_weather_station` |
| Build cost | $12,000,000 |
| Monthly upkeep | $350,000 × tier |
| Staff capacity | 8 / 16 / 24 |
| Prerequisite | Track Telemetry |

Dual-polarization mobile radar. When installed, the broadcast header shows the `[DOPPLER]` tag and a cyan border on the weather panel. Extends the rain forecast bars: minimum 6 laps shown, up to 10 based on `radar_tier + radar_eq_lvl`. Essential for wet-weather strategy.

---

### Setup Analytics
| Field | Value |
|-------|-------|
| Node ID | `track_setup_telemetry` |
| Build cost | $15,000,000 |
| Monthly upkeep | $420,000 × tier |
| Staff capacity | 10 / 20 / 30 |
| Prerequisite | Track Telemetry |

Dynamic ride height and damper telemetry providing recommended setup ranges during Free Practice. Improves setup confidence seeding for qualifying and race. Gateway to the Virtual FP Solver.

---

### Virtual FP Solver
| Field | Value |
|-------|-------|
| Node ID | `track_virtual_sim` |
| Build cost | $26,000,000 |
| Monthly upkeep | $720,000 × tier |
| Staff capacity | 12 / 24 / 36 |
| Prerequisite | Setup Analytics |

Runs 10,000 synthetic pre-weekend laps, ensuring FP1 starts significantly closer to an optimal setup. Reduces the gap between practice plan confidence and real-world performance. The most expensive trackside node — buy it once you have the pit stop chain fully developed.

---

### Factory Mission Control
| Field | Value |
|-------|-------|
| Node ID | `track_comm_uplink` |
| Build cost | $22,000,000 |
| Monthly upkeep | $600,000 × tier |
| Staff capacity | 12 / 24 / 36 |
| Prerequisite | Track Telemetry |

10,000Hz satellite telemetry uplink between trackside and factory. Applies a multiplier to **all post-race knowledge gains** across all 7 components:
- Performance knowledge: +15% per tier
- Reliability knowledge: +12% per tier

This is a flat global multiplier — every component benefits from every race, compounding across a full season.
