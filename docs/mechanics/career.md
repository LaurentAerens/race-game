# Career Mode

---

## Season Structure

Each season lasts **18 weeks**. You start as team principal of **Horizon Racing** in **Tier 3 (National Open Cup)**. Your goal is to build the team, win races, and climb the tier ladder.

Key calendar events:

| Timing | Event |
|--------|-------|
| Week 9 | Next season's regulations announced |
| Weeks 13–16 | Port-back upgrade window (see Factory) |
| Season finale | Promotion/relegation resolved, champion bonuses paid |

---

## Promotion & Relegation

| Outcome | Condition | Effect |
|---------|-----------|--------|
| T3 → T2 promotion | Win T3 championship | Player may decline. Car resets to T2 baseline specs. |
| T2 → T1 promotion | Win T2 championship | Player may decline. Car resets to T1 baseline specs. |
| T2 → T3 relegation | T2 last place (P10) | Team gets relegated titan boost (1.4× R&D, starts at 72.0 perf) |
| T1 → T2 relegation | T1 last place | Team starts at 92.0 performance, also has titan boost |

**Relegated teams** (`is_relegated_titan`) start slightly weaker but develop aggressively — they begin the season -3.5 score behind benchmark and catch up to +10 by season end.

> [!NOTE]
> A "lifeline" flag is shown if the player finishes P10 in T3, but there is no forced player relegation from T3.

### Sponsor Income Escalator on Promotion

Winning a championship and promoting significantly boosts sponsor income:

- **T3 → T2:** Per-race sponsor income ≈ **×1.87**
- **T2 → T1:** Per-race sponsor income ≈ **×1.93**

---

## Financial Systems

### Monthly Revenue

| Source | Formula |
|--------|---------|
| Base sponsor retainer | T1: $3.2M / T2: $1.1M / T3: $260k / T4: $80k / T5: $25k |
| Pay-driver sponsor income | Varies by driver deficiency (weaker driver = more income) |
| Merchandise | $12,000 × merch_tier × perf_factor × tier_econ |
| Fan Club | $10,000 × fc_tier × perf_factor × tier_econ × (avg_marketability / 50) |
| Licensing | $8,000 × lic_tier × perf_factor × tier_econ × (reputation / 50) |
| Museum / Heritage | ($8,000 + titles_won × $10,000) × museum_tier × max(0.5, perf_factor) × tier_econ |
| Customer Racing | $25,000 × cr_tier × perf_factor × tier_econ |

**perf_factor** = `max(0.15, min(1.35, 1.45 − avg_recent_pos × 0.10))` — uses your last 5 race finishing positions. Finishing well directly increases all commercial revenue.

**tier_econ multipliers:** T1 = 1.0, T2 = 0.65, T3 = 0.40, T4 = 0.20, T5 = 0.08

### Monthly Costs

| Cost | Notes |
|------|-------|
| Facility upkeep | base_upkeep × facility_tier, per unlocked node |
| Equipment upkeep | base_upkeep × current_level, per active equipment piece |
| Staff wages | Sum of all assigned staff monthly salaries |
| Driver salaries | salary_per_race × 2 per non-academy driver |
| Academy feeder seats | T3 seat: $95k/mo · T4: $55k/mo · T5: $25k/mo |

**Cash is updated weekly:** `weekly_net = net_monthly / 4` added to balance each week.

### Budget Deficit Response

If expenses exceed income, the game automatically:
1. Shuts down the lowest-ROI equipment pieces first
2. Then lays off the lowest-skill staff members

Keep a buffer — unexpected results can cascade.

---

## Champion Bonuses (End of Season)

**T1 / T2 / T3 championship winner (driver):**
- +2 pace, +2 consistency, +2 defending, +12 marketability
- Morale → 100, champion_titles +1
- If that driver races for **your team:** +$2.5M royalty bonus + +8 team reputation

**T4 / T5 feeder series winner (your academy driver):**
- +5 pace, +4 braking, +4 consistency, +4 defending, +15 marketability
- T4 champion: $25k prize + +5 reputation
- T5 champion: $10k prize + +3 reputation

**Forced graduation:**
- T5 champion aged ≥ 16 → automatically moves to T4
- T4 champion aged ≥ 18 → automatically moves to T3

---

## Season Regulations

Regulations are announced at **Week 9** and take effect next season. They can be triggered by any of three conditions:

| Tier | Trigger: Total perf score | OR Points lead | OR Stable seasons |
|------|--------------------------|----------------|------------------|
| T3 | > 3,000 | > 35% | 5 consecutive |
| T2 | > 6,500 | > 35% | 4 consecutive |
| T1 | > 15,000 | > 35% | 3 consecutive |

If triggered, one of five packages is applied:

| Package | What resets |
|---------|------------|
| MECHANICAL_TWEAKS | BRAKES, SUSPENSION |
| AERO_SHAKEUP | FRONT_WING, REAR_WING, FLOOR |
| POWERTRAIN_DIRECTIVE | ENGINE, ERS |
| MAJOR_OVERHAUL | All 7 parts |
| STATUS_QUO | Nothing — next-gen boosts carry over year-on-year |

> [!WARNING]
> Dominating the championship (>35% points lead) can trigger a **MAJOR_OVERHAUL** that wipes your car advantage. Consider managing your development pace.
