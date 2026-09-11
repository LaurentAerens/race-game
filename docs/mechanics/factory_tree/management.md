# Management Department

The Management department has a single node: the **Executive Boardroom**. It provides a global leadership aura that benefits every staff member in every department — making it punch well above its cost.

---

## Tree Structure

```
Executive Boardroom ($2.6M)            ← ROOT and only node
```

---

## Node Reference

### Executive Boardroom
| Field | Value |
|-------|-------|
| Node ID | `mgmt_boardroom` |
| Build cost | $2,600,000 |
| Monthly upkeep | $78,000 × tier |
| Staff capacity | 8 / 16 / 24 |
| Max tier | T3 |
| Prerequisite | None (root node) |

Executive leadership command center. Applies a **global leadership bonus** to all Department Heads and staff across every facility:

```
mgmt_lead_bonus = boardroom_tier × 5.0  (added to leadership stat, capped at 100)
```

| Tier | Global Leadership Bonus |
|------|------------------------|
| T1 | +5 to all staff leadership |
| T2 | +10 to all staff leadership |
| T3 | +15 to all staff leadership |

Equipment installed in the Boardroom adds further leadership bonuses:
- **War Room** (`eq_mgmt_strategy_war_room`): +1.5 leadership per level
- **Executive Telemetry** (`eq_mgmt_exec_telemetry`): +1.0 leadership per level
- **Board Display** (`eq_mgmt_board_display`): +1.5 leadership per level

### Why Leadership Matters

Leadership feeds into the **coordination rating** formula for every facility:

```
coordination = (head_leadership × 0.45 + avg_staff_leadership × 0.20 + avg_communication × 0.35) / 100
```

Higher coordination means a lower diminishing returns exponent (γ), which makes every additional specialist more valuable. A T3 Boardroom with full equipment can add 15+ leadership globally — meaningfully shifting coordination across all departments simultaneously.

> [!TIP]
> The Boardroom is the highest-ROI early purchase for global facility output. At $2.6M to build and $78k/month upkeep, it costs less than most individual specialist salaries while benefiting every person in the building.
