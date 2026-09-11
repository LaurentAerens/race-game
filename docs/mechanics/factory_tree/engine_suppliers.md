# Engine Suppliers

You sign one engine contract per season — it locks your ENGINE component's performance and reliability for the full season (~10 races). At season end, you choose a new supplier.

---

## Tier 3 Suppliers (National Open Cup)

| Supplier | Philosophy | Season Cost | Power | Fuel Efficiency | Reliability |
|----------|-----------|------------|-------|----------------|-------------|
| **Vortex EcoTech** | Entry budget & fuel efficiency | $250,000 | 70.0 | 95.0 | 88.0 |
| **AeroStar Endurance** | Bulletproof reliability & safe points | $800,000 | 76.0 | 88.0 | 95.0 |
| **Titan Velocity** | Maximum peak horsepower | $1,200,000 | 82.0 | 74.0 | 72.0 |

> [!TIP]
> **Vortex EcoTech** is the best T3 value for a cash-strapped early season. **AeroStar Endurance** is better if reliability retirements are killing your points. **Titan Velocity** gives the most raw pace but the 72.0 reliability means regular DNF risk — only worth it if your QA & NDT Lab is developed.

---

## Tier 2 Suppliers (Continental Championship)

| Supplier | Philosophy | Season Cost | Power | Fuel Efficiency | Reliability |
|----------|-----------|------------|-------|----------------|-------------|
| **CosmoSpec Customer V6** | Post-promotion survival budget unit | $1,200,000 | 310.0 | 90.0 | 86.0 |
| **AeroTorque Endurance V6** | High thermal efficiency & extreme reliability | $4,500,000 | 350.0 | 88.0 | 94.0 |
| **Apex High-Rev V8** | High-RPM aggressive performance | $8,500,000 | 395.0 | 80.0 | 82.0 |

> [!TIP]
> **CosmoSpec** is the immediate post-promotion choice while your finances stabilize. **AeroTorque** is the best all-round T2 engine. **Apex V8** has the highest ceiling but lower reliability and fuel efficiency — budget the extra fuel burn when calculating race strategy.

---

## Tier 1 Suppliers (World Super Formula)

| Supplier | Philosophy | Season Cost | Power | Fuel Efficiency | Reliability |
|----------|-----------|------------|-------|----------------|-------------|
| **Formula Standard Customer V6** | Post-promotion baseline customer unit | $5,000,000 | 710.0 | 90.0 | 88.0 |
| **Solaris Quantum Hybrid V6** | Elite midfield customer hybrid | $35,000,000 | 765.0 | 92.0 | 92.0 |
| **Scuderia Factory Hyper-V6** | Pinnacle world championship engine | $65,000,000 | 810.0 | 94.0 | 94.0 |
| **Works In-House V6 Turbo** ⭐ | Full bespoke works unit (unlimited evolution) | **$0** | 600.0 (start) | 92.0 | 85.0 |

> [!IMPORTANT]
> **Works In-House V6 Turbo** requires the **Works Engine Lab** facility (`eng_works_powertrain`, $85M to build) and is Tier 1 exclusive. It starts at 600 HP — weaker than all customer suppliers — but has **uncapped development potential** through in-house R&D. Over multiple STATUS_QUO seasons it can exceed 1,000+ HP at zero annual cost.

---

## Contract Rules

- The contract is **locked for the full season** once signed. You cannot swap mid-season.
- At season end, re-negotiation is required — you must pick a supplier again.
- The contract deducts from your cash immediately on signing.
- The selected engine sets the starting values of your ENGINE component's `performance` and `reliability`.
- In-season Engine Tuning (T2) and Works R&D (T1) can add on top of these base values through builds.
