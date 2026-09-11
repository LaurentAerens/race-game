import os
from typing import Dict, List
from ..core.circuit import Circuit

def create_emerald_ring() -> Circuit:
    """Balanced / Technical circuit: mixed straights, fast sweepers, technical infield, and final hairpin."""
    circuit = Circuit(name="Emerald Ring", width=14.0)
    points = [
        (-400, -250), (-150, -260), (100, -250), (350, -240),  # Main Straight (Nodes 0-3)
        (500, -180), (550, -50), (450, 80),                    # Turn 1-2 Fast Sweeper
        (300, 100), (150, 180), (100, 300),                    # Technical Infield
        (-50, 350), (-200, 300), (-250, 150),                  # Turn 6-8 Complex
        (-450, 100), (-550, -50), (-500, -180)                 # Final Hairpin onto Straight (Nodes 13-15)
    ]
    circuit.sectors = [0.33, 0.66, 1.0]
    circuit.set_control_points(points)
    circuit.set_pit_lane_endpoints(entry_node=15, exit_node=1, side="INSIDE", offset_m=12.0)
    
    circuit.drs_zones = [
        {"name": "Main Straight", "start_s": 0.0, "end_s": circuit.length * 0.22},
        {"name": "Back Straight", "start_s": circuit.length * 0.45, "end_s": circuit.length * 0.60}
    ]
    circuit.base_rain_chance = 0.25
    return circuit

def create_autodromo_velocita() -> Circuit:
    """Straight Line Speed / Power circuit: ultra-long straights, high top speed, dual DRS zones (Monza archetype)."""
    circuit = Circuit(name="Autodromo Velocita", width=14.5)
    points = [
        (-550, -320), (-250, -320), (100, -320), (450, -320),   # Main Straight (Nodes 0-3)
        (620, -260), (660, -160), (580, -90),                   # Chicane (Nodes 4-6)
        (480, 20), (420, 140), (380, 280),                      # Curva Grande Sweeper (Nodes 7-9)
        (200, 340), (-100, 340), (-350, 320),                   # Back Straight (Nodes 10-12)
        (-480, 250), (-540, 150), (-580, 30),                   # S-Curve Complex (Nodes 13-15)
        (-660, -80), (-640, -220)                               # Curva Parabolica (Nodes 16-17)
    ]
    circuit.sectors = [0.32, 0.65, 1.0]
    circuit.set_control_points(points)
    circuit.set_pit_lane_endpoints(entry_node=17, exit_node=1, side="INSIDE", offset_m=12.0)
    
    circuit.drs_zones = [
        {"name": "Main Straight", "start_s": 0.0, "end_s": circuit.length * 0.24},
        {"name": "Back Straight", "start_s": circuit.length * 0.52, "end_s": circuit.length * 0.72}
    ]
    circuit.base_rain_chance = 0.10
    return circuit

def create_oasis_grand_prix() -> Circuit:
    """Heavy Braking / Stop-and-Go circuit: high-speed approaches into hard braking hairpins and 90-degree corners."""
    circuit = Circuit(name="Oasis Grand Prix", width=14.0)
    points = [
        (-350, -260), (-100, -260), (150, -260), (400, -260),  # Start / Finish Straight (Nodes 0-3)
        (540, -230), (560, -120), (460, -50),                  # Turn 1-2 Heavy Braking Hairpin (Nodes 4-6)
        (380, 40), (380, 160),                                 # Acceleration Chute (Nodes 7-8)
        (480, 230), (420, 320), (280, 320),                    # Hard 90-Degree Corner (Nodes 9-11)
        (140, 280), (30, 200), (-60, 200),                     # Infield Stop-and-Go Chicane (Nodes 12-14)
        (-220, 240), (-380, 200),                              # Back Straight (Nodes 15-16)
        (-490, 100), (-520, -40), (-450, -180)                 # Final Deceleration Hairpin (Nodes 17-19)
    ]
    circuit.sectors = [0.34, 0.68, 1.0]
    circuit.set_control_points(points)
    circuit.set_pit_lane_endpoints(entry_node=19, exit_node=1, side="INSIDE", offset_m=12.0)
    
    circuit.drs_zones = [
        {"name": "Pit Straight", "start_s": 0.0, "end_s": circuit.length * 0.22},
        {"name": "Desert Back Straight", "start_s": circuit.length * 0.64, "end_s": circuit.length * 0.82}
    ]
    circuit.base_rain_chance = 0.02
    return circuit

