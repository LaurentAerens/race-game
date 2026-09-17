"""
Generates a high-definition, transparent top-down Formula Car technical blueprint asset.
Saves to data/formula_car_topdown.png for crisp Pygame smoothscaling in Car R&D Engineering.
"""

import os

import pygame


def generate_formula_car_blueprint(output_path: str = "data/formula_car_topdown.png"):
    pygame.init()
    # High resolution canvas: 1600 x 700 with alpha channel
    W, H = 1600, 700
    surf = pygame.Surface((W, H), pygame.SRCALPHA)
    surf.fill((0, 0, 0, 0))

    # Centerline & Car Coordinates (Horizontal orientation: Left = Front Nose, Right = Rear Exhaust)
    cx = W // 2
    cy = H // 2
    car_len = 1200
    half_l = car_len // 2

    front_x = cx - half_l + 80  # ~280
    rear_x = cx + half_l - 40  # ~1440

    # Colors: Technical blueprint palette
    C_OUTLINE = (0, 240, 255, 230)  # Electric cyan primary
    C_BODY_FILL = (12, 18, 28, 200)  # Semi-transparent dark carbon
    C_SECONDARY = (0, 180, 220, 190)  # Sub-wires
    C_ACCENT = (0, 255, 200, 240)  # Bright aqua
    C_TIRE = (20, 24, 32, 240)  # Tire rubber
    C_TIRE_RIM = (55, 75, 100, 255)  # Wheel rim line
    C_DISC = (255, 160, 40, 220)  # Carbon brake disc glow
    C_GRID = (0, 140, 180, 40)  # Calibration grid lines

    # Subtle blueprint coordinate ticks
    for x in range(front_x - 60, rear_x + 80, 60):
        pygame.draw.line(surf, C_GRID, (x, cy - 260), (x, cy + 260), 1)
    for y in range(cy - 240, cy + 260, 60):
        pygame.draw.line(surf, C_GRID, (front_x - 60, y), (rear_x + 80, y), 1)

    # 1. FRONT WING ASSEMBLY
    # Multi-tier front wing mainplane with curved endplates
    fw_span = 240
    fw_pts = [
        (front_x - 60, cy - fw_span),
        (front_x - 10, cy - fw_span + 10),
        (front_x + 40, cy - 70),
        (front_x + 30, cy),
        (front_x + 40, cy + 70),
        (front_x - 10, cy + fw_span - 10),
        (front_x - 60, cy + fw_span),
        (front_x - 75, cy + fw_span - 30),
        (front_x - 20, cy),
        (front_x - 75, cy - fw_span + 30),
    ]
    pygame.draw.polygon(surf, C_BODY_FILL, fw_pts)
    pygame.draw.polygon(surf, C_OUTLINE, fw_pts, width=3)

    # Front wing secondary cascade flaps
    for offset, alpha in [(15, 180), (30, 140), (45, 100)]:
        flap_col = (0, 220, 255, alpha)
        flap_top = [
            (front_x - 50 + offset, cy - fw_span + 15),
            (front_x - 5 + offset, cy - fw_span + 30),
            (front_x + 35 + offset // 2, cy - 65),
        ]
        pygame.draw.lines(surf, flap_col, False, flap_top, width=2)
        flap_bot = [
            (front_x - 50 + offset, cy + fw_span - 15),
            (front_x - 5 + offset, cy + fw_span - 30),
            (front_x + 35 + offset // 2, cy + 65),
        ]
        pygame.draw.lines(surf, flap_col, False, flap_bot, width=2)

    # Front Wing Endplates
    pygame.draw.rect(surf, C_ACCENT, (front_x - 78, cy - fw_span - 5, 45, 12), border_radius=3)
    pygame.draw.rect(surf, C_ACCENT, (front_x - 78, cy + fw_span - 7, 45, 12), border_radius=3)

    # 2. NOSE CONE & MONOCOQUE
    nose_pts = [
        (front_x - 15, cy),
        (front_x + 50, cy - 28),
        (front_x + 190, cy - 44),
        (front_x + 360, cy - 54),
        (cx - 30, cy - 60),
        (cx + 80, cy - 75),
        (cx + 280, cy - 70),
        (rear_x - 80, cy - 40),
        (rear_x - 20, cy),
        (rear_x - 80, cy + 40),
        (cx + 280, cy + 70),
        (cx + 80, cy + 75),
        (cx - 30, cy + 60),
        (front_x + 360, cy + 54),
        (front_x + 190, cy + 44),
        (front_x + 50, cy + 28),
    ]
    pygame.draw.polygon(surf, C_BODY_FILL, nose_pts)
    pygame.draw.polygon(surf, C_OUTLINE, nose_pts, width=3)

    # Nose tip vanity panel & pitot tube
    pygame.draw.line(surf, C_ACCENT, (front_x - 45, cy), (front_x - 15, cy), 3)
    pygame.draw.ellipse(surf, C_SECONDARY, (front_x + 40, cy - 14, 50, 28), width=2)

    # 3. OPEN WHEELS & BRAKE ASSEMBLIES
    # Front axle ~ front_x + 230, Rear axle ~ rear_x - 110
    fw_x = front_x + 200
    rw_x = rear_x - 150
    wheel_w, wheel_h = 135, 75
    rwheel_w, rwheel_h = 155, 90

    wheels = [
        # (x, y, w, h, is_rear)
        (fw_x, cy - 235, wheel_w, wheel_h, False),
        (fw_x, cy + 160, wheel_w, wheel_h, False),
        (rw_x, cy - 250, rwheel_w, rwheel_h, True),
        (rw_x, cy + 160, rwheel_w, rwheel_h, True),
    ]

    for wx, wy, ww, wh, is_rear in wheels:
        # Tire body
        pygame.draw.rect(surf, C_TIRE, (wx, wy, ww, wh), border_radius=10)
        pygame.draw.rect(surf, C_OUTLINE, (wx, wy, ww, wh), width=2, border_radius=10)
        # Tread groove lines
        for g_off in [-wh // 4, 0, wh // 4]:
            pygame.draw.line(
                surf, (35, 45, 60), (wx + 10, wy + wh // 2 + g_off), (wx + ww - 10, wy + wh // 2 + g_off), 2
            )
        # Rim hub & wheel center
        rim_rect = pygame.Rect(wx + 22, wy + 12, ww - 44, wh - 24)
        pygame.draw.ellipse(surf, C_TIRE_RIM, rim_rect)
        pygame.draw.ellipse(surf, C_OUTLINE, rim_rect, width=2)
        # Glowing carbon brake disc core inside rim
        disc_rect = pygame.Rect(wx + ww // 2 - 18, wy + wh // 2 - 10, 36, 20)
        pygame.draw.ellipse(surf, C_DISC, disc_rect)
        pygame.draw.circle(surf, (255, 220, 120), (wx + ww // 2, wy + wh // 2), 4)

    # 4. FRONT SUSPENSION WISHBONES (Double A-Arm + Pushrod geometry)
    f_hub_top = (fw_x + wheel_w // 2, cy - 160)
    f_hub_bot = (fw_x + wheel_w // 2, cy + 160)
    chassis_f_top1 = (fw_x - 30, cy - 42)
    chassis_f_top2 = (fw_x + 90, cy - 48)
    chassis_f_bot1 = (fw_x - 30, cy + 42)
    chassis_f_bot2 = (fw_x + 90, cy + 48)

    # Upper and Lower wishbones
    sus_col = (0, 200, 255, 220)
    for h_pt, c1, c2 in [(f_hub_top, chassis_f_top1, chassis_f_top2), (f_hub_bot, chassis_f_bot1, chassis_f_bot2)]:
        pygame.draw.line(surf, sus_col, h_pt, c1, 3)
        pygame.draw.line(surf, sus_col, h_pt, c2, 3)
        # Pushrod / steering tie-rod
        mid_chassis = (c1[0] + 50, (c1[1] + c2[1]) // 2)
        pygame.draw.line(surf, (0, 255, 220), h_pt, mid_chassis, 2)

    # 5. SIDEPODS & VENTURI FLOORS (Downwash aerodynamic channels)
    sidepod_l = [
        (cx - 90, cy - 60),
        (cx - 60, cy - 150),
        (cx + 60, cy - 146),
        (cx + 190, cy - 120),
        (cx + 280, cy - 70),
    ]
    sidepod_r = [
        (cx - 90, cy + 60),
        (cx - 60, cy + 150),
        (cx + 60, cy + 146),
        (cx + 190, cy + 120),
        (cx + 280, cy + 70),
    ]
    pygame.draw.polygon(surf, (14, 22, 34, 210), sidepod_l)
    pygame.draw.polygon(surf, C_OUTLINE, sidepod_l, width=3)
    pygame.draw.polygon(surf, (14, 22, 34, 210), sidepod_r)
    pygame.draw.polygon(surf, C_OUTLINE, sidepod_r, width=3)

    # Radiator cooling gills / louvers
    for i in range(5):
        lx = cx + 20 + i * 22
        pygame.draw.line(surf, C_SECONDARY, (lx, cy - 130 + i * 3), (lx + 14, cy - 90), 2)
        pygame.draw.line(surf, C_SECONDARY, (lx, cy + 130 - i * 3), (lx + 14, cy + 90), 2)

    # Venturi Floor edge wings & floor fences
    pygame.draw.line(surf, C_ACCENT, (cx - 70, cy - 155), (cx + 170, cy - 135), 4)
    pygame.draw.line(surf, C_ACCENT, (cx - 70, cy + 155), (cx + 170, cy + 135), 4)

    # 6. COCKPIT, HALO & AIRBOX
    # Cockpit opening
    cockpit_rect = pygame.Rect(cx - 100, cy - 34, 130, 68)
    pygame.draw.ellipse(surf, (8, 12, 18), cockpit_rect)
    pygame.draw.ellipse(surf, C_SECONDARY, cockpit_rect, width=2)

    # Steering wheel & seat contour
    pygame.draw.arc(surf, (255, 215, 0), (cx - 85, cy - 18, 28, 36), -1.2, 1.2, 3)
    pygame.draw.ellipse(surf, (25, 35, 48), (cx - 40, cy - 20, 50, 40))

    # Titanium Halo Safety Structure (3-point triangle)
    halo_apex = (cx - 10, cy)
    halo_left = (cx - 95, cy - 28)
    halo_right = (cx - 95, cy + 28)
    pygame.draw.line(surf, (220, 240, 255), (cx - 85, cy), halo_apex, 5)
    pygame.draw.line(surf, (200, 220, 255), halo_apex, halo_left, 4)
    pygame.draw.line(surf, (200, 220, 255), halo_apex, halo_right, 4)

    # Roll Hoop Engine Airbox Intake
    airbox_rect = pygame.Rect(cx + 28, cy - 24, 48, 48)
    pygame.draw.ellipse(surf, (6, 9, 14), airbox_rect)
    pygame.draw.ellipse(surf, C_OUTLINE, airbox_rect, width=3)
    pygame.draw.line(surf, C_ACCENT, (cx + 52, cy - 22), (cx + 52, cy + 22), 2)

    # Shark Fin Engine Cover Stabilizer
    pygame.draw.line(surf, C_ACCENT, (cx + 70, cy), (rear_x - 90, cy), 3)

    # 7. REAR SUSPENSION & DRIVE SHAFTS
    r_hub_top = (rw_x + rwheel_w // 2, cy - 160)
    r_hub_bot = (rw_x + rwheel_w // 2, cy + 160)
    chassis_r_top1 = (rw_x - 70, cy - 48)
    chassis_r_top2 = (rw_x + 50, cy - 35)
    chassis_r_bot1 = (rw_x - 70, cy + 48)
    chassis_r_bot2 = (rw_x + 50, cy + 35)

    for h_pt, c1, c2 in [(r_hub_top, chassis_r_top1, chassis_r_top2), (r_hub_bot, chassis_r_bot1, chassis_r_bot2)]:
        pygame.draw.line(surf, sus_col, h_pt, c1, 3)
        pygame.draw.line(surf, sus_col, h_pt, c2, 3)
        # Drive half-shaft
        pygame.draw.line(surf, (255, 140, 40), h_pt, (c1[0] + 40, (c1[1] + c2[1]) // 2), 2)

    # 8. REAR WING, BEAM WING & DIFFUSER
    # Beam Wing
    pygame.draw.line(surf, C_SECONDARY, (rear_x - 90, cy - 90), (rear_x - 90, cy + 90), 4)

    # Main Rear Wing & DRS Flap Assembly
    rw_span = 190
    rw_rect = pygame.Rect(rear_x - 70, cy - rw_span, 55, rw_span * 2)
    pygame.draw.rect(surf, C_BODY_FILL, rw_rect, border_radius=4)
    pygame.draw.rect(surf, C_OUTLINE, rw_rect, width=3, border_radius=4)

    # DRS Actuator Pod (Center)
    pygame.draw.rect(surf, (255, 255, 255), (rear_x - 65, cy - 14, 32, 28), border_radius=3)

    # Rear Wing Endplates
    pygame.draw.rect(surf, C_ACCENT, (rear_x - 85, cy - rw_span - 6, 75, 12), border_radius=3)
    pygame.draw.rect(surf, C_ACCENT, (rear_x - 85, cy + rw_span - 6, 75, 12), border_radius=3)

    # Central Exhaust Tailpipe & Rain Light
    pygame.draw.circle(surf, (255, 100, 30), (rear_x - 15, cy), 11)
    pygame.draw.circle(surf, (15, 20, 28), (rear_x - 15, cy), 8)
    pygame.draw.rect(surf, (255, 30, 30), (rear_x - 5, cy - 6, 12, 12), border_radius=2)

    # Save to file
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    pygame.image.save(surf, output_path)
    print(f"Successfully generated high-definition formula car blueprint: {output_path} ({W}x{H})")


if __name__ == "__main__":
    generate_formula_car_blueprint()
