# Game Overview

You are the team principal of a motorsport outfit working your way from the junior ranks to the pinnacle of the sport. Every decision — who drives, where you spend your R&D budget, which sponsors you sign, how you develop your staff — shapes your team's trajectory across multiple seasons.

---

## The Tier Ladder

The game features five competitive tiers. You start in **Tier 3** and work your way up through promotion.

| Tier | Series Name | Notes |
|------|-------------|-------|
| **T5** | Karting Masters Academy | Feeder series. Min driver age 14. 3 seats/team. |
| **T4** | Junior Talent Series F4 | Feeder series. Min driver age 15. 3 seats/team. |
| **T3** | National Open Cup | **Player starting tier.** Sprint-only weekends. |
| **T2** | Continental Championship | Full race weekends. ERS display unlocked. |
| **T1** | World Super Formula | Sprint + Race. Full ERS control. All 7 custom parts. |

> [!NOTE]
> T4 and T5 are **academy feeder series** — you do not race there yourself, but you can purchase seats to develop young drivers in your academy program.

---

## Session Structure by Tier

| Session | Tier 3 | Tier 2 | Tier 1 |
|---------|--------|--------|--------|
| Free Practice 1 | ✅ (5 laps) | ✅ (5 laps) | ✅ (5 laps) |
| Free Practice 2 | ✅ (5 laps) | ✅ (5 laps) | ✅ (5 laps) |
| Qualifying | ✅ (3 laps) | ✅ (3 laps) | ✅ (3 laps) |
| Sprint | ✅ | ❌ | ✅ (reversed top-10 grid) |
| Free Practice 3 | ❌ | ❌ | ✅ (5 laps) |
| Race | ❌ | ✅ | ✅ |

**Lap counts:**
- **Sprint:** `max(7, round(total_circuit_laps × 0.38))`
- **Race:** `max(18, total_circuit_laps)`

> [!IMPORTANT]
> In **Tier 3 there is no main race** — the Sprint is your only points-paying session each weekend.

---

## Points Systems

**Sprint** (top 8 score):

| P1 | P2 | P3 | P4 | P5 | P6 | P7 | P8 |
|----|----|----|----|----|----|----|-----|
| 8 | 7 | 6 | 5 | 4 | 3 | 2 | 1 |

**Race** (top 10 score):

| P1 | P2 | P3 | P4 | P5 | P6 | P7 | P8 | P9 | P10 |
|----|----|----|----|----|----|----|----|----|----|
| 25 | 18 | 15 | 12 | 10 | 8 | 6 | 4 | 2 | 1 |

---

## Tier Restrictions at a Glance

| Feature | T3 | T2 | T1 |
|---|---|---|---|
| Pace modes | NORMAL, PUSH | CONSERVE, NORMAL, PUSH, ATTACK | All |
| Engine modes | STANDARD only | LEAN, STANDARD, RICH | All |
| ERS | N/A | % shown, mode locked `[Spec]` | AUTO / RECHARGE / BALANCED / OVERTAKE |
| Custom R&D parts | BRAKES, FRONT_WING | All except FLOOR & ERS | All 7 parts |

---

## Season Calendar

Each season runs for **18 weeks**. Key milestones:

- **Week 9:** Next season's regulations are announced.
- **Weeks 13–16:** Port-back upgrade window (if eligible — see Factory).
- **Season finale:** Promotion, relegation, and champion bonuses are resolved.

AI teams develop in the background: from Week 9 onward, AI teams with no next-gen R&D allocation are automatically assigned 30–40% of budget.
