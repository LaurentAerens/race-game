# Admin & Creator Tools

The **Admin & Creator Suite** is accessible from the main menu. It contains two tools: the **Track Designer** and the **Database Editor**.

---

## Accessing the Admin Suite

From the main menu, select **Admin & Creator Suite**. A top bar with two tabs appears:

| Tab | Tool |
|-----|------|
| **TRACK DESIGNER** | Interactive circuit CAD editor + OpenStreetMap importer |
| **DATABASE EDITOR** | Edit car performance, driver skills, and team liveries |

Click **< MAIN MENU** in the top bar to return.

---

## Track Designer

A CAD-style interactive circuit designer. You can build circuits from scratch by placing and dragging control points, or import real-world road layouts from OpenStreetMap.

### Controls

| Input | Action |
|-------|--------|
| Left-click empty canvas | Insert a new control point |
| Left-click + drag node | Move an existing control point |
| Right-click node / Del | Remove that control point |
| Middle-click + drag / right-drag | Pan the canvas |
| Scroll wheel | Zoom in / out |
| Ctrl+Z | Undo last action |
| Ctrl+Y | Redo |

### Left Panel Options

- **Track name** — editable text field
- **Track width** — global default width in metres; individual nodes can override this
- **Per-node width** — select two adjacent nodes (Node A / Node B) and set the width for that section
- **DRS zones** — place entry and exit points for DRS detection and activation zones
- **Pit lane** — set pit entry node, pit exit node, side (left/right), and lateral offset in metres
- **Tyre compound selection** — pick 3 compounds from the dry compound list (C1–C5 / HARD–HYPERSOFT) to nominate for this circuit
- **Save** — saves the circuit to `tracks/` as a JSON file
- **Load** — opens a track browser showing all `.json` files in `tracks/`
- **Test Race** — launches an exhibition race on the current circuit immediately

### Track JSON Format

Saved tracks are plain JSON in `tracks/`. The format is:

```json
{
  "name": "My Custom Circuit",
  "width": 14.0,
  "control_points": [[x, y], ...],
  "node_widths": [14.0, ...],
  "sectors": [0.33, 0.66, 1.0],
  "drs_zones": [],
  "pit_entry_s": 1601.9,
  "pit_exit_s": 100.0,
  "pit_control_points": [[x, y], ...]
}
```

Coordinates are in metres on a local 2D plane (not GPS). You can hand-edit these files.

---

## OpenStreetMap Import

The **OSM Import** button inside the Track Designer opens a map modal that lets you trace a circuit layout from real-world road data.

### How it works

1. **Search** — type any location (city, venue, street name). The modal geocodes it via the OpenStreetMap Nominatim API and centres the map there.
2. **Road network render** — roads are fetched from the **Overpass API** and drawn colour-coded by type (motorway, primary, secondary, residential, etc.).
3. **Place waypoints** — click on roads to snap a waypoint to the nearest road node. Waypoints are connected in order.
4. **Auto-close loop** — once you have enough waypoints, the importer finds the shortest road path back to the start and closes the circuit.
5. **Clean up** — backtracking segments and excessive hairpins are automatically removed.
6. **Generate Circuit** — the GPS coordinates are projected to a local metre-plane using **Spherical Mercator (WGS84)** projection and converted to a `Circuit` object, which loads directly into the Track Designer for further editing.

### Technical notes

- Road data is fetched live from `overpass-api.de` — requires an internet connection.
- Fetch timeout is 10 seconds; if the area is too large or the server is busy, reduce the map zoom level.
- The OSM data cache is stored in `data/osm_cache/` as JSON files keyed by bounding box.
- The importer queries: `highway~"primary|secondary|tertiary|residential"` — motorways are excluded by default to avoid non-driveable layouts.
- GPS → metres conversion: `x = R × Δlon × cos(lat_rad)`, `y = −R × Δlat` (Y inverted so North is up).
- Any resulting circuit can be saved as a `.json` track and used in both exhibition races and the career mode calendar.

> [!NOTE]
> All circuits generated from OSM data are based on public road geometry. No trademarked circuit names or layouts are included as presets — you build and name everything yourself.

---

## Database Editor

A tabbed editor for modifying the game databases directly. Changes take effect immediately (no restart required).

### Exhibition Database (`race_game.db`)

- **Cars** — edit car performance ratings
- **Drivers** — edit any driver''s skill attributes (pace, braking, consistency, etc.)

### Career Database (`career.db`)

- **Teams** — edit team livery colours, performance ratings, cash, and reputation
- **Drivers** — edit career driver stats and potential ceilings
- **Facilities** — view and modify facility tier levels for any team

> [!CAUTION]
> The Database Editor writes directly to the SQLite files. There is no undo for database edits — back up `career.db` before making bulk changes.