def create_vortex_aero_ring() -> Circuit:
    """High-Speed Aero Sweepers circuit: wide 17m track with flowing high-radius corners and esses (Silverstone/Suzuka archetype)."""
    circuit = Circuit(name="Vortex Aero Ring", width=17.0)
    points = [
        (-380, -220), (-100, -220), (180, -220),               # Pit Straight (Nodes 0-2)
        (380, -170), (520, -70),                               # Abbey High-Speed Sweeper (Nodes 3-4)
        (460, 60), (340, 160), (200, 200), (60, 280),         # Flowing Esses (Nodes 5-8)
        (-80, 320), (-240, 300),                               # Chapel Curve Exit (Nodes 9-10)
        (-380, 220), (-500, 100),                              # Hangar Fast Arc (Nodes 11-12)
        (-560, -30), (-520, -140), (-460, -190)                # Sweeping Carousel (Nodes 13-15)
    ]
    widths = [16.0, 16.0, 16.0, 17.5, 18.0, 17.5, 17.0, 17.0, 17.5, 18.0, 18.0, 17.0, 17.0, 17.5, 17.5, 16.0]
    circuit.sectors = [0.33, 0.66, 1.0]
    circuit.set_control_points(points, widths=widths)
    circuit.set_pit_lane_endpoints(entry_node=15, exit_node=1, side="INSIDE", offset_m=13.0)
    
    circuit.drs_zones = [
        {"name": "Main Straight", "start_s": 0.0, "end_s": circuit.length * 0.18},
        {"name": "Vortex Sweeper DRS", "start_s": circuit.length * 0.58, "end_s": circuit.length * 0.76}
    ]
    circuit.base_rain_chance = 0.40
    return circuit

def create_apex_park() -> Circuit:
    """Heavy Braking / Technical circuit: chicanes, hairpins, and tight esses."""
    circuit = Circuit(name="Apex Park", width=15.0)
    points = [
        (-300, -200), (0, -200), (300, -200), (450, -150),     # Main Straight
        (500, 0), (400, 100), (200, 120),                      # Turn 1-3 Chicane
        (100, 250), (0, 300), (-150, 250),                     # Hairpin
        (-250, 100), (-350, 50), (-450, -50)                   # Fast Esses
    ]
    circuit.sectors = [0.35, 0.70, 1.0]
    circuit.set_control_points(points)
    circuit.set_pit_lane_endpoints(entry_node=12, exit_node=1, side="INSIDE", offset_m=12.0)
    circuit.drs_zones = [
        {"name": "Main Straight", "start_s": 0.0, "end_s": circuit.length * 0.25}
    ]
    circuit.base_rain_chance = 0.30
    return circuit

def create_harbor_city() -> Circuit:
    """Street Circuit / Heavy Braking: narrow walls, 90-degree marina turns, and chicane."""
    circuit = Circuit(name="Harbor City Street Circuit", width=12.0)
    points = [
        (-250, -150), (0, -150), (250, -150),                  # Harbor Boulevard
        (350, -100), (350, 50), (300, 150),                    # 90-degree Marina Turns
        (150, 180), (50, 220), (-100, 200),                    # Casino Square
        (-200, 150), (-300, 50), (-350, -50)                   # Tunnel & Swimming Pool
    ]
    circuit.sectors = [0.32, 0.68, 1.0]
    circuit.set_control_points(points)
    circuit.set_pit_lane_endpoints(entry_node=11, exit_node=1, side="INSIDE", offset_m=12.0)
    circuit.drs_zones = [
        {"name": "Harbor Straight", "start_s": 0.0, "end_s": circuit.length * 0.22}
    ]
    circuit.base_rain_chance = 0.12
    return circuit

