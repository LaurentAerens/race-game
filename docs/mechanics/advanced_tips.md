# Advanced Tips

All tips on this page are grounded in actual game mechanics.

---

## Race Strategy

**Pit under Safety Car — almost always.**
When the SC or VSC is deployed, the field bunches up and the pace difference between pitting and staying out collapses. This is the single best time to take a free tyre change. You lose minimal position gap because everyone is slowed down.

**There is no fuel refueling — manage from the start.**
Fuel is fixed at 50 kg at race start and only depletes. Use **LEAN engine mode** (0.80× fuel burn) during low-intensity phases. A `LONG_RUNS` practice plan also unlocks a fuel-saving bonus multiplier for the race.

**Use RICH engine mode sparingly.**
RICH mode: 1.35× fuel burn + 1.40× engine wear. It is a powerful sprint tool for the final laps or overtake attempts, but running it sustained risks terminal engine failure (component hits 0% = instant retirement).

**Monitor the component health bars constantly.**
FW / RW / BRK / ENG are shown in the Driver Strategy Panel. Any component reaching **0% = immediate retirement**. Emergency Repairs (+14 s) restore below-55% parts to 55–60% — use it as an insurance call, not a habitual stop.

**Clicking the Timing Tower follows that car.**
Click any row in the left panel to switch the camera to that driver. Useful for monitoring direct rivals mid-race.

---

## Tyre & Weather

**Intermediate tyres can be optimal for just 2–3 laps.**
The weather radar shows per-sector wetness (S1 / S2 / S3 independently) when a local shower is active. A patch of rain through one sector may make intermediates faster than any dry compound — watch the radar bars for upcoming laps.

**Driver `wet_weather` stat matters a great deal in rain.**
Signing drivers with high wet weather skill gives a major advantage on circuits with high rain probability (Knockhill 55%, Ardennes 60%, Vortex 40%).

---

## Driver Development

**Sign young, develop early.**
Driver growth is fastest before age 28. The age factor formula peaks for teenagers:
`age_factor = max(0.18, 1.0 − ((age − 15) / 14) × 0.55)`
A 17-year-old develops significantly faster than a 26-year-old.

**Race position multiplies development — a lot.**
P1 gives a **3.0× development multiplier**. P17+ gives only 0.55×. Putting a young driver in a competitive car accelerates their growth dramatically.

**Physio facility slows driver decline past 30.**
The decay buffer formula is reduced by physio tier and equipment level. Prioritise this if you have an older driver you want to keep competitive.

**Academy drivers are your cheapest fast-learners.**
Academy base growth rate (0.52×) beats race driver base (0.38×), and the youngest academy drivers grow even faster. Prodigy drivers get an additional multiplier. Auto-release happens at age > 25 — promote before then.

**Homegrown loyalty is your most powerful salary tool.**
Academy-developed drivers who join your main team get an 80% salary discount that decays over 6 seasons. Running an academy costs $25–95k/month per seat but pays back enormously in reduced wage bills.

**Don't over-negotiate with drivers.**
Each rejected offer decrements a driver's patience by 1. At 0, they walk permanently. Know your limit and make a competitive offer the first or second time.

---

## Engineering & Factory

**STATUS_QUO years are accumulation years.**
Next-gen chassis R&D boosts carry over year-on-year under STATUS_QUO. Even in a season where you don't dominate, investing in next-gen R&D compounds into future car improvements.

**Port-back is a late-season power move.**
Available Weeks 13–16 (STATUS_QUO seasons only, ≥10,000 next-gen points). Ports 2/3 of your accumulated performance + reliability boost to the current car. It comes with a 2-week factory cooldown, so time it around a circuit you're already competitive at.

**Dominating by >35% can trigger a MAJOR_OVERHAUL.**
If your championship lead exceeds 35% of the theoretical maximum, you risk triggering regulations that reset all 7 car components for next season. Consider whether to manage your development pace to avoid it.

**Regulations are announced Week 9 — adapt early.**
You have 9 weeks after announcement to adjust next-gen R&D allocation before the season ends. If an overhaul is coming, stop accumulating and invest this season's points wisely.

---

## Staff

**Vacant Category Director = 10% permanent output drag.**
A missing director applies a 0.90× multiplier to the entire department until filled. This is a hidden but persistent cost — always keep director seats filled.

**A great Department Head nearly eliminates diminishing returns.**
The diminishing returns exponent γ ranges from 0.55 (poor coordination) to 0.15 (elite coordination). An elite head with strong leadership makes every additional specialist more valuable.

**Underpaid staff lose morale fast.**
Below the underpaid threshold, morale drops 2.5 points per week. At minimum morale (15), staff output is capped at 0.40×. Pay at or above market rate — or invest in Teambuilding to lower the threshold.

**Intern prodigies are worth their mentor penalty.**
A mentored specialist works at 85% during the 6-week programme, but a prodigy intern graduates with potential 90–98 and receives +10–12 stat boosts. Prioritise mentoring prodigies.

---

## Finance & Promotion

**Promotion is worth far more than one champion bonus.**
Beyond the $2.5M royalty and $8 reputation boost, promoting to T2 increases per-race sponsor income by ~1.87×, and T2→T1 by ~1.93×. The compound effect over a full T2 season dwarfs the one-time prizes.

**Pay-drivers are a T3 survival tool, not a long-term solution.**
A very weak pay-driver can bring substantial sponsor income, but the development penalty and race performance hit compounds over time. Use them to survive early cash-tight seasons, then replace with academy graduates.

**Track your perf_factor actively.**
Your commercial revenue (merchandise, fan club, licensing) is multiplied by perf_factor based on last 5 race results. Finishing consistently in the top 5 produces 1.35× income vs 0.15× for consistent backmarker results — a 9× difference in commercial output.
