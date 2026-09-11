# 2D Open-Wheel Race Simulator & Circuit Designer

A standalone native desktop 2D open-wheel race simulator and interactive track editor inspired by *Motorsport Manager Mobile 3*. Built in pure **Python** with **Pygame-CE**, **SciPy**, and **Shapely** (100% open source, zero browser/HTML/JS dependencies).

---

## Features

### 1. Motorsport Manager Style 2D Race Simulation
- **20-Car Grid & 10 Teams**: Multi-lane racing line physics, slipstream (drafting), DRS activation zones, and late-braking overtaking maneuvers.
- **Deep Tire Degradation Model**: Soft (Red), Medium (Yellow), Hard (White), Intermediate (Green), and Full Wet (Blue) with realistic degradation cliffs, thermals, and wet-track crossover.
- **Tactical Driver Management**: Direct real-time commands for your team's drivers:
  - **Pace Mode**: Conserve, Normal, Push, Attack
  - **Engine Mix**: Lean, Standard, Rich
  - **ERS Battery**: Recharge, Balanced, Boost/Overtake
  - **Interactive "BOX THIS LAP"**: Pit strategy modal to pick tire compound.
- **Live Timing Tower**: Positions, gaps to leader, intervals, tire wear %, compound badges, pit counters, and personal best / fastest lap indicators. Click any driver to track them with the dynamic camera.
- **Dynamic Weather System**: Rain radar with 6-lap forward forecast, track wetness accumulation, and drying line physics.
- **Race Control**: Green/Yellow flags, Virtual Safety Car, Full Safety Car bunching the pack, and DRS enable/disable rules.

### 2. Interactive CAD-Style Circuit Designer
- **Visual Track Builder**:
  - Left-click on the canvas to add track control nodes.
  - Left-click & drag existing nodes to reshape corners in real-time.
  - Right-click any node to delete it.
  - Adjust track width and add DRS zones.
  - **Save & Load**: Saves directly to human-readable JSON files in `tracks/`.
  - **Test Race**: Hit "RACE ON THIS TRACK >>" to immediately start a 20-car Grand Prix on your custom creation!

### 3. OpenStreetMap (OSM) Track Importer
- Built-in Mercator projection utility (`src/core/osm_importer.py`) capable of converting real-world GPS coordinates and city street loops into playable racing circuits.

---

## Quick Start

### Installation
Ensure Python 3.11+ is installed, then install the lightweight dependencies:
```bash
pip install -r requirements.txt
```

### Launch the Game
Run the native desktop application:
```bash
python main.py
```

### Run Tests
```bash
python -m unittest discover tests
```

---

## Project Structure
```
race-game/
├── main.py                  # Desktop application entry point & mode controller
├── requirements.txt         # pygame-ce, scipy, shapely, requests, numpy
├── tracks/                  # Saved JSON track definitions
│   ├── emerald_ring.json
│   ├── apex_park.json
│   └── harbor_city.json
├── src/
│   ├── core/
│   │   ├── circuit.py       # Spline geometry, multi-lane offsets, DRS, sectors
│   │   ├── car.py           # Formula car dynamics, AI, slipstream, pit stops
│   │   ├── driver.py        # Driver stats, skills & ratings
│   │   ├── tires.py         # Tire compounds, deg curves & thermal grip
│   │   ├── weather.py       # Rain radar, wetness & drying lines
│   │   ├── race_control.py  # Flags, Safety Car, DRS rules
│   │   ├── osm_importer.py  # OpenStreetMap GPS / GeoJSON importer
│   │   └── simulation.py    # Master race coordinator & tick loop
│   ├── editor/
│   │   └── track_editor.py  # Interactive visual circuit designer
│   ├── data/
│   │   ├── teams.py         # 10 teams, 20 drivers with liveries & stats
│   │   └── default_tracks.py# Pre-made circuit generators
│   ├── render/
│   │   ├── track_renderer.py# AA asphalt, kerbs, DRS lines & pit lane
│   │   ├── car_renderer.py  # 2D formula cars, liveries, wings & particles
│   │   └── camera.py        # Smooth pan/zoom & car tracking
│   └── ui/
│       ├── theme.py         # Dark F1 broadcast theme
│       ├── timing_tower.py  # Live leaderboard & telemetry
│       ├── driver_panel.py  # Strategy management panel
│       ├── pit_modal.py     # Pit stop strategy dialog
│       ├── broadcast_header.py # Top bar (laps, weather, speed controls)
│       └── event_feed.py    # Live commentary & radio messages
└── tests/
    └── test_simulation.py   # Unit test suite
```

---

## License

This project is licensed under the **GNU General Public License v3.0** (GPL-3.0). See the [LICENSE](LICENSE) file for details.