def create_riviera_speedway() -> Circuit:
    """Balanced / Flowing circuit: long sweeping curves, medium straight, elevation-style transitions."""
    circuit = Circuit(name="Riviera Speedway", width=14.0)
    points = [
        (-350, -220), (-100, -220), (150, -220), (350, -200),  # Coastline Straight (Nodes 0-3)
        (480, -140), (510, -20), (440, 80),                    # Coastal Sweeper (Nodes 4-6)
        (320, 140), (180, 180), (80, 260),                     # Up-Hill Esse (Nodes 7-9)
        (-60, 300), (-200, 280), (-320, 180),                  # Ridge Curve (Nodes 10-12)
        (-420, 80), (-490, -40), (-450, -160)                  # Carousel Descent (Nodes 13-15)
    ]
    circuit.sectors = [0.33, 0.67, 1.0]
    circuit.set_control_points(points)
    circuit.set_pit_lane_endpoints(entry_node=15, exit_node=1, side="INSIDE", offset_m=12.0)
    circuit.drs_zones = [
        {"name": "Coastline Straight", "start_s": 0.0, "end_s": circuit.length * 0.23},
        {"name": "Ridge Straight", "start_s": circuit.length * 0.55, "end_s": circuit.length * 0.70}
    ]
    circuit.base_rain_chance = 0.18
    return circuit

def create_ardennes_forest() -> Circuit:
    """Straight Line Speed & Sweepers circuit: long uphill acceleration run, sweeping downhill curve (Spa archetype)."""
    circuit = Circuit(name="Ardennes Forest Circuit", width=14.5)
    points = [
        (-420, -280), (-180, -280), (80, -270),                # Pit Straight (Nodes 0-2)
        (220, -220), (280, -120),                              # Turn 1 Hairpin (Nodes 3-4)
        (380, -30), (450, 80), (480, 220),                     # Acceleration Blast (Nodes 5-7)
        (380, 320), (220, 350), (40, 320),                     # Chicane (Nodes 8-10)
        (-140, 260), (-260, 160), (-360, 60),                  # Fast Sweeper (Nodes 11-13)
        (-460, -40), (-520, -150), (-480, -230)                # Bus Stop & Final Turn (Nodes 14-16)
    ]
    circuit.sectors = [0.31, 0.64, 1.0]
    circuit.set_control_points(points)
    circuit.set_pit_lane_endpoints(entry_node=16, exit_node=1, side="INSIDE", offset_m=12.0)
    circuit.drs_zones = [
        {"name": "Kemmel Straight", "start_s": circuit.length * 0.18, "end_s": circuit.length * 0.40},
        {"name": "Blanchimont DRS", "start_s": circuit.length * 0.74, "end_s": circuit.length * 0.92}
    ]
    circuit.base_rain_chance = 0.60
    return circuit

def initialize_default_tracks_folder(tracks_dir: str = "tracks"):
    """Creates default track JSON files for all circuit archetypes."""
    os.makedirs(tracks_dir, exist_ok=True)
    circuits = [
        create_emerald_ring(),
        create_autodromo_velocita(),
        create_oasis_grand_prix(),
        create_vortex_aero_ring(),
        create_apex_park(),
        create_harbor_city(),
        create_riviera_speedway(),
        create_ardennes_forest()
    ]
    for c in circuits:
        safe_name = c.name.lower().replace(" ", "_").replace("-", "_") + ".json"
        path = os.path.join(tracks_dir, safe_name)
        c.save_json(path)

