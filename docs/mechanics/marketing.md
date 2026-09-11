# Sponsors & Commercial Revenue

---

## Sponsor Contracts

Sponsors are not classified into 4 tiers of made-up categories — the game uses three contract types: **STANDARD**, **PAY_DRIVER**, and **SPONSORED_DRIVER**. Contracts are measured in **seasons** (typically 1–5).

### Base Monthly Sponsor Retainer

This is the fixed tier-based retainer you receive regardless of results:

| Tier | Monthly Retainer |
|------|-----------------|
| T1 (World Super Formula) | $3,200,000 |
| T2 (Continental Championship) | $1,100,000 |
| T3 (National Open Cup) | $260,000 |
| T4 (Junior Talent F4) | $80,000 |
| T5 (Karting Academy) | $25,000 |

### Sponsor Appeal Score

The attractiveness of your team to sponsors is calculated as a composite **appeal score (0–100)** based on: tier championship points, recent form, historical titles, average driver marketability, and facility investment. A higher appeal score unlocks better sponsor contract values.

---

## Pay-Driver Sponsor Income

A **PAY_DRIVER** brings a sponsor to the team rather than drawing a salary. The weaker the driver (relative to tier benchmark), the larger the sponsorship:

```
deficiency_boost = max(1.0, 1.0 + ((base_skill − current_skill) / base_skill) × 1.5)
```

Income is then scaled by the tier's base pay-driver income rate. This is a cash-flow strategy — it sacrifices competitive performance for reliable weekly income.

---

## Commercial Revenue Streams

Beyond the base retainer, you can build commercial facilities that generate monthly income. All streams scale with your recent results and tier:

```
revenue = base_amount × facility_tier × perf_factor × tier_econ
```

| Stream | Base Amount | Extra Scaling |
|--------|-------------|---------------|
| Merchandise | $12,000 | — |
| Fan Club | $10,000 | × (avg_driver_marketability / 50) |
| Licensing | $8,000 | × (team_reputation / 50) |
| Museum / Heritage | $8,000 + titles × $10,000 | Uses max(0.5, perf_factor) |
| Customer Racing | $25,000 | — |

**perf_factor** = `max(0.15, min(1.35, 1.45 − avg_recent_pos × 0.10))`
Uses your last 5 race finishing positions. P1 every race = 1.35× multiplier; poor results can floor it at 0.15×.

**tier_econ:** T1 = 1.0 · T2 = 0.65 · T3 = 0.40 · T4 = 0.20 · T5 = 0.08

> [!TIP]
> Driver **marketability** directly multiplies Fan Club revenue. Improving it through media facilities, communications suites, and race wins compounds your commercial income.

### Commercial VIP Suite

The VIP Suite facility adds **+6% per tier** to performance bonus payouts from sponsor contracts.

---

## Promotion Income Escalator

Winning a championship and promoting to the next tier dramatically increases sponsor income:

- **T3 → T2:** Per-race sponsor income ≈ **×1.87**
- **T2 → T1:** Per-race sponsor income ≈ **×1.93**

Beyond prize money and champion bonuses ($2.5M royalty), the long-term income increase from promotion is one of the biggest financial rewards in the game.

---

## What Does Not Exist

> [!WARNING]
> The following mechanics do **not** exist in this game:
> - "Social Media Push", "TV Commercial", "Billboard", or "Fan Event" campaigns
> - A four-tier sponsor hierarchy (Title / Premium / Standard / Local)
> - A "Stability Modifier" affecting contracts
> - The ability to manually set a "contract length in race weekends"
>
> Commercial revenue grows through **facility upgrades** and **race results**, not one-off marketing campaigns.
