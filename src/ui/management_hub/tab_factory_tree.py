from typing import Any, Dict, List, Optional, Set, Tuple

import networkx as nx
import pygame

from ...management.engineering_manager import EngineeringManager
from ...management.game_manager import GameManager
from ..icons import UIIcons
from ..theme import UITheme


class FactoryTreeTab:
    """
    Visual Node Tree Graph for Factory Facilities & Sub-Departments.
    Total Open Construction Freedom with realistic upfront capital scaling.
    Allows building, upgrading, granular monthly sub-budget controls,
    and clicking into any facility to inspect, configure, and manage 5-15 specialized equipment items.
    """

    # 7 Fundamental Car Components: (Category, 2-Letter Code, Lucide Icon, Full Display Name)
    CAR_PARTS: List[Tuple[str, str, str, str]] = [
        ("FRONT_WING", "FW", "wind", "Front Wing"),
        ("REAR_WING", "RW", "flag", "Rear Wing"),
        ("FLOOR", "FL", "layers", "Floor / Underbody"),
        ("SUSPENSION", "SU", "sliders", "Suspension"),
        ("BRAKES", "BR", "disc", "Brakes"),
        ("ENGINE", "EN", "cpu", "Engine / ICE"),
        ("ERS", "ER", "battery-charging", "ERS Hybrid"),
    ]

    @classmethod
    def get_facility_influenced_parts(cls, node_id: str) -> Set[str]:
        """Returns the set of car component categories directly influenced by this facility node."""
        from ...management.engineering_manager import RELEVANT_COMPONENT_FACILITIES

        influenced = set()
        for cat, fac_list in RELEVANT_COMPONENT_FACILITIES.items():
            if node_id in fac_list:
                influenced.add(cat)

        # Cross-cutting, specialized, and multi-part facilities
        multi_map: Dict[str, Set[str]] = {
            "eng_workshop": {"FRONT_WING", "REAR_WING", "FLOOR", "SUSPENSION", "BRAKES", "ENGINE", "ERS"},
            "test_qa_ndt": {"FRONT_WING", "REAR_WING", "FLOOR", "SUSPENSION", "BRAKES", "ENGINE", "ERS"},
            "mfg_rapid_proto": {"FRONT_WING", "REAR_WING", "FLOOR", "SUSPENSION", "BRAKES", "ENGINE", "ERS"},
            "track_telemetry": {"FRONT_WING", "REAR_WING", "FLOOR", "SUSPENSION", "BRAKES", "ENGINE", "ERS"},
            "track_comm_uplink": {"FRONT_WING", "REAR_WING", "FLOOR", "SUSPENSION", "BRAKES", "ENGINE", "ERS"},
            "eng_cad_office": {"FRONT_WING", "REAR_WING", "FLOOR", "SUSPENSION", "BRAKES"},
            "track_fast_repair": {"FRONT_WING", "REAR_WING", "FLOOR", "SUSPENSION", "BRAKES"},
            "track_setup_telemetry": {"FRONT_WING", "REAR_WING", "FLOOR", "SUSPENSION"},
            "track_virtual_sim": {"FRONT_WING", "REAR_WING", "FLOOR", "SUSPENSION"},
            "track_reverse_eng": {"FRONT_WING", "REAR_WING", "FLOOR"},
            "eng_aero_model_shop": {"FRONT_WING", "REAR_WING", "FLOOR"},
            "mfg_cleanroom_autoclave": {"FRONT_WING", "REAR_WING", "FLOOR", "SUSPENSION"},
            "mfg_paint_bay": {"FRONT_WING", "REAR_WING", "FLOOR"},
            "mfg_prepreg_freezer": {"FRONT_WING", "REAR_WING", "FLOOR"},
            "mfg_rapid_tooling": {"FRONT_WING", "REAR_WING", "FLOOR"},
            "eng_works_powertrain": {"ENGINE", "ERS"},
            "mfg_additive_metal": {"SUSPENSION", "BRAKES", "ENGINE", "ERS"},
            "mfg_cnc_machining": {"SUSPENSION", "BRAKES", "ENGINE"},
            "eng_comp_materials": {"SUSPENSION", "BRAKES", "FLOOR"},
            "eng_kinematics_lab": {"SUSPENSION", "BRAKES"},
            "test_shaker_rig": {"SUSPENSION", "FLOOR"},
            "test_torsional_rig": {"SUSPENSION"},
            "track_sim_rig": {"SUSPENSION"},
        }
        if node_id in multi_map:
            influenced.update(multi_map[node_id])

        return influenced

    def _draw_parts_grid(
        self,
        surface: pygame.Surface,
        x: float,
        y: float,
        width: float,
        height: float,
        influenced_parts: Set[str],
        is_unlocked: bool,
    ):
        """
        Renders a crisp 7-slot mini grid of all car components on the facility card,
        vibrantly highlighting the parts directly influenced by this facility.
        """
        num_parts = len(self.CAR_PARTS)
        gap = max(1.0, 2.0 * self.zoom)
        total_gaps = (num_parts - 1) * gap
        chip_w = (width - total_gaps) / num_parts

        for idx, (cat, code, icon_name, full_name) in enumerate(self.CAR_PARTS):
            cx = x + idx * (chip_w + gap)
            chip_rect = pygame.Rect(int(cx), int(y), int(chip_w), int(height))

            is_influenced = cat in influenced_parts

            if is_influenced:
                if is_unlocked:
                    bg_col = (14, 42, 54)
                    border_col = (0, 220, 220)
                    icon_col = (0, 245, 255)
                    text_col = (255, 255, 255)
                else:
                    # Unbuilt facility: golden amber preview of future influenced parts
                    bg_col = (36, 30, 16)
                    border_col = (230, 180, 50)
                    icon_col = (255, 205, 70)
                    text_col = (240, 230, 200)
            else:
                bg_col = (14, 18, 24)
                border_col = (28, 34, 44)
                icon_col = (50, 60, 72)
                text_col = (55, 65, 78)

            pygame.draw.rect(surface, bg_col, chip_rect, border_radius=2)
            pygame.draw.rect(surface, border_col, chip_rect, width=1, border_radius=2)

            # Draw icon and code
            ic_size = max(8, int(10 * self.zoom))
            ic_surf = UIIcons.get_icon(icon_name, size=ic_size, color=icon_col)
            txt_surf = self.font_mini.render(code, True, text_col)

            # Center icon + text inside the chip
            total_w = ic_surf.get_width() + 2 + txt_surf.get_width()
            start_ix = chip_rect.x + max(2, (chip_rect.width - total_w) // 2)
            surface.blit(ic_surf, (start_ix, chip_rect.y + (chip_rect.height - ic_surf.get_height()) // 2))
            surface.blit(
                txt_surf,
                (start_ix + ic_surf.get_width() + 2, chip_rect.y + (chip_rect.height - txt_surf.get_height()) // 2),
            )

    def __init__(self, screen_width: int, screen_height: int):
        self.width = screen_width
        self.height = screen_height

        self.selected_dept: str = "ALL"
        self._init_fonts()

        # Pan & Zoom Camera
        self.pan_x: float = 40.0
        self.pan_y: float = 130.0
        self.zoom: float = 1.0
        self.is_dragging: bool = False
        self.drag_start: Tuple[int, int] = (0, 0)

        # Department Equipment & Personnel Inspector Drawer
        self.inspected_node_id: Optional[str] = None
        self.inspector_tab: str = "EQUIPMENT"  # 'EQUIPMENT' or 'STAFF'
        self.inspector_scroll_y: float = 0.0
        self.requested_hiring_target: Optional[Tuple[str, str, str]] = None

        self.status_message: str = (
            "Click any facility node to inspect its specialized equipment, staff roster, and budget!"
        )

        # Build NetworkX Graph
        self.graph = nx.DiGraph()
        self.node_positions: Dict[str, Tuple[float, float]] = {}
        self._build_graph_layout()

    def _init_fonts(self):
        self.font_title = UITheme.get_font(13, bold=True)
        self.font_card_title = UITheme.get_font(12, bold=True)
        self.font_body = UITheme.get_font(11, bold=False)
        self.font_badge = UITheme.get_font(10, bold=True)
        self.font_btn = UITheme.get_font(10, bold=True)
        self.font_mini = UITheme.get_font(8, bold=True)

    def resize(self, width: int, height: int):
        self.width = width
        self.height = height
        self._init_fonts()

    def _build_graph_layout(self, db: Optional[Any] = None):
        """
        Dynamically constructs NetworkX DAG and calculates clean hierarchical layout coordinates
        from any database input (supports custom modded facilities and arbitrary department trees).
        """
        self.graph.clear()
        self.node_positions.clear()

        # Fetch nodes from DB if available, else use fallback definitions
        nodes_data = []
        if db:
            try:
                with db.get_connection() as conn:
                    cur = conn.cursor()
                    cur.execute(
                        "SELECT id, department, name, description, parent_id, tier, max_tier, base_cost, base_upkeep FROM facility_nodes;"
                    )
                    nodes_data = [dict(r) for r in cur.fetchall()]
            except Exception:
                nodes_data = []

        if not nodes_data:
            from ...database.career_db import ALL_FACILITY_NODES

            nodes_data = [
                {"id": n[0], "department": n[1], "name": n[2], "description": n[3], "parent_id": n[4]}
                for n in ALL_FACILITY_NODES
            ]

        # 1. Populate graph nodes and parent-child edges
        node_dict = {n["id"]: n for n in nodes_data}
        for n in nodes_data:
            dept = n.get("department", "GENERAL")
            self.graph.add_node(n["id"], department=dept, data=n)
            if n.get("parent_id") and n["parent_id"] in node_dict:
                self.graph.add_edge(n["parent_id"], n["id"])

        # 2. Group nodes by Department
        dept_order_pref = [
            "ENGINEERING",
            "MANUFACTURING",
            "TESTING",
            "POWERTRAIN",
            "MARKETING",
            "HR",
            "TRACKSIDE",
            "DRIVER_PERF",
            "MANAGEMENT",
        ]
        dept_nodes = {}
        for n in nodes_data:
            dept = n.get("department", "GENERAL")
            if dept not in dept_nodes:
                dept_nodes[dept] = []
            dept_nodes[dept].append(n["id"])

        sorted_depts = sorted(
            dept_nodes.keys(), key=lambda d: dept_order_pref.index(d) if d in dept_order_pref else 999
        )

        # 3. Calculate topological depth (column X) for every node
        depths = {}
        for n_id in self.graph.nodes:
            p_id = node_dict.get(n_id, {}).get("parent_id")
            if not p_id:
                depths[n_id] = 0
            else:
                ancestor_depth = 0
                curr = p_id
                visited = set()
                while curr and curr not in visited and curr in node_dict:
                    visited.add(curr)
                    ancestor_depth += 1
                    curr = node_dict[curr].get("parent_id")
                depths[n_id] = ancestor_depth

        # Specific adjustments for multi-layer apex / late-stage nodes
        apex_overrides = {
            "eng_windtunnel": 3,
            "eng_floor": 4,
            "mfg_paint_bay": 4,
            "eng_works_powertrain": 4,
            "test_torsional_rig": 4,
            "mkt_heritage": 4,
            "mkt_customer_racing": 4,
            "hr_workforce_optimizer": 3,
            "hr_wellness_center": 2,
            "hr_equipment_procurement": 2,
        }

        for k, v in apex_overrides.items():
            if k in depths:
                depths[k] = v

        node_w_spacing = 330.0  # Generous 80px horizontal gap for smooth Bézier curve runway
        node_h_spacing = 145.0  # Generous vertical gap between rows for clean distinction

        # 4. Lay out departments vertically with clean row offsets & crossing minimization
        current_y_offset = 0.0

        for dept in sorted_depts:
            d_nodes = dept_nodes[dept]
            cols = {}
            for nid in d_nodes:
                col = depths.get(nid, 0)
                if col not in cols:
                    cols[col] = []
                cols[col].append(nid)

            max_rows_in_dept = max(len(row_list) for row_list in cols.values()) if cols else 1

            # Sort each column's nodes by average y-position of their predecessors in the graph
            all_cols = sorted(cols.keys())
            for col in all_cols:
                nids = cols[col]
                if col > 0:

                    def get_parent_order(nid):
                        parents = [p for p in self.graph.predecessors(nid) if p in self.node_positions]
                        if parents:
                            return sum(self.node_positions[p][1] for p in parents) / len(parents)
                        return 0.0

                    nids = sorted(nids, key=get_parent_order)
                    cols[col] = nids

                for r_idx, nid in enumerate(nids):
                    vert_shift = (max_rows_in_dept - len(nids)) * 0.4
                    row_y = current_y_offset + r_idx + vert_shift
                    self.node_positions[nid] = (col * node_w_spacing, row_y * node_h_spacing)

            current_y_offset += max_rows_in_dept + 0.6  # padding between departments

    def _draw_bezier_edge(
        self,
        surface: pygame.Surface,
        p1: Tuple[float, float],
        p2: Tuple[float, float],
        color: Tuple[int, int, int],
        width: int,
    ):
        """Draws a sleek anti-aliased cubic Bézier curve with directional flow arrows entering child ports."""
        x1, y1 = p1
        x2, y2 = p2

        dx = max(40.0, abs(x2 - x1) * 0.5)
        cx1 = x1 + dx
        cy1 = y1
        cx2 = x2 - dx
        cy2 = y2

        # Generate smooth curve points
        num_steps = 22
        pts = []
        for step in range(num_steps + 1):
            t = step / float(num_steps)
            inv_t = 1.0 - t
            bx = (inv_t**3) * x1 + 3 * (inv_t**2) * t * cx1 + 3 * inv_t * (t**2) * cx2 + (t**3) * x2
            by = (inv_t**3) * y1 + 3 * (inv_t**2) * t * cy1 + 3 * inv_t * (t**2) * cy2 + (t**3) * y2
            pts.append((bx, by))

        pygame.draw.lines(surface, color, False, pts, width)

        # Source connection port dot
        dot_r = max(2, int(3.5 * self.zoom))
        pygame.draw.circle(surface, color, (int(x1), int(y1)), dot_r)

        # Directional Arrowhead entering target node
        arrow_len = max(7.0, 9.0 * self.zoom)
        arrow_half_w = max(4.0, 6.0 * self.zoom)
        arrow_pts = [
            (int(x2), int(y2)),
            (int(x2 - arrow_len), int(y2 - arrow_half_w)),
            (int(x2 - arrow_len * 0.7), int(y2)),
            (int(x2 - arrow_len), int(y2 + arrow_half_w)),
        ]
        pygame.draw.polygon(surface, color, arrow_pts)

        # Midpoint directional flow marker on longer spans
        if len(pts) > 12 and abs(x2 - x1) > 120 * self.zoom:
            mid_idx = len(pts) // 2
            mx_pt, my_pt = pts[mid_idx]
            m_arrow = [
                (int(mx_pt + 3 * self.zoom), int(my_pt)),
                (int(mx_pt - 4 * self.zoom), int(my_pt - 4 * self.zoom)),
                (int(mx_pt - 2 * self.zoom), int(my_pt)),
                (int(mx_pt - 4 * self.zoom), int(my_pt + 4 * self.zoom)),
            ]
            pygame.draw.polygon(surface, color, m_arrow)

    def _dept_matches(self, node_dept: str, selected_dept: str) -> bool:
        """Checks if a node's department matches the filter, supporting aliases like COMMERCIAL/MARKETING."""
        if selected_dept == "ALL":
            return True
        if selected_dept in ("COMMERCIAL", "MARKETING") and node_dept in ("COMMERCIAL", "MARKETING"):
            return True
        return node_dept == selected_dept

    def _can_build_node(self, node_id: str, facilities: Dict[str, Any]) -> Tuple[bool, str]:
        """Checks if all prerequisite parent facilities are unlocked and built."""
        fac = facilities.get(node_id, {})
        parent_id = fac.get("parent_id") or (
            self.graph.nodes.get(node_id, {}).get("parent_id") if node_id in self.graph else None
        )
        if parent_id:
            p_f = facilities.get(parent_id, {})
            if not p_f.get("is_unlocked") or (p_f.get("current_tier") or 0) < 1:
                p_name = p_f.get("name") or parent_id
                return False, f"Requires {p_name}"
        return True, ""

    def get_department_tabs(self) -> List[Tuple[str, str]]:
        """Dynamically discovers all departments present in the DAG + ALL tab."""
        concise = (self.width - 48) // 10 < 115
        if concise:
            dept_labels = {
                "ALL": "ALL",
                "ENGINEERING": "AERO",
                "MANUFACTURING": "MFG",
                "TESTING": "TESTS",
                "POWERTRAIN": "PU",
                "COMMERCIAL": "COMM",
                "MARKETING": "COMM",
                "HR": "HR",
                "TRACKSIDE": "TRACK",
                "DRIVER_PERF": "DRV",
                "MANAGEMENT": "MGMT",
            }
        else:
            dept_labels = {
                "ALL": "ALL DEPARTMENTS",
                "ENGINEERING": "AERO & R&D",
                "MANUFACTURING": "MANUFACTURING",
                "TESTING": "TESTING & RIGS",
                "POWERTRAIN": "POWERTRAIN",
                "COMMERCIAL": "COMMERCIAL",
                "MARKETING": "COMMERCIAL",
                "HR": "HR & WELFARE",
                "TRACKSIDE": "TRACKSIDE",
                "DRIVER_PERF": "DRIVER PERF",
                "MANAGEMENT": "MANAGEMENT",
            }
        unique_depts = []
        for _, data in self.graph.nodes(data=True):
            d = data.get("department", "GENERAL")
            if d == "MARKETING":
                d = "COMMERCIAL"
            if d not in unique_depts:
                unique_depts.append(d)

        pref = [
            "ENGINEERING",
            "MANUFACTURING",
            "TESTING",
            "POWERTRAIN",
            "COMMERCIAL",
            "HR",
            "TRACKSIDE",
            "DRIVER_PERF",
            "MANAGEMENT",
        ]
        sorted_depts = sorted(unique_depts, key=lambda d: pref.index(d) if d in pref else 999)

        all_lbl = "ALL" if concise else "ALL DEPARTMENTS"
        tabs = [("ALL", all_lbl)]
        for d in sorted_depts:
            tabs.append((d, dept_labels.get(d, d.replace("_", " ").upper())))
        return tabs

    def _truncate_text(self, font: pygame.font.Font, text: str, max_w: float) -> str:
        """Truncates text with ellipsis if it exceeds maximum pixel width."""
        if max_w <= 10:
            return ""
        if font.size(text)[0] <= max_w:
            return text
        t = text
        while len(t) > 2 and font.size(t + "...")[0] > max_w:
            t = t[:-1]
        return t + "..."

    def _get_facility_benefit_info(
        self,
        node_id: str,
        dept: str,
        description: str,
        tier: Optional[int],
        is_unlocked: bool,
        eq_items: List[Dict[str, Any]],
        gm: GameManager,
        dev_gain_mult: float = 1.0,
        negative_penalty_mult: float = 1.0,
    ) -> Dict[str, Any]:
        """Dynamically computes unique authentic benefits, passive revenues, marketability, or component perf/rel rates scaled by staff performance (0.0 to 5.0x)."""
        safe_tier = int(tier or 1)
        t_val = max(1, safe_tier) if is_unlocked else 1
        tier = safe_tier

        # Staff Multiplier (0.0 when unstaffed, up to 5.0x with star specialists & leadership)
        staff_mult = 1.0
        is_unstaffed = False
        if gm and hasattr(gm, "staff_manager") and hasattr(gm, "team_id"):
            try:
                s_out = gm.staff_manager.calculate_facility_staff_output(
                    gm.team_id, node_id, tier if is_unlocked else 1, dev_gain_mult
                )
                staff_mult = s_out.get("staff_mult", 1.0)
                is_unstaffed = s_out.get("is_unstaffed", False)
            except Exception:
                staff_mult = 1.0
                is_unstaffed = False

        # 1. Commercial / Marketing nodes (Massive Marketability & Appeal Drivers)
        if node_id == "mkt_press":
            mkt = 4 * t_val

            return {
                "type": "COMMERCIAL",
                "tag": "MARKETABILITY",
                "tag_color": (0, 220, 255),
                "benefit_str": f"Marketability: +{mkt} | Media PR",
                "detail_str": f"Tier {t_val}: Press sentiment & reputation buffer",
                "insp_title": "PRESS OFFICE & PUBLIC RELATIONS:",
                "insp_line1": f"Marketability Rating: +{mkt} Points to Team Reach",
                "insp_line2": "Crisis Communications: Protects team reputation after poor races",
                "insp_line3": f"ON TIER {t_val + 1} UPGRADE: Marketability bonus increases to +{4 * (t_val + 1)}"
                if t_val < 3
                else "[ MAXIMUM TIER 3 REACHED ]",
            }
        elif node_id == "mkt_brand_design":
            mkt = 6 * t_val
            val = 5 * t_val
            return {
                "type": "COMMERCIAL",
                "tag": "SPONSOR VALUE",
                "tag_color": (255, 180, 40),
                "benefit_str": f"Marketability: +{mkt} | +{val}% Sponsor Value",
                "detail_str": f"Tier {t_val}: Livery styling & decal cash boost",
                "insp_title": "BRAND STRATEGY & LIVERY DESIGN:",
                "insp_line1": f"Sponsor Multiplier: +{val}% extra cash on all sponsor deals",
                "insp_line2": f"Marketability Bonus: +{mkt} Points to Team Reach",
                "insp_line3": f"ON TIER {t_val + 1} UPGRADE: Multiplier increases to +{5 * (t_val + 1)}%"
                if t_val < 3
                else "[ MAXIMUM TIER 3 REACHED ]",
            }
        elif node_id == "mkt_digital":
            mkt = 8 * t_val
            return {
                "type": "COMMERCIAL",
                "tag": "MARKETABILITY",
                "tag_color": (0, 220, 255),
                "benefit_str": f"Marketability: +{mkt} Viral Reach",
                "detail_str": f"Tier {t_val}: Real-time race weekend fan channels",
                "insp_title": "DIGITAL & SOCIAL MEDIA IMPACT:",
                "insp_line1": f"Marketability Bonus: +{mkt} Points to Team Reach",
                "insp_line2": "Viral Social Growth: Significantly boosts sponsor appeal rating",
                "insp_line3": f"ON TIER {t_val + 1} UPGRADE: Marketability bonus increases to +{8 * (t_val + 1)}"
                if t_val < 3
                else "[ MAXIMUM TIER 3 REACHED ]",
            }
        elif node_id == "mkt_merch":
            mkt = 5 * t_val
            return {
                "type": "COMMERCIAL",
                "tag": "MARKETABILITY",
                "tag_color": (0, 240, 140),
                "benefit_str": f"Marketability: +{mkt} | Retail Gear",
                "detail_str": f"Tier {t_val}: Performance-scaled retail side income",
                "insp_title": "MERCHANDISE & OFFICIAL TEAM APPAREL:",
                "insp_line1": f"Marketability Rating: +{mkt} Points from fan apparel in grandstands",
                "insp_line2": "Side Income: Generates modest monthly profit scaled by race performance",
                "insp_line3": f"ON TIER {t_val + 1} UPGRADE: Marketability bonus increases to +{5 * (t_val + 1)}"
                if t_val < 3
                else "[ MAXIMUM TIER 3 REACHED ]",
            }
        elif node_id == "mkt_fan_club":
            mkt = 5 * t_val
            return {
                "type": "COMMERCIAL",
                "tag": "MARKETABILITY",
                "tag_color": (0, 240, 140),
                "benefit_str": f"Marketability: +{mkt} | Fan Club",
                "detail_str": f"Tier {t_val}: Performance-scaled member dues",
                "insp_title": "FAN CLUB & COMMUNITY LOYALTY:",
                "insp_line1": f"Marketability Rating: +{mkt} Points from dedicated global fan base",
                "insp_line2": "Side Income: Member subscription dues scaled by team success",
                "insp_line3": f"ON TIER {t_val + 1} UPGRADE: Marketability bonus increases to +{5 * (t_val + 1)}"
                if t_val < 3
                else "[ MAXIMUM TIER 3 REACHED ]",
            }
        elif node_id == "mkt_studio":
            mkt = 12 * t_val
            return {
                "type": "COMMERCIAL",
                "tag": "MARKETABILITY",
                "tag_color": (0, 220, 255),
                "benefit_str": f"Marketability: +{mkt} | Docuseries",
                "detail_str": f"Tier {t_val}: Season car launches & media soundstage",
                "insp_title": "MEDIA BROADCAST STUDIO & SOUNDSTAGE:",
                "insp_line1": f"Marketability Surge: +{mkt} Points from broadcast docuseries",
                "insp_line2": "Fan Attachment: Increases fan engagement and sponsor visibility",
                "insp_line3": f"ON TIER {t_val + 1} UPGRADE: Marketability bonus increases to +{12 * (t_val + 1)}"
                if t_val < 3
                else "[ MAXIMUM TIER 3 REACHED ]",
            }
        elif node_id == "mkt_hospitality":
            app = 10 * t_val
            return {
                "type": "COMMERCIAL",
                "tag": "SPONSOR APPEAL",
                "tag_color": (255, 215, 0),
                "benefit_str": f"Sponsor Appeal: +{app} VIP",
                "detail_str": f"Tier {t_val}: Paddock Club executive suites",
                "insp_title": "VIP PADDOCK CLUB & EXECUTIVE HOSPITALITY:",
                "insp_line1": f"Sponsor Appeal Rating: +{app} Points to corporate appeal",
                "insp_line2": "Executive Suites: Unlocks high-tier tier-1 multi-million sponsor deals",
                "insp_line3": f"ON TIER {t_val + 1} UPGRADE: Sponsor appeal bonus increases to +{10 * (t_val + 1)}"
                if t_val < 3
                else "[ MAXIMUM TIER 3 REACHED ]",
            }
        elif node_id == "mkt_licensing":
            mkt = 6 * t_val
            return {
                "type": "COMMERCIAL",
                "tag": "ROYALTIES",
                "tag_color": (0, 240, 140),
                "benefit_str": f"Marketability: +{mkt} | CAD Royalties",
                "detail_str": f"Tier {t_val}: Diecast & gaming licensing cash",
                "insp_title": "BRAND LICENSING & IP PARTNERSHIPS:",
                "insp_line1": f"Marketability Rating: +{mkt} Points to Global Brand IP",
                "insp_line2": "IP Royalties: Steady monthly royalties from scale models & video games",
                "insp_line3": f"ON TIER {t_val + 1} UPGRADE: Marketability bonus increases to +{6 * (t_val + 1)}"
                if t_val < 3
                else "[ MAXIMUM TIER 3 REACHED ]",
            }
        elif node_id == "mkt_esports":
            mkt = 6 * t_val
            return {
                "type": "COMMERCIAL",
                "tag": "MARKETABILITY",
                "tag_color": (0, 220, 255),
                "benefit_str": f"Marketability: +{mkt} | Sim Rigs",
                "detail_str": f"Tier {t_val}: Virtual team & live streams",
                "insp_title": "ESPORTS RACING RIG & STREAMING CHANNELS:",
                "insp_line1": f"Marketability Rating: +{mkt} Points from youth & sim racing fans",
                "insp_line2": "Youth Demographic: Expands team appeal across younger motorsport fans",
                "insp_line3": f"ON TIER {t_val + 1} UPGRADE: Marketability bonus increases to +{6 * (t_val + 1)}"
                if t_val < 3
                else "[ MAXIMUM TIER 3 REACHED ]",
            }
        elif node_id == "mkt_heritage":
            mkt = 8 * t_val
            return {
                "type": "COMMERCIAL",
                "tag": "HERITAGE",
                "tag_color": (255, 215, 0),
                "benefit_str": f"Marketability: +{mkt} | Museum",
                "detail_str": f"Tier {t_val}: Trophy hall & heritage admission profits",
                "insp_title": "HERITAGE TROPHY MUSEUM & ARCHIVE:",
                "insp_line1": f"Marketability Base: +{mkt} Points to team prestige",
                "insp_line2": "Legacy Exhibition: Dynamic museum entry fees scale with team race wins",
                "insp_line3": "Scales dynamically (+4 pts per championship title won)!",
            }
        elif node_id == "mkt_customer_racing":
            app = 15 * t_val
            return {
                "type": "COMMERCIAL",
                "tag": "PRESTIGE",
                "tag_color": (255, 215, 0),
                "benefit_str": f"Sponsor Appeal: +{app} Prestige",
                "detail_str": f"Tier {t_val}: VIP client track days & car sales",
                "insp_title": "CUSTOMER RACING & CLIENT SALES:",
                "insp_line1": f"Elite Prestige Bonus: +{app} Sponsor Appeal Points",
                "insp_line2": "VIP Track Days: Track days for high-net-worth clients provide modest side profits",
                "insp_line3": f"ON TIER {t_val + 1} UPGRADE: Sponsor appeal bonus increases to +{15 * (t_val + 1)}"
                if t_val < 3
                else "[ MAXIMUM TIER 3 REACHED ]",
            }

        # 2. HR & Workforce Automation Nodes
        elif node_id == "hr_recruitment":
            t_desc = (
                "T1: Auto-Fills Open Specialist Desks"
                if t_val == 1
                else "T2: Auto-Intern Pipeline ($2k Min-Wage Check)"
            )
            return {
                "type": "HR",
                "tag": "RECRUITMENT",
                "tag_color": (255, 120, 200),
                "benefit_str": t_desc,
                "detail_str": f"Tier {t_val}: Automated specialist hiring & European intern pipeline",
                "insp_title": "RECRUITMENT & HIRING BUREAU (Tier 1 & 2):",
                "insp_line1": "Tier 1: Automatically recruits best-matching applicants into open facility desks",
                "insp_line2": "Tier 2: Automatically assigns 6-mo intern tryouts (with $2k reserve) & signs top potential",
                "insp_line3": "ON TIER 2 UPGRADE: Unlocks automated European intern tryouts & graduation signing"
                if t_val < 2
                else "[ MAXIMUM TIER 2 REACHED ]",
            }
        elif node_id == "hr_headhunting" or node_id == "hr_headhunter":
            return {
                "type": "HR",
                "tag": "POACHING",
                "tag_color": (255, 120, 200),
                "benefit_str": "Auto-Headhunter Delegation",
                "detail_str": f"Tier {t_val}: Autonomous rival paddock scouting & poaching",
                "insp_title": "EXECUTIVE HEADHUNTING BUREAU:",
                "insp_line1": "Autonomous Poaching: Scouts rival paddocks for best-value engineers & directors",
                "insp_line2": "Strategic Talent Acquisition: Fills under-leveraged posts within payroll budget",
                "insp_line3": f"Tier {t_val} Bureau: Scans deeper rival paddock candidate tiers",
            }
        elif node_id == "hr_payroll":
            return {
                "type": "HR",
                "tag": "PAYROLL",
                "tag_color": (0, 240, 140),
                "benefit_str": "Auto-Payroll Calibration",
                "detail_str": f"Tier {t_val}: Auto-adjusts wages to market value within budget",
                "insp_title": "PAYROLL & WAGE CALIBRATION DESK:",
                "insp_line1": "Wage Calibration: Automatically grants market raises when room budget allows",
                "insp_line2": "Morale Retention: Guarantees 100% morale satisfaction and prevents resignations",
                "insp_line3": f"Tier {t_val} Desk: Real-time market wage index tracking",
            }
        elif node_id == "hr_teambuilding" or node_id == "hr_welfare":
            return {
                "type": "HR",
                "tag": "WELFARE",
                "tag_color": (255, 120, 200),
                "benefit_str": f"Culture & Morale Buffer (+{2 * t_val} Morale)",
                "detail_str": f"Tier {t_val}: Buffers underpaid wage discontent (25-35%)",
                "insp_title": "TEAM CULTURE & WELFARE COMPLEX:",
                "insp_line1": f"Wage Discontent Buffer: Underpaid staff tolerate up to {20 + 6 * t_val}% wage deficits",
                "insp_line2": "Morale Recovery: Weekly morale regeneration boosted across all personnel",
                "insp_line3": f"ON TIER {t_val + 1} UPGRADE: Buffer increases by an additional +6%"
                if t_val < 3
                else "[ MAXIMUM TIER 3 REACHED ]",
            }
        elif node_id == "hr_leadership_institute":
            return {
                "type": "HR",
                "tag": "LEADERSHIP",
                "tag_color": (255, 180, 220),
                "benefit_str": f"+{18 * t_val}% Weekly Head/Director XP",
                "detail_str": f"Tier {t_val}: Leadership & Communication training",
                "insp_title": "LEADERSHIP DEVELOPMENT INSTITUTE:",
                "insp_line1": f"Management Growth: Accelerates weekly Leadership (+{0.18 * t_val:.2f}) & Comm (+{0.14 * t_val:.2f})",
                "insp_line2": "Synergy Multiplier: Strengthens Department Head coordination and Category Director boost",
                "insp_line3": f"ON TIER {t_val + 1} UPGRADE: Growth multiplier increases to +{18 * (t_val + 1)}%"
                if t_val < 3
                else "[ MAXIMUM TIER 3 REACHED ]",
            }
        elif node_id == "hr_performance_review":
            clarity = "Exact Stats" if t_val >= 3 else ("±4 pts" if t_val == 2 else "±10 pts")
            return {
                "type": "HR",
                "tag": "SCOUTING",
                "tag_color": (0, 220, 255),
                "benefit_str": f"Stat Clarity: {clarity}",
                "detail_str": f"Tier {t_val}: Narrows Fog-of-War scouting uncertainty",
                "insp_title": "PERFORMANCE REVIEW & ANALYTICS LAB:",
                "insp_line1": f"Fog-of-War Clarity: Narrows candidate and staff stat ranges (Current: {clarity})",
                "insp_line2": "Scouting Precision: Eliminates guesswork when evaluating potential prospects",
                "insp_line3": "ON TIER 3 UPGRADE: Unlocks 100% exact effective stat clarity"
                if t_val < 3
                else "[ MAXIMUM TIER 3 REACHED: 100% EXACT CLARITY ]",
            }
        elif node_id == "hr_performance_cull":
            return {
                "type": "HR",
                "tag": "RETENTION",
                "tag_color": (255, 80, 80),
                "benefit_str": "Demographic Age-Curve Cull",
                "detail_str": f"Tier {t_val}: Auto-dismisses severe underperformers",
                "insp_title": "TALENT RETENTION & EXIT REVIEW:",
                "insp_line1": "Age-Curve Benchmarking: Evaluates performance against demographic peak curve",
                "insp_line2": "Budget Protection: Automatically dismisses underperforming elder dead weight",
                "insp_line3": f"Tier {t_val} Review: Automated severance and contract termination",
            }
        elif node_id == "hr_tech_academy":
            return {
                "type": "HR",
                "tag": "R&D TRAINING",
                "tag_color": (0, 220, 255),
                "benefit_str": f"+{12 * t_val}% Engineering Growth",
                "detail_str": f"Tier {t_val}: Weekly Engineering stat & potential gain",
                "insp_title": "TECHNICAL ENGINEERING ACADEMY:",
                "insp_line1": f"Engineering Mastery: Accelerates weekly Engineering stat gains (+{0.12 * t_val:.2f}/wk)",
                "insp_line2": "Potential Realization: Converts hidden potential into active engineering skill",
                "insp_line3": f"ON TIER {t_val + 1} UPGRADE: Growth multiplier increases to +{12 * (t_val + 1)}%"
                if t_val < 3
                else "[ MAXIMUM TIER 3 REACHED ]",
            }
        elif node_id == "hr_craft_workshop":
            return {
                "type": "HR",
                "tag": "CRAFT GUILD",
                "tag_color": (255, 180, 40),
                "benefit_str": f"+{12 * t_val}% Craftsmanship Growth",
                "detail_str": f"Tier {t_val}: Weekly Craftsmanship & Composure gain",
                "insp_title": "CRAFTSMANSHIP & MASTER GUILD:",
                "insp_line1": f"Fabrication Skill: Accelerates Craftsmanship (+{0.12 * t_val:.2f}/wk) & Composure (+{0.08 * t_val:.2f}/wk)",
                "insp_line2": "Manufacturing Quality: Boosts manufacturing and testing staff performance",
                "insp_line3": f"ON TIER {t_val + 1} UPGRADE: Growth multiplier increases to +{12 * (t_val + 1)}%"
                if t_val < 3
                else "[ MAXIMUM TIER 3 REACHED ]",
            }
        elif node_id == "hr_workforce_optimizer":
            return {
                "type": "HR",
                "tag": "OPTIMIZER",
                "tag_color": (0, 240, 140),
                "benefit_str": "Succession & Replacement Optimizer",
                "detail_str": f"Tier {t_val}: Auto-replaces staff for superior talent",
                "insp_title": "WORKFORCE SUCCESSION & OPTIMIZATION SUITE:",
                "insp_line1": "Continuous Upgrading: Scans recruitment queue for strictly superior specialists",
                "insp_line2": "Seamless Replacement: Replaces inferior staff for the same or lower wage",
                "insp_line3": f"Tier {t_val} Optimizer: Unlocks automated talent replacement heuristics",
            }
        elif node_id == "hr_wellness_center":
            return {
                "type": "HR",
                "tag": "LONGEVITY",
                "tag_color": (0, 240, 140),
                "benefit_str": "Peak Age 54 & -60% Age Decline",
                "detail_str": f"Tier {t_val}: Preserves veteran mastery & delays retirement",
                "insp_title": "STAFF WELLNESS & LONGEVITY CENTER:",
                "insp_line1": "Career Extension: Extends peak productivity age from 50 to 54",
                "insp_line2": "Decline Protection: Reduces post-50 stat degradation rate by 60%",
                "insp_line3": f"Tier {t_val} Wellness: Medical and ergonomic physical health suites",
            }
        elif node_id == "hr_equipment_procurement":
            return {
                "type": "HR",
                "tag": "PROCUREMENT",
                "tag_color": (180, 120, 255),
                "benefit_str": "Autonomous Rig Procurement",
                "detail_str": f"Tier {t_val}: Auto-buys rigs using Department Savings",
                "insp_title": "AUTONOMOUS RIG PROCUREMENT SUITE:",
                "insp_line1": "Autonomous Procurement: Automatically buys/upgrades equipment rigs using room savings",
                "insp_line2": "Treasury Protection: Never spends central team bank treasury",
                "insp_line3": f"Tier {t_val} Procurement: Automated equipment procurement algorithms",
            }
        elif node_id == "mgmt_boardroom":
            return {
                "type": "MANAGEMENT",
                "tag": "FACTORY LEADERSHIP",
                "tag_color": (180, 120, 255),
                "benefit_str": f"+{5 * t_val} Factory Leadership (+{0.15 * t_val:.2f}/wk)",
                "detail_str": f"Tier {t_val}: Universal leadership boost for all factory staff",
                "insp_title": "EXECUTIVE BOARDROOM & FACTORY LEADERSHIP:",
                "insp_line1": f"Universal Leadership Aura: +{5 * t_val} effective Leadership across all factory staff",
                "insp_line2": f"Weekly Development: +{0.15 * t_val:.2f}/wk Leadership progression for everyone in factory",
                "insp_line3": f"ON TIER {t_val + 1} UPGRADE: Leadership aura increases to +{5 * (t_val + 1)} (+{0.15 * (t_val + 1):.2f}/wk)"
                if t_val < 3
                else "[ MAXIMUM TIER 3 REACHED ]",
            }

        # 3. Trackside & Driver Performance
        elif node_id == "track_pitrig":
            return {
                "type": "TRACKSIDE",
                "tag": "PIT CREW",
                "tag_color": (0, 240, 140),
                "benefit_str": f"Pit Practice: -{0.15 * t_val:.2f}s Stop Time",
                "detail_str": f"Tier {t_val}: 12-man pit crew reaction training",
                "insp_title": "PIT CREW REACTION TRAINING RIG:",
                "insp_line1": f"Pit Stop Duration: Reduces baseline pit stop time by -{0.15 * t_val:.2f}s",
                "insp_line2": "Error Reduction: Decreases probability of pit crew mistakes / wheel jams",
                "insp_line3": f"ON TIER {t_val + 1} UPGRADE: Stop time discount increases to -{0.15 * (t_val + 1):.2f}s"
                if t_val < 3
                else "[ MAXIMUM TIER 3 REACHED ]",
            }
        elif node_id == "track_wheelguns":
            return {
                "type": "TRACKSIDE",
                "tag": "FAST PITS",
                "tag_color": (0, 240, 140),
                "benefit_str": "2.1s Pit Stops & Laser Alignment",
                "detail_str": f"Tier {t_val}: Carbon guns & laser hub lock",
                "insp_title": "CARBON ULTRA-FAST WHEELGUNS:",
                "insp_line1": "Elite Pit Speed: Unlocks sub-2.2s world-class pit stop capability",
                "insp_line2": "Laser Guidance: Optical alignment guides instant wheel-nut lock",
                "insp_line3": f"Tier {t_val} Hardware: Maximizes track position gained in pit lane",
            }
        elif node_id == "track_telemetry":
            return {
                "type": "TRACKSIDE",
                "tag": "RACE TELEMETRY",
                "tag_color": (0, 240, 140),
                "benefit_str": "Live Telemetry & Strategy Server",
                "detail_str": f"Tier {t_val}: 100% precision tyre/race data",
                "insp_title": "TRACK TELEMETRY & STRATEGY SERVER:",
                "insp_line1": "Live Race Data: High-precision real-time tire degradation & temps",
                "insp_line2": "Pit Wall Strategy: Real-time Monte Carlo undercut strategy models",
                "insp_line3": f"Tier {t_val} Sensors: Powers trackside data integration across the paddock",
            }
        elif node_id == "track_fast_repair":
            return {
                "type": "TRACKSIDE",
                "tag": "RAPID REPAIRS",
                "tag_color": (255, 180, 50),
                "benefit_str": f"Tier {t_val}: -{0.6 * t_val:.1f}s Wing / -{2.0 * t_val:.1f}s Repair",
                "detail_str": f"Tier {t_val}: Sub-2.5s wing swaps & UV curing",
                "insp_title": "RAPID REPAIR GANTRY:",
                "insp_line1": f"Front Wing Swaps: Cuts pit replacement duration from 4.0s to {max(2.0, 4.0 - 0.6 * t_val):.1f}s",
                "insp_line2": f"Emergency Repairs: Cuts on-the-fly box time from 14.0s to {max(7.0, 14.0 - 2.0 * t_val):.1f}s",
                "insp_line3": f"Repaired Durability: Restores damaged parts up to {min(80.0, 55.0 + 7.0 * t_val):.0f}% durability",
            }
        elif node_id == "track_jack_release":
            return {
                "type": "TRACKSIDE",
                "tag": "ACTIVE JACK",
                "tag_color": (0, 240, 140),
                "benefit_str": f"Tier {t_val}: Sub-2.0s World-Class Stops",
                "detail_str": f"Tier {t_val}: Pneumatic lift & green-light release",
                "insp_title": "ACTIVE JACK & RELEASE SYSTEM:",
                "insp_line1": f"Pneumatic Lifting: Reduces base pit stop duration by -{0.15 * t_val:.2f}s",
                "insp_line2": "Optical Traffic Gantry: Automated zero-lag release scanner eliminating mistakes",
                "insp_line3": f"Tier {t_val} Rig: Eliminates pit release cross-threads and unsafe releases",
            }
        elif node_id == "track_rival_intel":
            return {
                "type": "TRACKSIDE",
                "tag": "PADDOCK RECON",
                "tag_color": (200, 100, 255),
                "benefit_str": f"Tier {t_val}: +{40 * t_val}% Copycat Proposals",
                "detail_str": f"Tier {t_val}: Trackside rival intelligence",
                "insp_title": "PADDOCK RECON UNIT:",
                "insp_line1": f"Competitor Intelligence: +{40 * t_val}% chance to roll competitor design pitches",
                "insp_line2": "Acoustic & Paddock Scouts: Intercepts rival tire degradation and engine modes",
                "insp_line3": f"Tier {t_val} Intel: Boosts competitor pitch success rate by +{6.0 * t_val:.1f}%",
            }
        elif node_id == "track_reverse_eng":
            return {
                "type": "TRACKSIDE",
                "tag": "REVERSE ENG",
                "tag_color": (200, 100, 255),
                "benefit_str": f"Tier {t_val}: +{25 * t_val}% Rival Knowledge Gain",
                "detail_str": f"Tier {t_val}: Pit-straight dynamic LIDAR profiler",
                "insp_title": "OPTICAL TELEMETRY INTERCEPT:",
                "insp_line1": f"Reverse Engineering: Increases knowledge gain from copycat ideas by +{25 * t_val}%",
                "insp_line2": "Dynamic LIDAR: Profiles competitor underfloor suction and ride height transients",
                "insp_line3": "Automated CAD AI: Reduces innovation lockout duration on competitor breakthroughs",
            }
        elif node_id == "track_weather_station":
            return {
                "type": "TRACKSIDE",
                "tag": "DOPPLER RADAR",
                "tag_color": (50, 200, 255),
                "benefit_str": f"Tier {t_val}: +{2 * t_val} Laps Radar Horizon",
                "detail_str": f"Tier {t_val}: Dual-polarization weather mast",
                "insp_title": "DOPPLER METEOROLOGICAL RADAR:",
                "insp_line1": f"Extended Lookahead: Extends rain radar forecast from 6 to {6 + 2 * t_val} laps ahead",
                "insp_line2": "Micro-Barometric Array: Predicts incoming rain arrival lap with sub-lap precision",
                "insp_line3": "Supercomputer Tracking: Eliminates forecast fog-of-war on track wetness accumulation",
            }
        elif node_id == "track_setup_telemetry":
            return {
                "type": "TRACKSIDE",
                "tag": "SETUP GUIDANCE",
                "tag_color": (255, 215, 0),
                "benefit_str": f"Tier {t_val}: Target Range Overlays in FP",
                "detail_str": f"Tier {t_val}: Dynamic damper & wing sensors",
                "insp_title": "TRACKSIDE SETUP ANALYTICS:",
                "insp_line1": "Practice Guidance: Displays optimal setup target range brackets on FP sliders",
                "insp_line2": f"Bracket Precision: Narrows uncertainty range down to ±{max(3, 18 - t_val * 4.5):.1f} points",
                "insp_line3": "Laser Ride Sensors: Reveals exact aerodynamic and mechanical sweet spots",
            }
        elif node_id == "track_virtual_sim":
            return {
                "type": "TRACKSIDE",
                "tag": "VIRTUAL FP",
                "tag_color": (255, 215, 0),
                "benefit_str": f"Tier {t_val}: FP1 Starts Near Sweet Spot",
                "detail_str": f"Tier {t_val}: 10,000 pre-weekend synthetic laps",
                "insp_title": "PRE-WEEKEND VIRTUAL RIG:",
                "insp_line1": f"Setup Baseline: FP1 car setup starts within ±{max(3, 18 - t_val * 4.5):.1f} of optimal sweet spot",
                "insp_line2": f"Confidence Boost: Car setup confidence begins at {25.0 + t_val * 10.0:.0f}% instead of 25%",
                "insp_line3": "Hardware-in-Loop: Saves practice run laps so drivers can focus on race programs",
            }
        elif node_id == "track_comm_uplink":
            return {
                "type": "TRACKSIDE",
                "tag": "FACTORY UPLINK",
                "tag_color": (0, 240, 140),
                "benefit_str": f"Tier {t_val}: +{15 * t_val}% All-Part Knowledge",
                "detail_str": f"Tier {t_val}: 10,000Hz satellite telemetry uplink",
                "insp_title": "REAL-TIME FACTORY MISSION CONTROL:",
                "insp_line1": f"Knowledge Multiplier: +{15 * t_val}% post-race telemetry knowledge on ALL components",
                "insp_line2": f"Reliability Boost: +{0.12 * t_val:.2f}% post-race reliability progress across all parts",
                "insp_line3": "Mission Control Bridge: Real-time trackside data feeds factory design office",
            }
        elif node_id == "driver_sim":
            return {
                "type": "DRIVER_PERF",
                "tag": "DRIVER TRAINING",
                "tag_color": (255, 100, 60),
                "benefit_str": f"Driver Sim: +{15 * t_val}% Prep & +{6 * t_val}% Young Driver",
                "detail_str": f"Tier {t_val}: Circuit prep & junior sim access",
                "insp_title": "DRIVER SIMULATOR TRAINING:",
                "insp_line1": f"Track Familiarity: +{15 * t_val}% setup preparation & confidence",
                "insp_line2": f"Young Driver Boost: +{6 * t_val}% feeder driver progression via off-peak sim time",
                "insp_line3": f"ON TIER {t_val + 1} UPGRADE: Preparation bonus increases to +{15 * (t_val + 1)}%"
                if t_val < 3
                else "[ MAXIMUM TIER 3 REACHED ]",
            }
        elif node_id == "driver_motion_sim":
            return {
                "type": "DRIVER_PERF",
                "tag": "DRIVER XP",
                "tag_color": (255, 100, 60),
                "benefit_str": f"Hexapod: +{25 * t_val}% XP & +{8 * t_val}% Young Driver",
                "detail_str": f"Tier {t_val}: 6-axis dynamic motion sim",
                "insp_title": "HEXAPOD DRIVER-IN-THE-LOOP SIM:",
                "insp_line1": f"Senior XP Multiplier: +{25 * t_val}% faster driver stat progression",
                "insp_line2": f"Young Driver Boost: +{8 * t_val}% feeder driver progression via shared pro telemetry",
                "insp_line3": f"ON TIER {t_val + 1} UPGRADE: Driver XP bonus increases to +{25 * (t_val + 1)}%"
                if t_val < 3
                else "[ MAXIMUM TIER 3 REACHED ]",
            }
        elif node_id == "driver_vr_cognitive":
            return {
                "type": "DRIVER_PERF",
                "tag": "REFLEX & VISION",
                "tag_color": (255, 120, 70),
                "benefit_str": f"Reflex Lab: +{30 * t_val}% Reflex & +{8 * t_val}% Young Driver",
                "detail_str": f"Tier {t_val}: Batak matrix & saccade tracking",
                "insp_title": "NEURO-REFLEX & COGNITIVE LAB:",
                "insp_line1": f"Reflex Progression: +{30 * t_val}% weekly growth on Race Starts, Defending & Consistency",
                "insp_line2": f"Young Driver Boost: +{8 * t_val}% reaction growth for academy feeder drivers",
                "insp_line3": f"ON TIER {t_val + 1} UPGRADE: Reaction growth increases to +{30 * (t_val + 1)}%"
                if t_val < 3
                else "[ MAXIMUM TIER 3 REACHED ]",
            }
        elif node_id == "driver_gym_conditioning":
            return {
                "type": "DRIVER_PERF",
                "tag": "PHYSICAL GYM",
                "tag_color": (255, 110, 50),
                "benefit_str": f"Biometric Gym: +{25 * t_val}% Endurance & +{6 * t_val}% Young Driver",
                "detail_str": f"Tier {t_val}: 5G neck dyno & sauna chamber",
                "insp_title": "BIOMETRIC ATHLETIC GYM & HEAT CHAMBER:",
                "insp_line1": f"Endurance Progression: +{25 * t_val}% weekly growth on Tire Management & Wet Weather",
                "insp_line2": f"Young Driver Boost: +{6 * t_val}% physical stamina growth for junior drivers",
                "insp_line3": f"ON TIER {t_val + 1} UPGRADE: Endurance growth increases to +{25 * (t_val + 1)}%"
                if t_val < 3
                else "[ MAXIMUM TIER 3 REACHED ]",
            }
        elif node_id == "driver_physio_recovery":
            return {
                "type": "DRIVER_PERF",
                "tag": "LONGEVITY",
                "tag_color": (255, 90, 80),
                "benefit_str": f"Physio Clinic: -{35 * t_val}% Age Decay & +{5 * t_val}% Young Driver",
                "detail_str": f"Tier {t_val}: -130°C cryo & hyperbaric pod",
                "insp_title": "PHYSIO & ATHLETIC LONGEVITY CLINIC:",
                "insp_line1": f"Age Decay Mitigation: Reduces weekly age 30+ physical stat decline by {35 * t_val}%",
                "insp_line2": f"Young Driver Boost: +{5 * t_val}% athletic resilience foundation for juniors",
                "insp_line3": f"ON TIER {t_val + 1} UPGRADE: Age decline protection increases to -{35 * (t_val + 1)}%"
                if t_val < 3
                else "[ MAXIMUM TIER 3 REACHED ]",
            }
        elif node_id == "driver_media_pr_coach":
            return {
                "type": "DRIVER_PERF",
                "tag": "MEDIA & PR",
                "tag_color": (255, 140, 80),
                "benefit_str": f"Media Studio: +{35 * t_val}% Marketability & +{25 * t_val}% Young Driver",
                "detail_str": f"Tier {t_val}: Broadcast scrum & crisis coaching",
                "insp_title": "MEDIA & PRESS CONFERENCE STUDIO:",
                "insp_line1": f"Marketability Growth: +{35 * t_val}% weekly progression on driver Marketability",
                "insp_line2": f"Young Driver Boost: +{25 * t_val}% marketability & interview poise for juniors",
                "insp_line3": f"ON TIER {t_val + 1} UPGRADE: Marketability bonus increases to +{35 * (t_val + 1)}%"
                if t_val < 3
                else "[ MAXIMUM TIER 3 REACHED ]",
            }
        elif node_id == "driver_radio_comms_lab":
            return {
                "type": "DRIVER_PERF",
                "tag": "TACTICAL COMMS",
                "tag_color": (255, 160, 60),
                "benefit_str": f"Radio Lab: +{35 * t_val}% Comms & +{25 * t_val}% Young Driver",
                "detail_str": f"Tier {t_val}: 115dB cockpit simulator & debrief",
                "insp_title": "TACTICAL RADIO & ENGINEERING COMMS LAB:",
                "insp_line1": f"Comms Progression: +{35 * t_val}% growth on Communication & Technical Understanding",
                "insp_line2": f"Young Driver Boost: +{25 * t_val}% radio shorthand and engineer protocol training",
                "insp_line3": f"ON TIER {t_val + 1} UPGRADE: Feedback and growth bonuses increase"
                if t_val < 3
                else "[ MAXIMUM TIER 3 REACHED ]",
            }
        elif node_id == "driver_commercial_suite":
            return {
                "type": "DRIVER_PERF",
                "tag": "SPONSOR VIP",
                "tag_color": (255, 175, 40),
                "benefit_str": f"Sponsor Suite: +{5 * t_val} Appeal & +{15 * t_val}% Young Driver",
                "detail_str": f"Tier {t_val}: Holographic keynote & VIP dining",
                "insp_title": "BRAND AMBASSADOR & SPONSOR SUITE:",
                "insp_line1": f"Sponsor Appeal: +{5 * t_val} flat points added to global team Sponsor Appeal",
                "insp_line2": f"Young Driver Boost: +{15 * t_val}% partner presentation & marketability growth",
                "insp_line3": "Backer Patience: Pay-driver sponsors show +15% more patience during contract talks",
            }
        elif node_id == "driver_academy":
            return {
                "type": "DRIVER_PERF",
                "tag": "SCOUTING",
                "tag_color": (255, 100, 60),
                "benefit_str": "Junior Driver Scouting & Feeder",
                "detail_str": f"Tier {t_val}: Scout talent in feeder series",
                "insp_title": "JUNIOR DRIVER ACADEMY:",
                "insp_line1": "Talent Scouting: Scouts high-potential junior drivers in Tier 4 & 5",
                "insp_line2": "Scholarship Contracts: Secure future star drivers at low rookie salaries",
                "insp_line3": f"Tier {t_val} Academy: Increases discovery chance of prodigy talent",
            }
        elif node_id == "driver_karting_scholarship":
            return {
                "type": "DRIVER_PERF",
                "tag": "KARTING FOUNDATION",
                "tag_color": (255, 130, 90),
                "benefit_str": f"Karting Foundation: +{4 * t_val} Potential Floor",
                "detail_str": f"Tier {t_val}: Grassroots radar across Tier 5 KMA",
                "insp_title": "GRASSROOTS KARTING SCHOLARSHIP:",
                "insp_line1": f"Potential Floor: Raises junior scout candidate minimum potential by +{4 * t_val} points",
                "insp_line2": "Guaranteed Prodigy: Unlocks guaranteed generational talent in scout candidate batches",
                "insp_line3": f"ON TIER {t_val + 1} UPGRADE: Potential floor increases to +{4 * (t_val + 1)}"
                if t_val < 3
                else "[ MAXIMUM TIER 3 REACHED ]",
            }
        elif node_id == "driver_f4_bootcamp":
            return {
                "type": "DRIVER_PERF",
                "tag": "JUNIOR BOOTCAMP",
                "tag_color": (255, 110, 110),
                "benefit_str": f"Junior Bootcamp: +{35 * t_val}% Feeder Driver XP",
                "detail_str": f"Tier {t_val}: Spec F4 fleet & track debrief",
                "insp_title": "SINGLE-SEATER JUNIOR BOOT CAMP:",
                "insp_line1": f"Feeder Development: Academy drivers gain +{35 * t_val}% faster weekly attribute growth",
                "insp_line2": "Instant Promotion: Seamless transition from feeder series to Primary seat without morale penalty",
                "insp_line3": f"ON TIER {t_val + 1} UPGRADE: Feeder XP boost increases to +{35 * (t_val + 1)}%"
                if t_val < 3
                else "[ MAXIMUM TIER 3 REACHED ]",
            }

        # 4. Manufacturing & Testing (Multi-Component & Cross-Cutting Production)
        elif node_id == "eng_windtunnel":
            eff_s = staff_mult if is_unlocked and not is_unstaffed else 0.0
            p_rate = 0.8 * t_val * eff_s
            tot_p = 4.0 * t_val * eff_s
            r_rate = 0.4 * t_val * eff_s
            b_str = (
                f"Rate: +{p_rate:.1f}/part (+{tot_p:.1f} tot) [{staff_mult:.1f}x Staff]"
                if eff_s > 0
                else "Rate: +0.0/part (+0.0 tot) [Unstaffed: 0x]"
            )
            return {
                "type": "AERODYNAMICS",
                "tag": "AERO 5-PARTS",
                "tag_color": (0, 200, 255),
                "benefit_str": b_str,
                "detail_str": f"Tier {t_val}: Wings, Floor, Susp, Brakes (No Engine)"
                if eff_s > 0
                else "Recruit staff in Personnel to activate output",
                "insp_title": "WIND TUNNEL AERODYNAMIC PRODUCTION (5 Parts):",
                "insp_line1": f"Base (Tier {t_val}): +{p_rate:.1f} Perf & +{r_rate:.1f}% Rel per part (+{tot_p:.1f} total across 5 parts)",
                "insp_line2": "IMPACTS: Front Wing, Rear Wing, Floor, Suspension, Brakes (No Engine)",
                "insp_line3": f"ON TIER {t_val + 1} UPGRADE: Production increases to +{0.8 * (t_val + 1):.1f} Perf/part (+{4.0 * (t_val + 1):.1f} tot)"
                if t_val < 3
                else "[ MAXIMUM TIER 3 REACHED ]",
            }
        elif node_id == "eng_cfd":
            eff_s = staff_mult if is_unlocked and not is_unstaffed else 0.0
            p_rate = 1.2 * t_val * eff_s
            tot_p = 3.6 * t_val * eff_s
            b_str = (
                f"Rate: +{p_rate:.1f}/part (+{tot_p:.1f} tot) [{staff_mult:.1f}x Staff]"
                if eff_s > 0
                else "Rate: +0.0/part (+0.0 tot) [Unstaffed: 0x]"
            )
            return {
                "type": "AERODYNAMICS",
                "tag": "AERO 3-PARTS",
                "tag_color": (0, 200, 255),
                "benefit_str": b_str,
                "detail_str": f"Tier {t_val}: Front Wing, Rear Wing, Floor"
                if eff_s > 0
                else "Recruit staff in Personnel to activate output",
                "insp_title": "COMPUTATIONAL FLUID DYNAMICS CLUSTER (3 Parts):",
                "insp_line1": f"Aero Multiplier: +{12 * t_val}% weekly aerodynamic insight (+{p_rate:.1f} Perf/part)",
                "insp_line2": "IMPACTS: Front Wing, Rear Wing, Floor",
                "insp_line3": f"ON TIER {t_val + 1} UPGRADE: Aero multiplier increases to +{12 * (t_val + 1)}%"
                if t_val < 3
                else "[ MAXIMUM TIER 3 REACHED ]",
            }
        elif node_id == "eng_aero_scanning":
            eff_s = staff_mult if is_unlocked and not is_unstaffed else 0.0
            p_rate = 1.0 * t_val * eff_s
            tot_p = 3.0 * t_val * eff_s
            b_str = (
                f"Rate: +{p_rate:.1f}/part (+{tot_p:.1f} tot) [{staff_mult:.1f}x Staff]"
                if eff_s > 0
                else "Rate: +0.0/part (+0.0 tot) [Unstaffed: 0x]"
            )
            return {
                "type": "AERODYNAMICS",
                "tag": "AERO 3-PARTS",
                "tag_color": (0, 200, 255),
                "benefit_str": b_str,
                "detail_str": f"Tier {t_val}: Front Wing, Rear Wing, Floor"
                if eff_s > 0
                else "Recruit staff in Personnel to activate output",
                "insp_title": "AERO PIV SCANNER & FLOW TELEMETRY (3 Parts):",
                "insp_line1": f"Flow Precision: +{10 * t_val}% aero surface correlation (+{p_rate:.1f} Perf/part)",
                "insp_line2": "IMPACTS: Front Wing, Rear Wing, Floor",
                "insp_line3": f"ON TIER {t_val + 1} UPGRADE: Production increases to +{1.0 * (t_val + 1):.1f} Perf/part"
                if t_val < 3
                else "[ MAXIMUM TIER 3 REACHED ]",
            }
        elif node_id == "eng_aero_model_shop":
            eff_s = staff_mult if is_unlocked and not is_unstaffed else 0.0
            p_rate = 0.8 * t_val * eff_s
            tot_p = 2.4 * t_val * eff_s
            b_str = (
                f"Rate: +{p_rate:.1f}/part (+{tot_p:.1f} tot) [{staff_mult:.1f}x Staff]"
                if eff_s > 0
                else "Rate: +0.0/part (+0.0 tot) [Unstaffed: 0x]"
            )
            return {
                "type": "AERODYNAMICS",
                "tag": "AERO 3-PARTS",
                "tag_color": (0, 200, 255),
                "benefit_str": b_str,
                "detail_str": f"Tier {t_val}: Front Wing, Rear Wing, Floor"
                if eff_s > 0
                else "Recruit staff in Personnel to activate output",
                "insp_title": "AERO 60% SCALE MODEL SHOP (3 Parts):",
                "insp_line1": f"Scale Model Speed: +{8 * t_val}% faster scale prototype turnaround",
                "insp_line2": "IMPACTS: Front Wing, Rear Wing, Floor",
                "insp_line3": f"ON TIER {t_val + 1} UPGRADE: Production increases to +{0.8 * (t_val + 1):.1f} Perf/part"
                if t_val < 3
                else "[ MAXIMUM TIER 3 REACHED ]",
            }
        elif node_id == "mfg_cleanroom_autoclave":
            return {
                "type": "MANUFACTURING",
                "tag": "LIGHTWEIGHT",
                "tag_color": (255, 140, 0),
                "benefit_str": f"+{1.5 * t_val:.1f} Perf | -{0.3 * t_val:.1f}% Rel [4 Parts]",
                "detail_str": f"Tier {t_val}: -{2.5 * t_val:.1f}kg Weight (Synergy with QA Lab)",
                "insp_title": "CLEANROOM & PRESSURIZED AUTOCLAVES (Lightweighting Trade-Off):",
                "insp_line1": f"Lightweight Performance: +{1.5 * t_val:.1f} Performance per part (-{2.5 * t_val:.1f}kg chassis weight)",
                "insp_line2": f"Structural Margin: -{0.3 * t_val:.1f}% Reliability per part (Pushes carbon layup to the limit)",
                "insp_line3": "SYNERGY: Pair with QA & NDT Lab or Materials Lab to eliminate reliability risk!",
            }
        elif node_id == "mfg_paint_bay":
            return {
                "type": "MANUFACTURING",
                "tag": "WEIGHT & AERO",
                "tag_color": (255, 140, 0),
                "benefit_str": f"+{0.8 * t_val:.1f} Perf | -{0.2 * t_val:.1f}% Rel [3 Parts]",
                "detail_str": f"Tier {t_val}: -{1.5 * t_val:.1f}kg Livery (Ultra-thin topcoat)",
                "insp_title": "PAINT & LIVERY BAY (Thin Topcoat Trade-Off):",
                "insp_line1": f"Weight Savings: +{0.8 * t_val:.1f} Performance per part (-{1.5 * t_val:.1f}kg lightweight livery)",
                "insp_line2": f"Weather Resistance: -{0.2 * t_val:.1f}% Reliability per part (Ultra-thin micro-coating)",
                "insp_line3": "SYNERGY: Pair with QA & NDT Lab for zero-risk lightweight livery!",
            }
        elif node_id == "eng_comp_materials":
            eff_s = staff_mult if is_unlocked and not is_unstaffed else 0.0
            p_rate = 1.5 * t_val * eff_s
            tot_p = 3.0 * t_val * eff_s
            b_str = (
                f"Rate: +{p_rate:.1f}/part (+{tot_p:.1f} tot) [{staff_mult:.1f}x Staff]"
                if eff_s > 0
                else "Rate: +0.0/part (+0.0 tot) [Unstaffed: 0x]"
            )
            return {
                "type": "CHASSIS",
                "tag": "CHASSIS 2-PARTS",
                "tag_color": (170, 255, 0),
                "benefit_str": b_str,
                "detail_str": f"Tier {t_val}: Suspension & Brakes"
                if eff_s > 0
                else "Recruit staff in Personnel to activate output",
                "insp_title": "COMPOSITE MATERIALS LAB (2 Parts):",
                "insp_line1": f"Carbon Strength: +{15 * t_val}% structural insight (+{p_rate:.1f} Perf & +{0.8 * t_val:.1f}% Rel/part)",
                "insp_line2": "IMPACTS: Suspension, Brakes (Reinforces composite structural margins)",
                "insp_line3": f"ON TIER {t_val + 1} UPGRADE: Production increases to +{1.5 * (t_val + 1):.1f} Perf/part"
                if t_val < 3
                else "[ MAXIMUM TIER 3 REACHED ]",
            }
        elif node_id == "mfg_cnc_machining":
            eff_s = staff_mult if is_unlocked and not is_unstaffed else 0.0
            p_rate = 1.0 * t_val * eff_s
            tot_p = 3.0 * t_val * eff_s
            b_str = (
                f"Rate: +{p_rate:.1f}/part (+{tot_p:.1f} tot) [{staff_mult:.1f}x Staff]"
                if eff_s > 0
                else "Rate: +0.0/part (+0.0 tot) [Unstaffed: 0x]"
            )
            return {
                "type": "MANUFACTURING",
                "tag": "PRECISION 3-PARTS",
                "tag_color": (255, 140, 0),
                "benefit_str": b_str,
                "detail_str": f"Tier {t_val}: Suspension, Brakes, Engine"
                if eff_s > 0
                else "Recruit staff in Personnel to activate output",
                "insp_title": "5-AXIS CNC MACHINING SHOP (3 Parts):",
                "insp_line1": f"Milling Precision: +{10 * t_val}% metallic part accuracy (+{p_rate:.1f} Perf/part)",
                "insp_line2": "IMPACTS: Suspension, Brakes, Engine Tuning",
                "insp_line3": f"ON TIER {t_val + 1} UPGRADE: Production increases to +{1.0 * (t_val + 1):.1f} Perf/part"
                if t_val < 3
                else "[ MAXIMUM TIER 3 REACHED ]",
            }

        elif node_id == "eng_kinematics_lab":
            return {
                "type": "TESTING",
                "tag": "TYRE LIFE",
                "tag_color": (170, 255, 0),
                "benefit_str": f"-{6 * t_val}% Tyre Deg | +1.2 Perf/part",
                "detail_str": f"Tier {t_val}: Suspension & Brakes (2 Parts)",
                "insp_title": "SUSPENSION KINEMATICS RIG (2 Parts):",
                "insp_line1": f"Tire Degradation: Reduces tire wear by -{6 * t_val}% (+{1.2 * t_val:.1f} Perf/part)",
                "insp_line2": "IMPACTS: Suspension, Brakes",
                "insp_line3": f"ON TIER {t_val + 1} UPGRADE: Tire deg reduction increases to -{6 * (t_val + 1)}%"
                if t_val < 3
                else "[ MAXIMUM TIER 3 REACHED ]",
            }
        elif node_id == "test_shaker_rig":
            return {
                "type": "TESTING",
                "tag": "RIDE CONTROL",
                "tag_color": (170, 255, 0),
                "benefit_str": f"+{15 * t_val}% Kerb Grip | Rate: +{1.5 * t_val:.1f} Perf",
                "detail_str": f"Tier {t_val}: Suspension & Mechanical Grip",
                "insp_title": "7-POST HYDRAULIC SHAKER RIG (Suspension):",
                "insp_line1": f"Kerb Compliance: +{15 * t_val}% high-speed bump stability (+{1.5 * t_val:.1f} Perf)",
                "insp_line2": "IMPACTS: Suspension (1 Part Dedicated)",
                "insp_line3": f"ON TIER {t_val + 1} UPGRADE: Kerb compliance increases to +{15 * (t_val + 1)}%"
                if t_val < 3
                else "[ MAXIMUM TIER 3 REACHED ]",
            }
        elif node_id == "mfg_additive_metal":
            p_rate = 0.9 * t_val
            tot_p = 2.7 * t_val
            return {
                "type": "MANUFACTURING",
                "tag": "3D METAL",
                "tag_color": (255, 140, 0),
                "benefit_str": f"Rate: +{p_rate:.1f}/part (+{tot_p:.1f} tot) | 3 Parts",
                "detail_str": f"Tier {t_val}: Suspension, Brakes, ERS",
                "insp_title": "ADDITIVE METAL 3D PRINTING (3 Parts):",
                "insp_line1": f"Titanium Printing: +{9 * t_val}% lightweight metallic parts (+{p_rate:.1f} Perf/part)",
                "insp_line2": "IMPACTS: Suspension, Brakes, ERS",
                "insp_line3": f"ON TIER {t_val + 1} UPGRADE: Production increases to +{0.9 * (t_val + 1):.1f} Perf/part"
                if t_val < 3
                else "[ MAXIMUM TIER 3 REACHED ]",
            }
        elif node_id == "test_torsional_rig":
            return {
                "type": "TESTING",
                "tag": "STIFFNESS",
                "tag_color": (170, 255, 0),
                "benefit_str": f"+{1.2 * t_val:.1f}% Rel | +{0.8 * t_val:.1f} Perf [3 Parts]",
                "detail_str": f"Tier {t_val}: +{15 * t_val}% Tub Rigidity (Survivability)",
                "insp_title": "CHASSIS TORSIONAL RIGIDITY TEST CELL (Stiffness & Reliability):",
                "insp_line1": f"Tub Rigidity: +{15 * t_val}% chassis aero-platform stiffness (+{1.2 * t_val:.1f}% Rel / +{0.8 * t_val:.1f} Perf)",
                "insp_line2": "IMPACTS: Chassis Tub, Suspension, Aero Floor",
                "insp_line3": "SYNERGY: Eliminates aero deflection and reinforces suspension mounting points!",
            }
        elif node_id == "eng_dyno":
            p_rate = 1.8 * t_val
            return {
                "type": "POWERTRAIN",
                "tag": "POWERTRAIN",
                "tag_color": (255, 60, 60),
                "benefit_str": f"+{1.8 * t_val:.1f} Perf | +{1.8 * t_val:.1f}% Rel [2 Parts]",
                "detail_str": f"Tier {t_val}: Stress testing counter-balances tuning",
                "insp_title": "ENGINE DYNAMOMETER CELLS (Reliability Bench):",
                "insp_line1": f"Power Unit R&D: +{18 * t_val}% weekly powertrain insight (+{p_rate:.1f} Perf & +{1.8 * t_val:.1f}% Rel/part)",
                "insp_line2": "IMPACTS: Engine, ERS (Extreme thermal cycle and RPM stress testing)",
                "insp_line3": "SYNERGY: Completely counter-balances the reliability penalty of high-boost Engine Tuning!",
            }
        elif node_id == "eng_thermal_rig":
            p_rate = 1.1 * t_val
            tot_p = 3.3 * t_val
            return {
                "type": "POWERTRAIN",
                "tag": "THERMAL 3-PARTS",
                "tag_color": (255, 60, 60),
                "benefit_str": f"Rate: +{p_rate:.1f}/part (+{tot_p:.1f} tot) | 3 Parts",
                "detail_str": f"Tier {t_val}: Engine, ERS, Brakes",
                "insp_title": "THERMAL CHAMBER & COOLING BENCH (3 Parts):",
                "insp_line1": f"Thermal Management: +{11 * t_val}% thermal insight (+{p_rate:.1f} Perf & +{0.9 * t_val:.1f}% Rel/part)",
                "insp_line2": "IMPACTS: Engine, ERS, Brakes",
                "insp_line3": f"ON TIER {t_val + 1} UPGRADE: Production increases to +{1.1 * (t_val + 1):.1f} Perf/part"
                if t_val < 3
                else "[ MAXIMUM TIER 3 REACHED ]",
            }
        elif node_id == "mfg_electronics":
            p_rate = 1.4 * t_val
            tot_p = 2.8 * t_val
            return {
                "type": "POWERTRAIN",
                "tag": "ELECTRICS",
                "tag_color": (255, 60, 60),
                "benefit_str": f"Rate: +{p_rate:.1f}/part (+{tot_p:.1f} tot) | 2 Parts",
                "detail_str": f"Tier {t_val}: ERS & Engine Electrics",
                "insp_title": "ELECTRONICS & WIRING HARNESS LAB (2 Parts):",
                "insp_line1": f"Electrical Reliability: +{14 * t_val}% insight (+{p_rate:.1f} Perf & +{1.0 * t_val:.1f}% Rel/part)",
                "insp_line2": "IMPACTS: ERS, Engine",
                "insp_line3": f"ON TIER {t_val + 1} UPGRADE: Production increases to +{1.4 * (t_val + 1):.1f} Perf/part"
                if t_val < 3
                else "[ MAXIMUM TIER 3 REACHED ]",
            }
        elif node_id == "mfg_exotic_welding":
            p_rate = 1.3 * t_val
            tot_p = 2.6 * t_val
            return {
                "type": "POWERTRAIN",
                "tag": "WELDING",
                "tag_color": (255, 60, 60),
                "benefit_str": f"Rate: +{p_rate:.1f}/part (+{tot_p:.1f} tot) | 2 Parts",
                "detail_str": f"Tier {t_val}: Engine Exhaust & ERS",
                "insp_title": "EXOTIC ALLOY WELDING FACILITY (2 Parts):",
                "insp_line1": f"Inconel Fabrication: +{13 * t_val}% insight (+{p_rate:.1f} Perf & +{0.8 * t_val:.1f}% Rel/part)",
                "insp_line2": "IMPACTS: Engine, ERS",
                "insp_line3": f"ON TIER {t_val + 1} UPGRADE: Production increases to +{1.3 * (t_val + 1):.1f} Perf/part"
                if t_val < 3
                else "[ MAXIMUM TIER 3 REACHED ]",
            }
        elif node_id == "test_qa_ndt":
            return {
                "type": "TESTING",
                "tag": "QA SCREENING",
                "tag_color": (170, 255, 0),
                "benefit_str": f"+{2.0 * t_val:.1f}% Rel | -{0.4 * t_val:.1f} Perf [7 Parts]",
                "detail_str": f"Tier {t_val}: Blocks flawed designs (Synergy with Autoclave)",
                "insp_title": "QA & NON-DESTRUCTIVE TESTING (Engineering Trade-Off):",
                "insp_line1": f"Reliability Surge: +{2.0 * t_val:.1f}% Reliability per part (Blocks flawed concept failures)",
                "insp_line2": f"Conservative Screening: -{0.4 * t_val:.1f} Performance per part (Rejects bleeding-edge radical designs)",
                "insp_line3": "SYNERGY: Pair with Cleanroom Autoclave or Rapid Proto to eliminate reliability risk!",
            }
        elif node_id == "eng_cad_office":
            return {
                "type": "ENGINEERING",
                "tag": "R&D SUCCESS",
                "tag_color": (0, 200, 255),
                "benefit_str": f"+{5 * t_val}% R&D Success Rate [7 Parts]",
                "detail_str": f"Tier {t_val}: Reduces flawed concept risk",
                "insp_title": "CAD DESIGN OFFICE & FEA MODELING (ALL 7 Parts):",
                "insp_line1": f"R&D Success Multiplier: +{5 * t_val}% increased success chance across all part builds",
                "insp_line2": "IMPACTS: All 7 Car Components (Minimizes packaging flaws)",
                "insp_line3": f"ON TIER {t_val + 1} UPGRADE: Success rate bonus increases to +{5 * (t_val + 1)}%"
                if t_val < 3
                else "[ MAXIMUM TIER 3 REACHED ]",
            }
        elif node_id == "mfg_rapid_proto":
            return {
                "type": "MANUFACTURING",
                "tag": "INNOVATION",
                "tag_color": (255, 140, 0),
                "benefit_str": f"+{8 * t_val}% Innovation Speed [7 Parts]",
                "detail_str": f"Tier {t_val}: Rapid 3D printing of scale parts",
                "insp_title": "RAPID PROTOTYPING & ADDITIVE FABRICATION (ALL 7 Parts):",
                "insp_line1": f"Development Speed: +{8 * t_val}% faster concept turnaround across all parts",
                "insp_line2": "IMPACTS: All 7 Car Components",
                "insp_line3": f"ON TIER {t_val + 1} UPGRADE: Speed bonus increases to +{8 * (t_val + 1)}%"
                if t_val < 3
                else "[ MAXIMUM TIER 3 REACHED ]",
            }
        elif node_id == "eng_works_powertrain":
            return {
                "type": "POWERTRAIN",
                "tag": "WORKS ENGINE",
                "tag_color": (255, 60, 60),
                "benefit_str": "Bespoke Power Unit ($0 Supplier Fee)",
                "detail_str": f"Tier {t_val}: In-house V6 turbo manufacturing",
                "insp_title": "WORKS POWER UNIT FACTORY (Engine & ERS):",
                "insp_line1": "Constructor Status: Unlocks bespoke in-house V6 turbo engine builds",
                "insp_line2": "IMPACTS: Engine, ERS (Eliminates seasonal customer engine supplier fees)",
                "insp_line3": "Full Power Unit Control: Build custom ICE, Turbo, MGU-K, and MGU-H",
            }

        # 5. Core direct single-component R&D facilities (Brakes, Wings, Suspension, Engine Tuning, Floor, ERS)
        comp_labels = {
            "eng_brakes": ("Brakes Only", "BRAKES"),
            "eng_wings_front": ("Front Wing Only", "FRONT WING"),
            "eng_wings_rear": ("Rear Wing Only", "REAR WING"),
            "eng_floor": ("Floor Only", "FLOOR"),
            "eng_suspension": ("Suspension Only", "SUSPENSION"),
            "eng_tuning": ("Engine Only", "ENGINE"),
            "eng_ers": ("ERS Only", "ERS"),
        }
        lbl_info = comp_labels.get(node_id, ("Component", "COMPONENT"))
        part_tag = lbl_info[0]
        part_name = lbl_info[1]

        eq_p_cur = 0.0
        eq_r_cur = 0.0
        active_eq_count = 0
        for eq in eq_items:
            if eq.get("is_active") and (eq.get("current_level") or 0) > 0:
                active_eq_count += 1
                p_lvl = float(eq.get("perf_bonus_per_level") or 0.0)
                r_lvl = float(eq.get("rel_bonus_per_level") or 0.0)
                eq_p_cur += (p_lvl * dev_gain_mult if p_lvl > 0 else p_lvl * negative_penalty_mult) * eq[
                    "current_level"
                ]
                eq_r_cur += (r_lvl * dev_gain_mult if r_lvl > 0 else r_lvl * negative_penalty_mult) * eq[
                    "current_level"
                ]

        # Dedicated single-component facility rate (Concentrated on 1 part)
        if node_id == "eng_tuning":
            # Engine tuning trade-off: high boost performance (+3.8), minor thermal stress (-0.5% rel)
            base_p_unit = 3.8 * dev_gain_mult
            base_r_unit = -0.5 * negative_penalty_mult
        else:
            base_p_unit = 3.0 * dev_gain_mult
            base_r_unit = 1.2 * dev_gain_mult

        eff_s = staff_mult if is_unlocked and not is_unstaffed else 0.0
        cur_base_p = (base_p_unit * (1.0 + (tier - 1) * 0.65) if is_unlocked and tier > 0 else 0.0) * eff_s
        cur_base_r = (base_r_unit * (1.0 + (tier - 1) * 0.65) if is_unlocked and tier > 0 else 0.0) * eff_s
        next_base_p = base_p_unit * (1.0 + tier * 0.65)
        next_base_r = base_r_unit * (1.0 + tier * 0.65)

        tot_p = cur_base_p + eq_p_cur * eff_s
        tot_r = cur_base_r + eq_r_cur * eff_s

        r_sign = "+" if tot_r >= 0 else ""
        eq_sign = "+" if eq_r_cur >= 0 else ""

        if eff_s <= 0.0:
            b_str = "Rate: +0.0 Perf | +0.0% Rel [Unstaffed: 0x]"
            d_str = f"Impacts: {part_tag} (Recruit staff in Personnel to activate)"
        else:
            b_str = f"Rate: +{tot_p:.1f} Perf | {r_sign}{tot_r:.1f}% Rel [{staff_mult:.1f}x Staff]"
            d_str = (
                f"Impacts: {part_tag} (1 Part Dedicated | {staff_mult:.1f}x Multiplier)"
                if node_id != "eng_tuning"
                else f"High-boost tuning ({staff_mult:.1f}x Staff)"
            )

        return {
            "type": "PERF_REL",
            "tag": "1-PART DIRECT",
            "tag_color": (0, 240, 140) if tot_r >= 0 else (255, 180, 40),
            "tot_p": tot_p,
            "tot_r": tot_r,
            "cur_base_p": cur_base_p,
            "cur_base_r": cur_base_r,
            "next_base_p": next_base_p,
            "next_base_r": next_base_r,
            "eq_p_cur": eq_p_cur,
            "eq_r_cur": eq_r_cur,
            "active_eq_count": active_eq_count,
            "benefit_str": b_str,
            "detail_str": d_str,
            "insp_title": f"{part_name} DEDICATED PRODUCTION (1 Part Only):"
            if node_id != "eng_tuning"
            else "ENGINE TUNING & ECU REMAPPING (High-Boost Trade-Off):",
            "insp_line1": f"Base (Tier {t_val}): +{cur_base_p:.1f} Perf, {r_sign}{cur_base_r:.1f}% Rel  |  Equip ({active_eq_count} active): +{eq_p_cur:.2f} Perf, {eq_sign}{eq_r_cur:.2f}% Rel",
            "insp_line2": f"IMPACTS: {part_name} ONLY (Concentrated dedicated development)"
            if node_id != "eng_tuning"
            else "IMPACTS: Engine Only (Pushes powertrain closer to limits)",
            "insp_line3": f"ON TIER {t_val + 1} UPGRADE: Base increases to +{next_base_p:.1f} Perf & {r_sign}{next_base_r:.1f}% Rel"
            if t_val < 3
            else "[ MAXIMUM TIER 3 REACHED ]",
        }

    def _get_node_telemetry_rates(
        self,
        node_id: str,
        tier: Optional[int],
        eq_items: List[Dict[str, Any]],
        dev_gain_mult: float = 1.0,
        negative_penalty_mult: float = 1.0,
        staff_mult: float = 1.0,
    ) -> Dict[str, Any]:
        """Calculates facility base rate, active equipment rate sum, and upgrade delta scaled by staff_mult."""
        t_val = int(tier or 0)
        # Active Equipment Sums
        eq_p_cur = 0.0
        eq_r_cur = 0.0
        active_eq_count = 0
        for eq in eq_items:
            if eq.get("is_active") and (eq.get("current_level") or 0) > 0:
                active_eq_count += 1
                p_lvl = float(eq.get("perf_bonus_per_level") or 0.0)
                r_lvl = float(eq.get("rel_bonus_per_level") or 0.0)
                p_mult = dev_gain_mult if p_lvl > 0 else negative_penalty_mult
                r_mult = dev_gain_mult if r_lvl > 0 else negative_penalty_mult
                eq_p_cur += p_lvl * p_mult * eq["current_level"]
                eq_r_cur += r_lvl * r_mult * eq["current_level"]

        # Base facility rate by tier (Tier 1 = 2.5/1.0, Tier 2 = 4.1/1.65, Tier 3 = 5.8/2.3)
        base_p_unit = 2.5 * dev_gain_mult
        base_r_unit = 1.0 * dev_gain_mult

        if t_val <= 0:
            cur_base_p = 0.0
            cur_base_r = 0.0
            next_base_p = base_p_unit
            next_base_r = base_r_unit
        else:
            cur_base_p = base_p_unit * (1.0 + (tier - 1) * 0.65) * staff_mult
            cur_base_r = base_r_unit * (1.0 + (tier - 1) * 0.65) * staff_mult
            next_base_p = base_p_unit * (1.0 + tier * 0.65)
            next_base_r = base_r_unit * (1.0 + tier * 0.65)

        tot_p = cur_base_p + eq_p_cur * staff_mult
        tot_r = cur_base_r + eq_r_cur * staff_mult
        next_tot_p = next_base_p + eq_p_cur
        next_tot_r = next_base_r + eq_r_cur

        return {
            "cur_base_p": cur_base_p,
            "cur_base_r": cur_base_r,
            "next_base_p": next_base_p,
            "next_base_r": next_base_r,
            "eq_p_cur": eq_p_cur,
            "eq_r_cur": eq_r_cur,
            "active_eq_count": active_eq_count,
            "tot_p": tot_p,
            "tot_r": tot_r,
            "next_tot_p": next_tot_p,
            "next_tot_r": next_tot_r,
            "diff_base_p": next_base_p - cur_base_p,
            "diff_base_r": next_base_r - cur_base_r,
        }

    def handle_click(
        self,
        mx: int,
        my: int,
        gm: GameManager,
        em: EngineeringManager,
        cost_mult: float = 1.0,
        upkeep_mult: float = 1.0,
    ) -> bool:
        # =====================================================================
        # A. Clicks inside Equipment Inspector Drawer (if open)
        # =====================================================================
        if self.inspected_node_id:
            drawer_x = self.width - 550
            drawer_rect = pygame.Rect(drawer_x, 60, 526, self.height - 75)

            if drawer_rect.collidepoint(mx, my):
                # Close button
                close_btn = pygame.Rect(drawer_x + 526 - 70, 68, 60, 22)
                if close_btn.collidepoint(mx, my):
                    self.inspected_node_id = None
                    return True

                # Budget +/- buttons inside drawer (aligned on right of fin_rect)
                status = gm.db.get_department_financial_status(
                    gm.team_id, self.inspected_node_id, upkeep_mult=upkeep_mult
                )
                sub_budget = status["monthly_budget"]
                min_op_cost = status.get("min_operational_cost", 0.0)
                fin_rect = pygame.Rect(drawer_x + 12, 100, 502, 50)
                d_minus = pygame.Rect(fin_rect.x + fin_rect.width - 64, fin_rect.y + 6, 26, 20)
                d_plus = pygame.Rect(fin_rect.x + fin_rect.width - 32, fin_rect.y + 6, 26, 20)

                if d_minus.collidepoint(mx, my):
                    new_b = max(min_op_cost, sub_budget - 5000.0)
                    em.set_subnode_budget(gm.team_id, self.inspected_node_id, new_b, upkeep_mult=upkeep_mult)
                    return True
                elif d_plus.collidepoint(mx, my):
                    new_b = max(min_op_cost, sub_budget + 5000.0)
                    em.set_subnode_budget(gm.team_id, self.inspected_node_id, new_b, upkeep_mult=upkeep_mult)
                    return True

                # Sweep to treasury button inside inspector
                savings_val = status.get("savings_balance", 0.0)
                if savings_val > 0:
                    sweep_btn = pygame.Rect(fin_rect.x + fin_rect.width - 180, fin_rect.y + 33, 172, 17)
                    if sweep_btn.collidepoint(mx, my):
                        success, msg, amt = gm.db.sweep_facility_savings_to_treasury(gm.team_id, self.inspected_node_id)
                        self.status_message = msg
                        return True

                # Facility Upgrade Button inside drawer
                prod_rect = pygame.Rect(drawer_x + 12, 156, 502, 116)
                fac_list = gm.db.get_team_facilities(gm.team_id)
                f_dict = {f["id"]: f for f in fac_list}
                cur_f = f_dict.get(self.inspected_node_id, {})
                cur_t = cur_f.get("current_tier", 1)
                max_t = cur_f.get("max_tier", 3)

                if cur_t < max_t:
                    fac_upg_btn = pygame.Rect(prod_rect.x + prod_rect.width - 134, prod_rect.y + 4, 126, 22)
                    if fac_upg_btn.collidepoint(mx, my):
                        success, msg = em.upgrade_facility_node(gm.team_id, self.inspected_node_id, cost_mult=cost_mult)
                        self.status_message = msg
                        return True

                # Drawer Sub-Tabs: [ EQUIPMENT RIGS ] vs [ ROOM ROSTER & STAFF ]
                tab_eq_rect = pygame.Rect(drawer_x + 12, 276, 246, 24)
                tab_staff_rect = pygame.Rect(drawer_x + 264, 276, 250, 24)
                if tab_eq_rect.collidepoint(mx, my):
                    self.inspector_tab = "EQUIPMENT"
                    self.inspector_scroll_y = 0.0
                    return True
                elif tab_staff_rect.collidepoint(mx, my):
                    self.inspector_tab = "STAFF"
                    self.inspector_scroll_y = 0.0
                    return True

                if self.inspector_tab == "EQUIPMENT":
                    # Equipment list item clicks
                    eq_items = gm.db.get_facility_equipment(gm.team_id, self.inspected_node_id)
                    eq_list_rect = pygame.Rect(drawer_x + 12, 304, 502, self.height - 395)

                    if eq_list_rect.collidepoint(mx, my):
                        item_y_start = eq_list_rect.y + self.inspector_scroll_y
                        card_h = 82
                        for idx, eq in enumerate(eq_items):
                            iy = item_y_start + idx * (card_h + 6)
                            if iy + card_h < eq_list_rect.y or iy > eq_list_rect.y + eq_list_rect.height:
                                continue

                            # Active / Shutdown Toggle Button
                            if not eq["is_tier_locked"] and eq["current_level"] > 0:
                                togg_btn = pygame.Rect(drawer_x + 526 - 170, iy + 52, 70, 22)
                                if togg_btn.collidepoint(mx, my):
                                    new_act = not bool(eq["is_active"])
                                    gm.db.set_equipment_active(gm.team_id, eq["id"], new_act)
                                    self.status_message = f"Set {eq['name']} to {'ACTIVE' if new_act else 'SHUTDOWN'}."
                                    return True

                            # Buy / Upgrade Button
                            if not eq["is_tier_locked"] and eq["current_level"] < eq["max_level"]:
                                upg_btn = pygame.Rect(drawer_x + 526 - 90, iy + 52, 80, 22)
                                if upg_btn.collidepoint(mx, my):
                                    success, msg = gm.db.upgrade_equipment(gm.team_id, eq["id"], cost_mult=cost_mult)
                                    self.status_message = msg
                                    return True
                elif self.inspector_tab == "STAFF":
                    # Personnel Room Roster Action Clicks
                    p_data = gm.staff_manager.get_facility_personnel(gm.team_id, self.inspected_node_id, cur_t)
                    staff_list = p_data["staff"]

                    staff_list_rect = pygame.Rect(drawer_x + 12, 304, 502, self.height - 395)
                    if staff_list_rect.collidepoint(mx, my):
                        curr_y = staff_list_rect.y + self.inspector_scroll_y

                        # Vacant Head Appoint click
                        if not p_data["head"]:
                            app_head_btn = pygame.Rect(
                                staff_list_rect.x + 6 + staff_list_rect.width - 12 - 145, curr_y + 38, 135, 22
                            )
                            if app_head_btn.collidepoint(mx, my):
                                self.requested_hiring_target = (self.inspected_node_id, "HEAD", "Head of Department")
                                return True

                        curr_y += 76 + 18

                        # Staff list clicks
                        for s in staff_list:
                            s_rect = pygame.Rect(staff_list_rect.x + 6, curr_y, staff_list_rect.width - 12, 54)
                            p_btn = pygame.Rect(s_rect.x + s_rect.width - 165, s_rect.y + 24, 80, 20)
                            if p_btn.collidepoint(mx, my):
                                success, msg = gm.staff_manager.promote_to_department_head(
                                    gm.team_id, s["id"], self.inspected_node_id
                                )
                                self.status_message = msg
                                return True

                            r_btn = pygame.Rect(s_rect.x + s_rect.width - 80, s_rect.y + 24, 74, 20)
                            if r_btn.collidepoint(mx, my):
                                new_sal = round(s.get("salary_monthly", 8000.0) * 1.25, 0)
                                success, msg = gm.staff_manager.offer_raise(s["id"], new_sal)
                                self.status_message = msg
                                return True

                            curr_y += 60

                        # Vacant Desk Slots Hire click
                        for v_idx in range(p_data["vacant_staff_slots"]):
                            v_rect = pygame.Rect(staff_list_rect.x + 6, curr_y, staff_list_rect.width - 12, 36)
                            hire_v_btn = pygame.Rect(v_rect.x + v_rect.width - 130, v_rect.y + 6, 120, 24)
                            if hire_v_btn.collidepoint(mx, my):
                                desk_num = len(staff_list) + v_idx + 1
                                self.requested_hiring_target = (self.inspected_node_id, "STAFF", f"Desk #{desk_num}")
                                return True
                            curr_y += 42

                        # Intern Tryout click
                        curr_y += 24
                        if not p_data["intern"]:
                            int_btn = pygame.Rect(
                                staff_list_rect.x + 6 + staff_list_rect.width - 12 - 145, curr_y + 14, 135, 26
                            )
                            if int_btn.collidepoint(mx, my):
                                self.requested_hiring_target = (
                                    self.inspected_node_id,
                                    "INTERN",
                                    "6-Month Intern Tryout",
                                )
                                return True

                return True
            else:
                # Click outside drawer -> close drawer and allow canvas/tab interaction
                self.inspected_node_id = None

        # =====================================================================
        # B. Department Filter Tabs (Top)
        # =====================================================================
        depts = self.get_department_tabs()
        tab_w = max(90, (self.width - 48) // len(depts))
        for idx, (dept_key, _) in enumerate(depts):
            d_rect = pygame.Rect(24 + idx * tab_w, 64, tab_w - 4, 24)
            if d_rect.collidepoint(mx, my):
                self.selected_dept = dept_key
                # Auto-Pan Camera to center on the selected department!
                if dept_key == "ALL":
                    self.pan_x = 40.0
                    self.pan_y = 130.0
                    self.zoom = 1.0
                else:
                    matching_pts = [
                        pos
                        for nid, pos in self.node_positions.items()
                        if nid in self.graph
                        and self._dept_matches(self.graph.nodes[nid].get("department", "GENERAL"), dept_key)
                    ]
                    if matching_pts:
                        min_x = min(p[0] for p in matching_pts)
                        min_y = min(p[1] for p in matching_pts)
                        self.pan_x = 40.0 - min_x * self.zoom
                        self.pan_y = 130.0 - min_y * self.zoom
                return True

        # =====================================================================
        # C. Zoom & Reset View Buttons (HUD Floating Controls)
        # =====================================================================
        canvas_bottom = self.height - 40
        hud_right = (self.width - 550 - 12) if self.inspected_node_id else (self.width - 24 - 12)
        hud_y = canvas_bottom - 28
        hud_rect = pygame.Rect(hud_right - 164, hud_y, 164, 22)

        if hud_rect.collidepoint(mx, my):
            btn_hud_out = pygame.Rect(hud_rect.x + 3, hud_rect.y + 2, 22, 18)
            btn_hud_100 = pygame.Rect(hud_rect.x + 28, hud_rect.y + 2, 42, 18)
            btn_hud_in = pygame.Rect(hud_rect.x + 73, hud_rect.y + 2, 22, 18)
            btn_hud_fit = pygame.Rect(hud_rect.x + 98, hud_rect.y + 2, 63, 18)

            if btn_hud_out.collidepoint(mx, my):
                self.zoom = max(0.65, round(self.zoom - 0.1, 2))
                return True
            if btn_hud_100.collidepoint(mx, my):
                self.zoom = 1.0
                return True
            if btn_hud_in.collidepoint(mx, my):
                self.zoom = min(1.4, round(self.zoom + 0.1, 2))
                return True
            if btn_hud_fit.collidepoint(mx, my):
                self.pan_x = 40.0
                self.pan_y = 130.0
                self.zoom = 1.0
                return True

        btn_reset = pygame.Rect(self.width - 120, 96, 96, 22)
        if btn_reset.collidepoint(mx, my):
            self.pan_x = 40.0
            self.pan_y = 130.0
            self.zoom = 1.0
            return True

        # =====================================================================
        # D. Check Sub-Node Card Clicks (Build, Upgrade, Budget, or Open Inspector)
        # =====================================================================
        facilities = {f["id"]: f for f in gm.db.get_team_facilities(gm.team_id)}

        for node_id, (gx, gy) in self.node_positions.items():
            f = facilities.get(node_id)
            if not f:
                continue

            if not self._dept_matches(f.get("department", "GENERAL"), self.selected_dept):
                continue

            sx = self.pan_x + gx * self.zoom
            sy = self.pan_y + gy * self.zoom
            sw = 250 * self.zoom
            sh = 106 * self.zoom

            is_unlocked = bool(f.get("is_unlocked", False))
            cur_tier = f.get("current_tier") or 0
            max_tier = f.get("max_tier") or 3
            sub_budget = f.get("monthly_sub_budget") or 0.0

            node_rect = pygame.Rect(sx, sy, sw, sh)
            if not node_rect.collidepoint(mx, my):
                continue

            if is_unlocked:
                # Minus & Plus budget buttons
                minus_btn = pygame.Rect(sx + 88 * self.zoom, sy + 80 * self.zoom, 20 * self.zoom, 18 * self.zoom)
                plus_btn = pygame.Rect(sx + 112 * self.zoom, sy + 80 * self.zoom, 20 * self.zoom, 18 * self.zoom)

                if minus_btn.collidepoint(mx, my):
                    st = gm.db.get_department_financial_status(gm.team_id, node_id, upkeep_mult=upkeep_mult)
                    min_op = st.get("min_operational_cost", 0.0)
                    new_budget = max(min_op, sub_budget - 5000.0)
                    em.set_subnode_budget(gm.team_id, node_id, new_budget, upkeep_mult=upkeep_mult)
                    self.status_message = f"Set {f['name']} budget to ${new_budget:,.0f}/mo."
                    return True
                elif plus_btn.collidepoint(mx, my):
                    st = gm.db.get_department_financial_status(gm.team_id, node_id, upkeep_mult=upkeep_mult)
                    min_op = st.get("min_operational_cost", 0.0)
                    new_budget = max(min_op, sub_budget + 5000.0)
                    em.set_subnode_budget(gm.team_id, node_id, new_budget, upkeep_mult=upkeep_mult)
                    self.status_message = f"Set {f['name']} budget to ${new_budget:,.0f}/mo."
                    return True

                # Upgrade Tier button
                if cur_tier < max_tier:
                    upg_btn = pygame.Rect(sx + sw - 76 * self.zoom, sy + 80 * self.zoom, 70 * self.zoom, 20 * self.zoom)
                    if upg_btn.collidepoint(mx, my):
                        success, msg = em.upgrade_facility_node(gm.team_id, node_id, cost_mult=cost_mult)
                        self.status_message = msg
                        return True

                # Clicked node body -> Open Equipment Inspector Drawer!
                self.inspected_node_id = node_id
                self.inspector_scroll_y = 0.0
                return True
            else:
                # Build / Construct Button
                build_btn = pygame.Rect(sx + sw - 92 * self.zoom, sy + 80 * self.zoom, 86 * self.zoom, 20 * self.zoom)
                if build_btn.collidepoint(mx, my):
                    can_b, req_msg = self._can_build_node(node_id, facilities)
                    if can_b:
                        success, msg = em.build_facility_node(gm.team_id, node_id, cost_mult=cost_mult)
                        self.status_message = msg
                        return True
                    else:
                        self.status_message = f"Cannot build {f['name']}: {req_msg} first."
                        return True
                else:
                    # Still open inspector to preview equipment
                    self.inspected_node_id = node_id
                    self.inspector_scroll_y = 0.0
                    return True

        return False

    def handle_scroll(self, event: pygame.event.Event):
        """Handles modern pygame.MOUSEWHEEL events for zooming or drawer scrolling."""
        if self.inspected_node_id:
            # Scroll inside inspector drawer
            delta = event.y * 35.0
            self.inspector_scroll_y = max(-650.0, min(0.0, self.inspector_scroll_y + delta))
        else:
            # Zoom canvas
            if event.y > 0:
                self.zoom = min(1.4, round(self.zoom + 0.05, 2))
            elif event.y < 0:
                self.zoom = max(0.65, round(self.zoom - 0.05, 2))

    def handle_mouse_drag(self, event: pygame.event.Event):
        """Allows dragging to pan around the graph or wheel scrolling inside the inspector."""
        if event.type == pygame.MOUSEBUTTONDOWN:
            if self.inspected_node_id:
                drawer_x = self.width - 550
                drawer_rect = pygame.Rect(drawer_x, 60, 526, self.height - 75)
                if drawer_rect.collidepoint(event.pos):
                    # Scroll inside inspector drawer with buttons 4/5
                    if event.button == 4:
                        self.inspector_scroll_y = min(0.0, self.inspector_scroll_y + 35.0)
                    elif event.button == 5:
                        self.inspector_scroll_y = max(-650.0, self.inspector_scroll_y - 35.0)
                    return
            if event.button == 1 and event.pos[1] > 120:
                self.is_dragging = True
                self.drag_start = event.pos
            elif event.button == 4:
                self.zoom = min(1.4, round(self.zoom + 0.05, 2))
            elif event.button == 5:
                self.zoom = max(0.65, round(self.zoom - 0.05, 2))

        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            self.is_dragging = False

        elif event.type == pygame.MOUSEMOTION and self.is_dragging:
            dx = event.pos[0] - self.drag_start[0]
            dy = event.pos[1] - self.drag_start[1]
            self.pan_x += dx
            self.pan_y += dy
            self.drag_start = event.pos

    def render(
        self,
        surface: pygame.Surface,
        gm: GameManager,
        em: EngineeringManager,
        cost_mult: float = 1.0,
        upkeep_mult: float = 1.0,
        dev_gain_mult: float = 1.0,
        negative_penalty_mult: float = 1.0,
    ):
        # Auto-refresh DAG layout if needed (e.g. initial build or when custom nodes are added/deleted in DB)
        current_node_count = 0
        try:
            with gm.db.get_connection() as conn:
                cur = conn.cursor()
                cur.execute("SELECT COUNT(*) FROM facility_nodes;")
                current_node_count = cur.fetchone()[0]
        except Exception:
            current_node_count = len(self.graph.nodes)

        if not self.node_positions or len(self.graph.nodes) != current_node_count:
            self._build_graph_layout(gm.db)

        # 1. Department Tabs (Top)
        depts = self.get_department_tabs()
        dept_icons = {
            "ALL": "network",
            "AERODYNAMICS": "flag",
            "POWERTRAIN": "wrench",
            "CHASSIS": "shield",
            "MANUFACTURING": "factory",
            "FACILITIES": "network",
            "TELEMETRY": "gauge",
            "COMMERCIAL": "circle-dollar-sign",
            "MARKETING": "circle-dollar-sign",
            "ENGINEERING": "wrench",
            "TESTING": "gauge",
            "HR": "users",
            "TRACKSIDE": "flag",
            "DRIVER_PERF": "zap",
            "MANAGEMENT": "award",
            "GENERAL": "factory",
        }
        tab_w = max(90, (self.width - 48) // len(depts))
        for idx, (dept_key, label) in enumerate(depts):
            d_rect = pygame.Rect(24 + idx * tab_w, 64, tab_w - 4, 24)
            is_sel = dept_key == self.selected_dept
            UITheme.draw_button(
                surface,
                d_rect,
                label,
                self.font_btn,
                is_active=is_sel,
                icon=dept_icons.get(dept_key, "network"),
                icon_size=12,
            )

        facilities = {f["id"]: f for f in gm.db.get_team_facilities(gm.team_id)}

        # Executive Factory Summary Bar (Docked at y=92, height=28)
        unlocked_count = sum(1 for f in facilities.values() if f.get("is_unlocked"))
        total_facilities = max(1, len(facilities))
        total_upkeep = sum(
            (f.get("base_upkeep", 0) * (f.get("current_tier") or 1))
            for f in facilities.values()
            if f.get("is_unlocked")
        )
        total_budgets = sum((f.get("monthly_sub_budget") or 0.0) for f in facilities.values() if f.get("is_unlocked"))

        exec_rect = pygame.Rect(24, 92, self.width - 48, 28)
        pygame.draw.rect(surface, (16, 22, 32), exec_rect, border_radius=3)
        pygame.draw.rect(surface, (35, 48, 65), exec_rect, width=1, border_radius=3)

        # Unlocked Facilities KPI
        pct_unlocked = (unlocked_count / total_facilities) * 100.0
        UITheme.draw_stat_item(
            surface,
            exec_rect.x + 12,
            exec_rect.y + 6,
            "factory",
            f"FACILITIES: {unlocked_count}/{total_facilities} ({pct_unlocked:.0f}%)",
            self.font_badge,
            text_color=(0, 240, 220),
            icon_color=(0, 240, 220),
            icon_size=13,
        )

        # Total Monthly Upkeep
        UITheme.draw_stat_item(
            surface,
            exec_rect.x + 225,
            exec_rect.y + 6,
            "trending-down",
            f"UPKEEP: ${total_upkeep * upkeep_mult:,.0f}/mo",
            self.font_badge,
            text_color=(255, 180, 50),
            icon_color=(255, 180, 50),
            icon_size=13,
        )

        # Sub-Budgets Total
        UITheme.draw_stat_item(
            surface,
            exec_rect.x + 440,
            exec_rect.y + 6,
            "circle-dollar-sign",
            f"SUB-BUDGETS: ${total_budgets:,.0f}/mo",
            self.font_badge,
            text_color=(180, 220, 255),
            icon_color=(0, 200, 255),
            icon_size=13,
        )

        # Help hint on the right
        hint_str = "Hover/click nodes to trace dependencies ►"
        h_surf = self.font_body.render(hint_str, True, (130, 150, 170))
        surface.blit(h_surf, (exec_rect.right - h_surf.get_width() - 12, exec_rect.y + 7))

        # Canvas Clip Area (starting below executive bar)
        canvas_rect = pygame.Rect(24, 124, self.width - 48, self.height - 164)
        pygame.draw.rect(surface, (12, 16, 22), canvas_rect)
        pygame.draw.rect(surface, UITheme.PANEL_BORDER, canvas_rect, width=1)

        # Detect hovered node for interactive edge highlighting
        mx, my = pygame.mouse.get_pos()
        pending_tooltip: Optional[Tuple[str, str, Tuple[int, int], str]] = None
        hovered_node = None
        if canvas_rect.collidepoint(mx, my):
            for node_id, (gx, gy) in self.node_positions.items():
                sx = self.pan_x + gx * self.zoom
                sy = self.pan_y + gy * self.zoom
                sw = 250 * self.zoom
                sh = 106 * self.zoom
                if pygame.Rect(sx, sy, sw, sh).collidepoint(mx, my):
                    hovered_node = node_id
                    break
        focused_node = self.inspected_node_id or hovered_node

        # Set Clip
        prev_clip = surface.get_clip()
        surface.set_clip(canvas_rect)

        # 2. Draw NetworkX Dependency Edges (Connecting Lines with directional arrows and focus tracing)
        for u, v in self.graph.edges():
            u_f = facilities.get(u)
            v_f = facilities.get(v)
            if not u_f or not v_f:
                continue

            if self.selected_dept != "ALL":
                if not self._dept_matches(
                    u_f.get("department", "GENERAL"), self.selected_dept
                ) or not self._dept_matches(v_f.get("department", "GENERAL"), self.selected_dept):
                    continue

            p1 = self.node_positions[u]
            p2 = self.node_positions[v]

            x1 = self.pan_x + (p1[0] + 250) * self.zoom
            y1 = self.pan_y + (p1[1] + 53) * self.zoom
            x2 = self.pan_x + p2[0] * self.zoom
            y2 = self.pan_y + (p2[1] + 53) * self.zoom

            is_parent_edge = focused_node is not None and v == focused_node
            is_child_edge = focused_node is not None and u == focused_node

            if focused_node is not None:
                if is_parent_edge:
                    # Parent prerequisite edge entering focused node
                    line_col = (255, 205, 40) if not u_f.get("is_unlocked") else (0, 240, 140)
                    line_w = max(3, int(4 * self.zoom))
                elif is_child_edge:
                    # Child unlock edge flowing out of focused node
                    line_col = (0, 240, 255)
                    line_w = max(3, int(4 * self.zoom))
                else:
                    # Dim unrelated edges so the dependency path stands out clearly
                    line_col = (28, 36, 48)
                    line_w = max(1, int(1.2 * self.zoom))
            else:
                is_active = bool(u_f.get("is_unlocked", False) and v_f.get("is_unlocked", False))
                if is_active:
                    line_col = (0, 220, 220)
                    line_w = max(2, int(2.5 * self.zoom))
                else:
                    line_col = (110, 130, 155)
                    line_w = max(2, int(1.8 * self.zoom))

            self._draw_bezier_edge(surface, (x1, y1), (x2, y2), line_col, line_w)

        # 3. Draw NetworkX Nodes (Interactive Cards)
        for node_id, (gx, gy) in self.node_positions.items():
            f = facilities.get(node_id)
            if not f:
                continue

            if not self._dept_matches(f.get("department", "GENERAL"), self.selected_dept):
                continue

            sx = self.pan_x + gx * self.zoom
            sy = self.pan_y + gy * self.zoom
            sw = 250 * self.zoom
            sh = 106 * self.zoom

            if (
                sx + sw < canvas_rect.x
                or sx > canvas_rect.x + canvas_rect.width
                or sy + sh < canvas_rect.y
                or sy > canvas_rect.y + canvas_rect.height
            ):
                continue

            card_rect = pygame.Rect(sx, sy, sw, sh)
            is_unlocked = bool(f.get("is_unlocked", False))
            cur_tier = f.get("current_tier") or 0
            max_tier = f.get("max_tier") or 3
            sub_budget = f.get("monthly_sub_budget") or 0.0

            # Background box
            is_inspected = self.inspected_node_id == node_id
            bg_col = (26, 36, 50) if is_inspected else ((20, 28, 38) if is_unlocked else (14, 18, 24))
            border_col = (255, 215, 0) if is_inspected else ((0, 220, 255) if is_unlocked else (50, 60, 75))
            pygame.draw.rect(surface, bg_col, card_rect, border_radius=4)
            pygame.draw.rect(surface, border_col, card_rect, width=2 if is_inspected else 1, border_radius=4)

            # Department indicator color bar on left
            dept_cols = {
                "ENGINEERING": (0, 200, 255),
                "MANUFACTURING": (255, 140, 0),
                "TESTING": (170, 255, 0),
                "POWERTRAIN": (255, 60, 60),
                "COMMERCIAL": (255, 200, 40),
                "MARKETING": (255, 200, 40),
                "HR": (255, 120, 200),
                "TRACKSIDE": (0, 240, 140),
                "DRIVER_PERF": (255, 100, 60),
                "MANAGEMENT": (180, 120, 255),
            }
            bar_col = dept_cols.get(f["department"], (100, 100, 100))
            pygame.draw.rect(
                surface, bar_col, (sx, sy, 5 * self.zoom, sh), border_top_left_radius=4, border_bottom_left_radius=4
            )

            # Compute Facility Benefit Information
            node_eq = gm.db.get_facility_equipment(gm.team_id, node_id, upkeep_mult=upkeep_mult)
            b_info = self._get_facility_benefit_info(
                node_id,
                f.get("department", "GENERAL"),
                f.get("description", ""),
                cur_tier if is_unlocked else 1,
                is_unlocked,
                node_eq,
                gm,
                dev_gain_mult,
                negative_penalty_mult,
            )

            # Row 1: Node Title (left with department icon) & Tier Badge (right)
            dept_name = f.get("department", "GENERAL")
            node_icon = dept_icons.get(dept_name, "factory")
            ic_size = max(10, int(13 * self.zoom))
            UITheme.draw_icon(surface, node_icon, (sx + 8 * self.zoom, sy + 6 * self.zoom), color=bar_col, size=ic_size)
            disp_name = self._truncate_text(self.font_card_title, f["name"], sw - 82 * self.zoom)
            surface.blit(
                self.font_card_title.render(disp_name, True, UITheme.TEXT_WHITE if is_unlocked else (180, 190, 200)),
                (sx + 24 * self.zoom, sy + 6 * self.zoom),
            )

            influenced_parts = self.get_facility_influenced_parts(node_id)

            if is_unlocked:
                # Row 1 Right: Visual Tier Indicator Pips (Gold Diamonds)
                pip_size = max(5, int(7 * self.zoom))
                pip_gap = max(3, int(3.5 * self.zoom))
                total_pips_w = max_tier * pip_size + (max_tier - 1) * pip_gap
                px_start = sx + sw - 8 * self.zoom - total_pips_w
                py_center = sy + 13 * self.zoom

                for t_idx in range(max_tier):
                    px = px_start + t_idx * (pip_size + pip_gap)
                    is_filled = t_idx < cur_tier
                    p_rect = pygame.Rect(int(px), int(py_center - pip_size / 2), pip_size, pip_size)
                    if is_filled:
                        pygame.draw.rect(surface, (255, 215, 0), p_rect, border_radius=1)
                        pygame.draw.rect(surface, (255, 240, 140), p_rect, width=1, border_radius=1)
                    else:
                        pygame.draw.rect(surface, (22, 28, 38), p_rect, border_radius=1)
                        pygame.draw.rect(surface, (60, 75, 95), p_rect, width=1, border_radius=1)

                # Row 2: Unique Facility Benefit Output (Unobstructed full row, truncated to fit card)
                disp_benefit = self._truncate_text(self.font_badge, b_info["benefit_str"], sw - 18 * self.zoom)
                surface.blit(
                    self.font_badge.render(disp_benefit, True, b_info["tag_color"]),
                    (sx + 10 * self.zoom, sy + 23 * self.zoom),
                )

                # Row 3: Car Components Influence Mini-Grid (All 7 Car Parts)
                self._draw_parts_grid(
                    surface,
                    sx + 8 * self.zoom,
                    sy + 39 * self.zoom,
                    sw - 16 * self.zoom,
                    17 * self.zoom,
                    influenced_parts,
                    is_unlocked=True,
                )

                # Row 4: Detail / Breakdown & Upkeep with Icon
                upk_amt_str = f"${f['base_upkeep'] * cur_tier:,.0f}/mo"
                disp_upk = self._truncate_text(self.font_body, f"{b_info['detail_str']} |", sw - 80 * self.zoom)
                surface.blit(
                    self.font_body.render(disp_upk, True, UITheme.TEXT_MUTED),
                    (sx + 10 * self.zoom, sy + 60 * self.zoom),
                )
                upk_x = sx + 10 * self.zoom + self.font_body.size(disp_upk)[0] + 4 * self.zoom
                UITheme.draw_stat_item(
                    surface,
                    int(upk_x),
                    int(sy + 60 * self.zoom),
                    "trending-down",
                    upk_amt_str,
                    self.font_body,
                    text_color=UITheme.TEXT_MUTED,
                    icon_color=(255, 140, 40),
                    icon_size=max(9, int(11 * self.zoom)),
                )

                # Row 5: Budget Controls (left/middle with icon) & Upgrade Button (right)
                bud_str = f"${sub_budget / 1000:.0f}k/mo" if sub_budget >= 1000 else f"${sub_budget:,.0f}/mo"
                UITheme.draw_stat_item(
                    surface,
                    int(sx + 8 * self.zoom),
                    int(sy + 82 * self.zoom),
                    "circle-dollar-sign",
                    bud_str,
                    self.font_badge,
                    text_color=(0, 220, 255),
                    icon_color=(0, 220, 255),
                    icon_size=max(9, int(12 * self.zoom)),
                )

                minus_btn = pygame.Rect(sx + 88 * self.zoom, sy + 80 * self.zoom, 20 * self.zoom, 18 * self.zoom)
                plus_btn = pygame.Rect(sx + 112 * self.zoom, sy + 80 * self.zoom, 20 * self.zoom, 18 * self.zoom)

                pygame.draw.rect(surface, (45, 55, 70), minus_btn, border_radius=2)
                pygame.draw.rect(surface, (45, 55, 70), plus_btn, border_radius=2)

                m_txt = self.font_btn.render("-", True, UITheme.TEXT_WHITE)
                p_txt = self.font_btn.render("+", True, UITheme.TEXT_WHITE)
                surface.blit(m_txt, (minus_btn.x + (minus_btn.width - m_txt.get_width()) // 2, minus_btn.y + 1))
                surface.blit(p_txt, (plus_btn.x + (plus_btn.width - p_txt.get_width()) // 2, plus_btn.y + 1))

                # Upgrade button if not max tier (right side of Row 5)
                if cur_tier < max_tier:
                    next_t = cur_tier + 1
                    upg_cost = f["base_cost"] * (1.5 if next_t == 2 else 2.5) * cost_mult
                    upg_btn = pygame.Rect(sx + sw - 76 * self.zoom, sy + 80 * self.zoom, 70 * self.zoom, 20 * self.zoom)
                    upg_cost_str = f"${upg_cost / 1000000:.1f}M" if upg_cost >= 1000000 else f"${upg_cost / 1000:.0f}k"
                    UITheme.draw_button(
                        surface,
                        upg_btn,
                        f"UPG {upg_cost_str}",
                        self.font_btn,
                        icon="wrench",
                        icon_size=max(8, int(10 * self.zoom)),
                    )
                else:
                    max_lbl = self.font_badge.render("[MAX]", True, (255, 215, 0))
                    surface.blit(max_lbl, (sx + sw - max_lbl.get_width() - 8 * self.zoom, sy + 82 * self.zoom))

            else:
                # Row 1 (Right): UNBUILT Badge
                surface.blit(
                    self.font_badge.render("[UNBUILT]", True, (160, 170, 180)),
                    (sx + sw - 62 * self.zoom, sy + 6 * self.zoom),
                )

                # Row 2: Unique Facility Benefit Preview (Unobstructed full row, truncated to fit card)
                disp_benefit = self._truncate_text(self.font_badge, b_info["benefit_str"], sw - 18 * self.zoom)
                surface.blit(
                    self.font_badge.render(disp_benefit, True, b_info["tag_color"]),
                    (sx + 10 * self.zoom, sy + 23 * self.zoom),
                )

                # Row 3: Car Components Influence Mini-Grid (Preview of what it will influence once built)
                self._draw_parts_grid(
                    surface,
                    sx + 8 * self.zoom,
                    sy + 39 * self.zoom,
                    sw - 16 * self.zoom,
                    17 * self.zoom,
                    influenced_parts,
                    is_unlocked=False,
                )

                # Row 4: Detail / Base Upkeep with Icon
                upk_amt_str = f"${f['base_upkeep']:,.0f}/mo"
                disp_cost = self._truncate_text(self.font_body, f"{b_info['detail_str']} |", sw - 80 * self.zoom)
                surface.blit(
                    self.font_body.render(disp_cost, True, (140, 150, 160)),
                    (sx + 10 * self.zoom, sy + 60 * self.zoom),
                )
                upk_x = sx + 10 * self.zoom + self.font_body.size(disp_cost)[0] + 4 * self.zoom
                UITheme.draw_stat_item(
                    surface,
                    int(upk_x),
                    int(sy + 60 * self.zoom),
                    "trending-down",
                    upk_amt_str,
                    self.font_body,
                    text_color=(140, 150, 160),
                    icon_color=(255, 140, 40),
                    icon_size=max(9, int(11 * self.zoom)),
                )

                # Row 5: Cost with Icon (left) & BUILD Button (right)
                b_cost = f["base_cost"] * cost_mult
                b_cost_str = f"${b_cost / 1000000:.1f}M" if b_cost >= 1000000 else f"${b_cost / 1000:.0f}k"
                UITheme.draw_stat_item(
                    surface,
                    int(sx + 8 * self.zoom),
                    int(sy + 82 * self.zoom),
                    "circle-dollar-sign",
                    b_cost_str,
                    self.font_badge,
                    text_color=(255, 180, 40),
                    icon_color=(255, 180, 40),
                    icon_size=max(9, int(12 * self.zoom)),
                )

                can_b, req_msg = self._can_build_node(node_id, facilities)
                build_btn = pygame.Rect(sx + sw - 92 * self.zoom, sy + 80 * self.zoom, 86 * self.zoom, 20 * self.zoom)

                if can_b:
                    UITheme.draw_button(
                        surface,
                        build_btn,
                        f"BUILD {b_cost_str}",
                        self.font_btn,
                        icon="wrench",
                        icon_size=max(8, int(10 * self.zoom)),
                    )
                else:
                    UITheme.draw_button(
                        surface,
                        build_btn,
                        "LOCKED",
                        self.font_btn,
                        icon="lock",
                        icon_size=max(8, int(10 * self.zoom)),
                        is_disabled=True,
                    )

        # Restore Canvas Clip
        surface.set_clip(prev_clip)

        # Floating Camera HUD in bottom-right of canvas
        hud_right = (self.width - 550 - 12) if self.inspected_node_id else (canvas_rect.right - 12)
        hud_y = canvas_rect.bottom - 28
        hud_rect = pygame.Rect(hud_right - 164, hud_y, 164, 22)
        pygame.draw.rect(surface, (18, 24, 34), hud_rect, border_radius=3)
        pygame.draw.rect(surface, (45, 60, 80), hud_rect, width=1, border_radius=3)

        btn_hud_out = pygame.Rect(hud_rect.x + 3, hud_rect.y + 2, 22, 18)
        btn_hud_100 = pygame.Rect(hud_rect.x + 28, hud_rect.y + 2, 42, 18)
        btn_hud_in = pygame.Rect(hud_rect.x + 73, hud_rect.y + 2, 22, 18)
        btn_hud_fit = pygame.Rect(hud_rect.x + 98, hud_rect.y + 2, 63, 18)

        UITheme.draw_button(surface, btn_hud_out, "-", self.font_badge, bg_color=(28, 36, 48))
        UITheme.draw_button(surface, btn_hud_100, f"{int(self.zoom * 100)}%", self.font_mini, bg_color=(28, 36, 48))
        UITheme.draw_button(surface, btn_hud_in, "+", self.font_badge, bg_color=(28, 36, 48))
        UITheme.draw_button(surface, btn_hud_fit, "RESET", self.font_mini, bg_color=(35, 48, 65))

        # =====================================================================
        # 4. Render Department Equipment Inspector Drawer (Right Side)
        # =====================================================================
        if self.inspected_node_id:
            drawer_x = self.width - 550
            drawer_rect = pygame.Rect(drawer_x, 60, 526, self.height - 75)
            pygame.draw.rect(surface, (14, 18, 26), drawer_rect, border_radius=4)
            pygame.draw.rect(surface, (0, 220, 255), drawer_rect, width=2, border_radius=4)

            # Header
            fac_info = facilities.get(self.inspected_node_id, {})
            hdr_rect = pygame.Rect(drawer_x, 60, 526, 36)
            pygame.draw.rect(surface, (20, 30, 45), hdr_rect, border_top_left_radius=4, border_top_right_radius=4)

            dep_key = fac_info.get("department", "GENERAL")
            dep_ic = dept_icons.get(dep_key, "factory")
            UITheme.draw_icon(surface, dep_ic, (drawer_x + 12, 69), color=(255, 215, 0), size=18)

            title_txt = f"{fac_info.get('name', 'Facility')} (Tier {fac_info.get('current_tier', 1)}/3)"
            surface.blit(self.font_title.render(title_txt, True, (255, 215, 0)), (drawer_x + 36, 70))

            # Close button
            close_btn = pygame.Rect(drawer_x + 526 - 70, 68, 60, 22)
            UITheme.draw_button(
                surface,
                close_btn,
                "CLOSE",
                self.font_btn,
                bg_color=(180, 40, 40),
                icon="x",
                icon_size=10,
            )

            # Financial Health & Budget Status Card
            fin_status = gm.db.get_department_financial_status(
                gm.team_id, self.inspected_node_id, upkeep_mult=upkeep_mult
            )
            fin_rect = pygame.Rect(drawer_x + 12, 98, 502, 54)
            pygame.draw.rect(surface, (20, 26, 36), fin_rect, border_radius=3)
            pygame.draw.rect(surface, (45, 60, 80), fin_rect, width=1, border_radius=3)

            b_str = f"Monthly Budget: ${fin_status['monthly_budget']:,.0f}/mo"
            UITheme.draw_stat_item(
                surface,
                fin_rect.x + 10,
                fin_rect.y + 5,
                "circle-dollar-sign",
                b_str,
                self.font_card_title,
                text_color=(0, 220, 255),
                icon_color=(0, 220, 255),
                icon_size=15,
            )

            # Budget minus/plus buttons inside inspector (cleanly right-aligned)
            d_minus = pygame.Rect(fin_rect.x + fin_rect.width - 64, fin_rect.y + 5, 26, 18)
            d_plus = pygame.Rect(fin_rect.x + fin_rect.width - 32, fin_rect.y + 5, 26, 18)
            pygame.draw.rect(surface, (45, 55, 70), d_minus, border_radius=2)
            pygame.draw.rect(surface, (45, 55, 70), d_plus, border_radius=2)
            surface.blit(self.font_btn.render("-", True, UITheme.TEXT_WHITE), (d_minus.x + 8, d_minus.y + 1))
            surface.blit(self.font_btn.render("+", True, UITheme.TEXT_WHITE), (d_plus.x + 7, d_plus.y + 1))

            cost_str = f"Min Op Demand: ${fin_status['min_operational_cost']:,.0f}/mo"
            cost_w = UITheme.draw_stat_item(
                surface,
                fin_rect.x + 10,
                fin_rect.y + 22,
                "trending-down",
                cost_str,
                self.font_body,
                text_color=UITheme.TEXT_MUTED,
                icon_color=(255, 140, 40),
                icon_size=12,
            )
            fin_info_rect = pygame.Rect(fin_rect.x + 10 + cost_w + 8, fin_rect.y + 20, 16, 16)
            is_fin_hov = fin_info_rect.collidepoint(mx, my) and drawer_rect.collidepoint(mx, my)
            UITheme.draw_info_icon(surface, fin_info_rect, is_hover=is_fin_hov)
            if is_fin_hov:
                fin_lore = (
                    f"Minimum monthly operating cost required for 100% facility efficiency:\n\n"
                    f"• Facility Base Upkeep: ${fin_status['facility_upkeep']:,.0f}/mo\n"
                    f"• Installed Equipment Upkeep: ${fin_status['equipment_upkeep']:,.0f}/mo\n"
                    f"• Department Staff Wages: ${fin_status['staff_salaries']:,.0f}/mo\n\n"
                    f"Operating below minimum demand reduces team development output and reliability."
                )
                pending_tooltip = (
                    "OPERATIONAL EXPENSES BREAKDOWN",
                    fin_lore,
                    (mx + 10, my + 10),
                    "coins",
                )

            # Department Savings Account row & Sweep button
            savings_amt = fin_status.get("savings_balance", 0.0)
            sav_txt = f"Dept Savings: ${savings_amt:,.0f}"
            sav_col = (0, 255, 160) if savings_amt > 0 else (140, 150, 160)
            UITheme.draw_stat_item(
                surface,
                fin_rect.x + 10,
                fin_rect.y + 38,
                "coins",
                sav_txt,
                self.font_badge,
                text_color=sav_col,
                icon_color=sav_col,
                icon_size=12,
            )

            if savings_amt > 0:
                sweep_btn = pygame.Rect(fin_rect.x + fin_rect.width - 180, fin_rect.y + 33, 172, 18)
                UITheme.draw_button(
                    surface,
                    sweep_btn,
                    "SWEEP TO TREASURY",
                    self.font_badge,
                    bg_color=(0, 130, 80),
                    icon="circle-dollar-sign",
                    icon_size=11,
                )

            # Equipment items
            eq_items = gm.db.get_facility_equipment(gm.team_id, self.inspected_node_id, upkeep_mult=upkeep_mult)

            # Department Production & Upgrade Impact Breakdown Card
            prod_rect = pygame.Rect(drawer_x + 12, 156, 502, 116)
            pygame.draw.rect(surface, (18, 26, 38), prod_rect, border_radius=3)
            pygame.draw.rect(surface, (0, 180, 220), prod_rect, width=1, border_radius=3)

            insp_b = self._get_facility_benefit_info(
                self.inspected_node_id,
                fac_info.get("department", "GENERAL"),
                fac_info.get("description", ""),
                int(fac_info.get("current_tier") or 1),
                bool(fac_info.get("is_unlocked")),
                eq_items,
                gm,
                dev_gain_mult,
                negative_penalty_mult,
            )

            # Row 1: Production Card Title (left) & Facility Upgrade Button (right)
            cur_t = fac_info.get("current_tier", 1)
            max_t = fac_info.get("max_tier", 3)
            title_w_limit = prod_rect.width - (145 if cur_t < max_t else 20)
            disp_insp_title = self._truncate_text(self.font_card_title, insp_b["insp_title"], title_w_limit)
            UITheme.draw_stat_item(
                surface,
                prod_rect.x + 10,
                prod_rect.y + 5,
                "award",
                disp_insp_title,
                self.font_card_title,
                text_color=(255, 215, 0),
                icon_color=(255, 215, 0),
                icon_size=14,
            )

            if cur_t < max_t:
                next_t = cur_t + 1
                upg_cost = fac_info.get("base_cost", 0) * (1.5 if next_t == 2 else 2.5) * cost_mult
                upg_cost_str = f"${upg_cost / 1000000:.1f}M" if upg_cost >= 1000000 else f"${upg_cost / 1000:.0f}k"
                fac_upg_btn = pygame.Rect(prod_rect.x + prod_rect.width - 134, prod_rect.y + 4, 126, 20)
                UITheme.draw_button(
                    surface,
                    fac_upg_btn,
                    f"UPGRADE {upg_cost_str}",
                    self.font_btn,
                    icon="wrench",
                    icon_size=11,
                )

            # Row 2: Car Components Influence Matrix (All 7 Car Parts)
            inf_parts = self.get_facility_influenced_parts(self.inspected_node_id)
            p_gap = 4
            p_w = (prod_rect.width - 20 - 6 * p_gap) / 7
            p_h = 28
            for p_idx, (cat, code, icon_name, full_name) in enumerate(self.CAR_PARTS):
                px = prod_rect.x + 10 + p_idx * (p_w + p_gap)
                p_rect = pygame.Rect(int(px), prod_rect.y + 27, int(p_w), p_h)
                is_inf = cat in inf_parts

                if is_inf:
                    p_bg = (14, 44, 56)
                    p_border = (0, 240, 220)
                    p_ic_col = (0, 245, 255)
                    p_txt_col = (255, 255, 255)
                    status_lbl = "ACTIVE"
                    status_col = (0, 255, 160)
                else:
                    p_bg = (15, 19, 26)
                    p_border = (28, 35, 46)
                    p_ic_col = (55, 65, 78)
                    p_txt_col = (65, 75, 88)
                    status_lbl = "NONE"
                    status_col = (70, 80, 95)

                pygame.draw.rect(surface, p_bg, p_rect, border_radius=3)
                pygame.draw.rect(surface, p_border, p_rect, width=1, border_radius=3)

                # Icon + Code on line 1
                p_ic = UIIcons.get_icon(icon_name, size=11, color=p_ic_col)
                p_code_txt = self.font_badge.render(code, True, p_txt_col)
                header_w = p_ic.get_width() + 3 + p_code_txt.get_width()
                h_x = p_rect.x + (p_rect.width - header_w) // 2
                surface.blit(p_ic, (h_x, p_rect.y + 3))
                surface.blit(p_code_txt, (h_x + p_ic.get_width() + 3, p_rect.y + 2))

                # Status on line 2
                st_surf = self.font_mini.render(status_lbl, True, status_col)
                surface.blit(st_surf, (p_rect.x + (p_rect.width - st_surf.get_width()) // 2, p_rect.y + 15))

            # Row 3: Breakdown Line 1
            surface.blit(
                self.font_body.render(insp_b["insp_line1"], True, (200, 220, 240)),
                (prod_rect.x + 10, prod_rect.y + 59),
            )

            # Row 4: Breakdown Line 2 (Highlighted Total Output / Advantage)
            UITheme.draw_stat_item(
                surface,
                prod_rect.x + 10,
                prod_rect.y + 77,
                "zap",
                insp_b["insp_line2"],
                self.font_card_title,
                text_color=(0, 255, 160),
                icon_color=(0, 255, 160),
                icon_size=13,
            )

            # Row 5: Breakdown Line 3 (Upgrade Impact)
            disp_line3 = self._truncate_text(self.font_badge, insp_b["insp_line3"], prod_rect.width - 20)
            surface.blit(self.font_badge.render(disp_line3, True, (255, 180, 40)), (prod_rect.x + 10, prod_rect.y + 96))

            # Sub-Tab Bar (Equipment Rigs vs Room Personnel Roster)
            is_pure_operational = self.inspected_node_id in ("hr_recruitment", "hr_headhunting", "hr_payroll")
            if is_pure_operational:
                self.inspector_tab = "STAFF"
                tab_staff_rect = pygame.Rect(drawer_x + 12, 276, 502, 24)
                UITheme.draw_button(
                    surface,
                    tab_staff_rect,
                    "OPERATIONAL ROSTER & STAFF",
                    self.font_badge,
                    is_active=True,
                    icon="users",
                    icon_size=13,
                )
            else:
                tab_eq_rect = pygame.Rect(drawer_x + 12, 276, 246, 24)
                tab_staff_rect = pygame.Rect(drawer_x + 264, 276, 250, 24)

                eq_active = self.inspector_tab == "EQUIPMENT"
                UITheme.draw_button(
                    surface,
                    tab_eq_rect,
                    f"EQUIPMENT RIGS ({len(eq_items)})",
                    self.font_badge,
                    is_active=eq_active,
                    icon="wrench",
                    icon_size=12,
                )
                UITheme.draw_button(
                    surface,
                    tab_staff_rect,
                    "ROOM ROSTER & STAFF",
                    self.font_badge,
                    is_active=not eq_active,
                    icon="users",
                    icon_size=12,
                )

            # Scrollable Canvas
            eq_canvas = pygame.Rect(drawer_x + 12, 304, 502, self.height - 395)
            pygame.draw.rect(surface, (10, 14, 20), eq_canvas, border_radius=3)
            pygame.draw.rect(surface, (35, 45, 60), eq_canvas, width=1, border_radius=3)

            drawer_prev_clip = surface.get_clip()
            surface.set_clip(eq_canvas)

            if self.inspector_tab == "EQUIPMENT":
                item_y_start = eq_canvas.y + self.inspector_scroll_y
                card_h = 82

                for idx, eq in enumerate(eq_items):
                    iy = item_y_start + idx * (card_h + 6)
                    if iy + card_h < eq_canvas.y or iy > eq_canvas.y + eq_canvas.height:
                        continue

                    item_rect = pygame.Rect(eq_canvas.x + 6, iy, eq_canvas.width - 12, card_h)
                    is_active = bool(eq["is_active"] and eq["current_level"] > 0)
                    is_locked = bool(eq["is_tier_locked"])

                    bg_col = (18, 24, 32) if not is_locked else (12, 14, 18)
                    border_col = (0, 180, 120) if is_active else ((80, 40, 40) if is_locked else (40, 50, 65))
                    pygame.draw.rect(surface, bg_col, item_rect, border_radius=3)
                    pygame.draw.rect(surface, border_col, item_rect, width=1, border_radius=3)

                    # Equipment Title & Level
                    if eq["current_level"] > 0:
                        lvl_str = f"Lv {eq['current_level']}/{eq['max_level']}"
                    else:
                        lvl_str = "UNINSTALLED"
                    name_surf = self.font_card_title.render(
                        eq["name"], True, UITheme.TEXT_WHITE if not is_locked else (120, 130, 140)
                    )
                    surface.blit(name_surf, (item_rect.x + 8, item_rect.y + 6))

                    info_rect = pygame.Rect(item_rect.x + 8 + name_surf.get_width() + 6, item_rect.y + 5, 16, 16)
                    is_info_hov = info_rect.collidepoint(mx, my) and eq_canvas.collidepoint(mx, my)
                    UITheme.draw_info_icon(surface, info_rect, is_hover=is_info_hov)
                    if is_info_hov:
                        pending_tooltip = (
                            f"{eq['name'].upper()} SPECIFICATION",
                            eq["description"],
                            (mx + 10, my + 10),
                            "info",
                        )

                    lvl_badge = self.font_badge.render(
                        f"[{lvl_str}]", True, (255, 215, 0) if is_active else (140, 140, 140)
                    )
                    surface.blit(
                        lvl_badge, (item_rect.x + item_rect.width - lvl_badge.get_width() - 8, item_rect.y + 6)
                    )

                    # Status Indicator Chip (replaces dense text block)
                    if is_active:
                        UITheme.draw_stat_item(
                            surface,
                            item_rect.x + 8,
                            item_rect.y + 24,
                            "check-circle",
                            "ONLINE & CALIBRATED",
                            self.font_badge,
                            text_color=(0, 240, 140),
                            icon_color=(0, 240, 140),
                            icon_size=11,
                        )
                    elif is_locked:
                        req_t = eq.get("unlocked_at_facility_tier", 1)
                        UITheme.draw_stat_item(
                            surface,
                            item_rect.x + 8,
                            item_rect.y + 24,
                            "lock",
                            f"REQUIRES FACILITY TIER {req_t}",
                            self.font_badge,
                            text_color=(240, 100, 100),
                            icon_color=(240, 100, 100),
                            icon_size=11,
                        )
                    else:
                        UITheme.draw_stat_item(
                            surface,
                            item_rect.x + 8,
                            item_rect.y + 24,
                            "wrench",
                            "AVAILABLE FOR INSTALLATION",
                            self.font_badge,
                            text_color=(160, 170, 180),
                            icon_color=(160, 170, 180),
                            icon_size=11,
                        )

                    # Current Impact and Next Upgrade Impact
                    p_lvl = float(eq.get("perf_bonus_per_level") or 0.0)
                    r_lvl = float(eq.get("rel_bonus_per_level") or 0.0)
                    p_mult = dev_gain_mult if p_lvl > 0 else negative_penalty_mult
                    r_mult = dev_gain_mult if r_lvl > 0 else negative_penalty_mult
                    p_unit = p_lvl * p_mult
                    r_unit = r_lvl * r_mult

                    cur_p = p_unit * eq["current_level"]
                    cur_r = r_unit * eq["current_level"]
                    cur_r_sign = "+" if cur_r >= 0 else ""

                    next_lvl = eq["current_level"] + 1
                    next_p = p_unit * next_lvl
                    next_r = r_unit * next_lvl
                    next_r_sign = "+" if next_r >= 0 else ""
                    d_r_sign = "+" if r_unit >= 0 else ""

                    # Current stats row (y + 38)
                    cx = item_rect.x + 8
                    cur_col = (0, 240, 140) if is_active else (140, 140, 140)
                    surface.blit(self.font_body.render("Cur:", True, cur_col), (cx, item_rect.y + 38))
                    cx += self.font_body.size("Cur:")[0] + 5

                    cx += (
                        UITheme.draw_stat_item(
                            surface,
                            cx,
                            item_rect.y + 38,
                            "zap",
                            f"+{cur_p:.2f}",
                            self.font_body,
                            text_color=cur_col,
                            icon_color=(255, 215, 0) if is_active else (140, 140, 140),
                            icon_size=12,
                        )
                        + 6
                    )

                    UITheme.draw_stat_item(
                        surface,
                        cx,
                        item_rect.y + 38,
                        "shield",
                        f"{cur_r_sign}{cur_r:.2f}%",
                        self.font_body,
                        text_color=cur_col,
                        icon_color=(0, 220, 255) if is_active else (140, 140, 140),
                        icon_size=12,
                    )

                    # Next stats row (starting at item_rect.x + 220)
                    nx = item_rect.x + 220
                    if eq["current_level"] < eq["max_level"]:
                        surface.blit(self.font_body.render("Next:", True, (0, 220, 255)), (nx, item_rect.y + 38))
                        nx += self.font_body.size("Next:")[0] + 5

                        p_txt = f"+{next_p:.2f}" + (f" (+{p_unit:.2f})" if eq["current_level"] > 0 else "")
                        nx += (
                            UITheme.draw_stat_item(
                                surface,
                                nx,
                                item_rect.y + 38,
                                "zap",
                                p_txt,
                                self.font_body,
                                text_color=(0, 220, 255),
                                icon_color=(255, 215, 0),
                                icon_size=12,
                            )
                            + 6
                        )

                        r_txt = f"{next_r_sign}{next_r:.2f}%" + (
                            f" ({d_r_sign}{r_unit:.2f}%)" if eq["current_level"] > 0 else ""
                        )
                        UITheme.draw_stat_item(
                            surface,
                            nx,
                            item_rect.y + 38,
                            "shield",
                            r_txt,
                            self.font_body,
                            text_color=(0, 220, 255),
                            icon_color=(0, 220, 255),
                            icon_size=12,
                        )
                    else:
                        UITheme.draw_stat_item(
                            surface,
                            nx,
                            item_rect.y + 38,
                            "sparkles",
                            "MAX LEVEL",
                            self.font_body,
                            text_color=(255, 215, 0),
                            icon_color=(255, 215, 0),
                            icon_size=12,
                        )

                    # Upkeep and Action Buttons
                    next_upk = eq["base_upkeep"] * next_lvl * upkeep_mult
                    if eq["current_level"] > 0:
                        upk_str = f"${eq['current_upkeep']:,.0f}/mo (Next: ${next_upk:,.0f}/mo)"
                    else:
                        upk_str = f"$0/mo (Buy: ${next_upk:,.0f}/mo)"
                    UITheme.draw_stat_item(
                        surface,
                        item_rect.x + 8,
                        item_rect.y + 56,
                        "trending-down",
                        upk_str,
                        self.font_badge,
                        text_color=UITheme.TEXT_MUTED,
                        icon_color=(255, 140, 40),
                        icon_size=11,
                    )

                    # Action Buttons
                    if is_locked:
                        lock_lbl = self.font_badge.render(
                            f"[ LOCKED: Tier {eq['unlocked_at_facility_tier']} ]", True, (255, 80, 80)
                        )
                        surface.blit(
                            lock_lbl, (item_rect.x + item_rect.width - lock_lbl.get_width() - 8, item_rect.y + 52)
                        )
                    else:
                        # Active Toggle Button (only when installed)
                        if eq["current_level"] > 0:
                            togg_btn = pygame.Rect(drawer_x + 526 - 170, item_rect.y + 52, 70, 22)
                            UITheme.draw_button(
                                surface,
                                togg_btn,
                                "ACTIVE" if is_active else "OFF",
                                self.font_btn,
                                bg_color=(0, 140, 80) if is_active else (120, 40, 40),
                                icon="check" if is_active else "x",
                                icon_size=10,
                            )

                        # Manual Install / Upgrade Button
                        if eq["current_level"] < eq["max_level"]:
                            upg_btn = pygame.Rect(drawer_x + 526 - 90, item_rect.y + 52, 80, 22)
                            cost_scaled = eq["next_upgrade_cost"] * cost_mult
                            cost_str = (
                                f"${cost_scaled / 1000000:.1f}M"
                                if cost_scaled >= 1000000
                                else f"${cost_scaled / 1000:.0f}k"
                            )
                            is_buy = eq["current_level"] == 0
                            UITheme.draw_button(
                                surface,
                                upg_btn,
                                f"BUY {cost_str}" if is_buy else f"UPG {cost_str}",
                                self.font_btn,
                                bg_color=(0, 140, 90) if is_buy else (35, 60, 85),
                                text_color=(255, 255, 255) if is_buy else (0, 220, 255),
                                icon="shopping-cart" if is_buy else "wrench",
                                icon_size=11,
                            )
                        else:
                            m_lbl = self.font_badge.render("[ MAX LVL ]", True, (255, 215, 0))
                            surface.blit(
                                m_lbl, (item_rect.x + item_rect.width - m_lbl.get_width() - 8, item_rect.y + 52)
                            )

            elif self.inspector_tab == "STAFF":
                # Render Personnel Room Roster
                cur_tier_val = fac_info.get("current_tier", 1)
                p_data = gm.staff_manager.get_facility_personnel(gm.team_id, self.inspected_node_id, cur_tier_val)
                p_out = gm.staff_manager.calculate_facility_staff_output(
                    gm.team_id, self.inspected_node_id, cur_tier_val, dev_gain_mult
                )
                head = p_data["head"]
                staff_list = p_data["staff"]
                intern = p_data["intern"]
                target_spec = p_data["target_specialty"]

                curr_y = eq_canvas.y + self.inspector_scroll_y + 8

                # 1. Department Head Card
                head_card_rect = pygame.Rect(eq_canvas.x + 6, curr_y, eq_canvas.width - 12, 68)
                pygame.draw.rect(surface, (20, 30, 44), head_card_rect, border_radius=3)
                pygame.draw.rect(
                    surface, (255, 215, 0) if head else (180, 80, 80), head_card_rect, width=1, border_radius=3
                )

                if head:
                    UITheme.draw_icon(
                        surface, "award", (head_card_rect.x + 8, head_card_rect.y + 7), color=(255, 215, 0), size=15
                    )
                    h_name_str = f"HEAD OF DEPARTMENT: {head['name']} (Age {head['age']})"
                    surface.blit(
                        self.font_card_title.render(h_name_str, True, (255, 215, 0)),
                        (head_card_rect.x + 28, head_card_rect.y + 6),
                    )

                    is_h_match = head.get("specialty") == target_spec
                    spec_badge_txt = f"Specialty: {head.get('specialty')} {'[MATCH +50%]' if is_h_match else ''}"
                    surface.blit(
                        self.font_badge.render(spec_badge_txt, True, (0, 240, 140) if is_h_match else (200, 200, 200)),
                        (head_card_rect.x + 8, head_card_rect.y + 24),
                    )

                    hs_x = head_card_rect.x + 8
                    hs_y = head_card_rect.y + 44
                    gap = 12
                    hs_x += (
                        UITheme.draw_stat_item(
                            surface,
                            hs_x,
                            hs_y,
                            "award",
                            f"Leadership: {head.get('stat_leadership', 50):.0f}",
                            self.font_body,
                            text_color=(180, 210, 240),
                            icon_color=(255, 160, 200),
                            icon_size=11,
                            gap=3,
                        )
                        + gap
                    )
                    hs_x += (
                        UITheme.draw_stat_item(
                            surface,
                            hs_x,
                            hs_y,
                            "zap",
                            f"Multiplier: {p_out['head_mult']:.2f}x",
                            self.font_body,
                            text_color=(180, 210, 240),
                            icon_color=(0, 220, 255),
                            icon_size=11,
                            gap=3,
                        )
                        + gap
                    )
                    UITheme.draw_stat_item(
                        surface,
                        hs_x,
                        hs_y,
                        "trending-down",
                        f"${head.get('salary_monthly', 8000):,.0f}/mo",
                        self.font_body,
                        text_color=(180, 210, 240),
                        icon_color=(255, 140, 40),
                        icon_size=11,
                        gap=3,
                    )
                else:
                    UITheme.draw_icon(
                        surface,
                        "triangle-alert",
                        (head_card_rect.x + 8, head_card_rect.y + 8),
                        color=(255, 100, 100),
                        size=15,
                    )
                    surface.blit(
                        self.font_card_title.render("DEPARTMENT HEAD: VACANT", True, (255, 100, 100)),
                        (head_card_rect.x + 28, head_card_rect.y + 8),
                    )
                    surface.blit(
                        self.font_body.render(
                            "Operating in Unsupervised Mode (1.00x Base Output | 0% Leadership Bonus)",
                            True,
                            (180, 180, 180),
                        ),
                        (head_card_rect.x + 8, head_card_rect.y + 28),
                    )

                    app_head_btn = pygame.Rect(
                        head_card_rect.x + head_card_rect.width - 145, head_card_rect.y + 38, 135, 22
                    )
                    UITheme.draw_button(
                        surface,
                        app_head_btn,
                        "APPOINT HEAD",
                        self.font_btn,
                        bg_color=(140, 100, 20),
                        text_color=(255, 215, 0),
                        icon="award",
                        icon_size=11,
                    )

                curr_y += 76

                # 2. Staff Specialists Header
                staff_hdr = f"SPECIALIST STAFF ({len(staff_list)}/{p_data['max_staff_slots']} Desks Filled):"
                UITheme.draw_stat_item(
                    surface,
                    eq_canvas.x + 8,
                    curr_y,
                    "users",
                    staff_hdr,
                    self.font_badge,
                    text_color=(0, 220, 255),
                    icon_color=(0, 220, 255),
                    icon_size=13,
                )
                curr_y += 18

                for s in staff_list:
                    s_rect = pygame.Rect(eq_canvas.x + 6, curr_y, eq_canvas.width - 12, 54)
                    pygame.draw.rect(surface, (16, 22, 30), s_rect, border_radius=3)
                    pygame.draw.rect(surface, (40, 52, 68), s_rect, width=1, border_radius=3)

                    is_s_match = s.get("specialty") == target_spec
                    s_col = (0, 240, 140) if is_s_match else UITheme.TEXT_WHITE
                    UITheme.draw_icon(
                        surface,
                        "user",
                        (s_rect.x + 8, s_rect.y + 7),
                        color=s_col,
                        size=14,
                    )
                    s_title = (
                        f"{s['name']} (Age {s['age']}) | {s.get('specialty')} {'[MATCH +50%]' if is_s_match else ''}"
                    )
                    surface.blit(
                        self.font_card_title.render(s_title, True, s_col),
                        (s_rect.x + 28, s_rect.y + 6),
                    )

                    is_mentoring = intern and intern.get("intern_mentor_id") == s.get("id")
                    mor = s.get("morale", 85)
                    mor_col = (0, 240, 140) if mor >= 80 else ((255, 200, 40) if mor >= 60 else (255, 90, 90))

                    ss_x = s_rect.x + 8
                    ss_y = s_rect.y + 26
                    gap = 10
                    ss_x += (
                        UITheme.draw_stat_item(
                            surface,
                            ss_x,
                            ss_y,
                            "wrench",
                            f"Eng: {s.get('stat_engineering', 35):.0f}",
                            self.font_body,
                            text_color=UITheme.TEXT_MUTED,
                            icon_color=(0, 220, 255),
                            icon_size=11,
                            gap=3,
                        )
                        + gap
                    )
                    ss_x += (
                        UITheme.draw_stat_item(
                            surface,
                            ss_x,
                            ss_y,
                            "sparkles",
                            f"Craft: {s.get('stat_craftsmanship', 35):.0f}",
                            self.font_body,
                            text_color=UITheme.TEXT_MUTED,
                            icon_color=(255, 180, 40),
                            icon_size=11,
                            gap=3,
                        )
                        + gap
                    )
                    ss_x += (
                        UITheme.draw_stat_item(
                            surface,
                            ss_x,
                            ss_y,
                            "heart",
                            f"{mor:.0f}%",
                            self.font_body,
                            text_color=mor_col,
                            icon_color=mor_col,
                            icon_size=11,
                            gap=3,
                        )
                        + gap
                    )
                    if is_mentoring:
                        UITheme.draw_stat_item(
                            surface,
                            ss_x,
                            ss_y,
                            "graduation-cap",
                            "MENTOR (-15%)",
                            self.font_badge,
                            text_color=(255, 160, 40),
                            icon_color=(255, 160, 40),
                            icon_size=11,
                            gap=3,
                        )

                    # Promote to Head Button
                    p_btn = pygame.Rect(s_rect.x + s_rect.width - 165, s_rect.y + 24, 80, 20)
                    UITheme.draw_button(
                        surface,
                        p_btn,
                        "PROMOTE",
                        self.font_btn,
                        bg_color=(30, 55, 80),
                        text_color=(0, 220, 255),
                        icon="award",
                        icon_size=10,
                    )

                    # Offer Raise Button
                    r_btn = pygame.Rect(s_rect.x + s_rect.width - 80, s_rect.y + 24, 74, 20)
                    UITheme.draw_button(
                        surface,
                        r_btn,
                        "+25% RAISE",
                        self.font_btn,
                        bg_color=(35, 65, 45),
                        text_color=(0, 240, 140),
                        icon="trending-up",
                        icon_size=10,
                    )

                    curr_y += 60

                # Empty Desk Slots with Clickable Button
                for v_idx in range(p_data["vacant_staff_slots"]):
                    v_rect = pygame.Rect(eq_canvas.x + 6, curr_y, eq_canvas.width - 12, 36)
                    pygame.draw.rect(surface, (12, 18, 26), v_rect, border_radius=3)
                    pygame.draw.rect(surface, (0, 140, 180), v_rect, width=1, border_radius=3)
                    desk_num = len(staff_list) + v_idx + 1
                    UITheme.draw_icon(surface, "user", (v_rect.x + 10, v_rect.y + 11), color=(0, 180, 220), size=14)
                    surface.blit(
                        self.font_body.render(f"Open Desk #{desk_num} (Available for Specialist)", True, (0, 220, 255)),
                        (v_rect.x + 28, v_rect.y + 10),
                    )

                    hire_v_btn = pygame.Rect(v_rect.x + v_rect.width - 130, v_rect.y + 6, 120, 24)
                    UITheme.draw_button(
                        surface,
                        hire_v_btn,
                        "HIRE TO DESK",
                        self.font_btn,
                        bg_color=(0, 140, 80),
                        icon="user",
                        icon_size=11,
                    )

                    curr_y += 42

                # 3. European 6-Month Intern Desk
                curr_y += 6
                intern_hdr = "EUROPEAN 6-MONTH TALENT TRYOUT (INTERN):"
                UITheme.draw_stat_item(
                    surface,
                    eq_canvas.x + 8,
                    curr_y,
                    "graduation-cap",
                    intern_hdr,
                    self.font_badge,
                    text_color=(255, 180, 40),
                    icon_color=(255, 180, 40),
                    icon_size=13,
                )
                curr_y += 18

                i_rect = pygame.Rect(eq_canvas.x + 6, curr_y, eq_canvas.width - 12, 54)
                pygame.draw.rect(surface, (18, 22, 32), i_rect, border_radius=3)
                pygame.draw.rect(surface, (160, 100, 240) if intern else (40, 50, 65), i_rect, width=1, border_radius=3)

                if intern:
                    is_done = bool(intern.get("is_potential_revealed"))
                    UITheme.draw_icon(
                        surface,
                        "graduation-cap",
                        (i_rect.x + 8, i_rect.y + 7),
                        color=(180, 140, 255),
                        size=15,
                    )
                    i_title = (
                        f"{intern['name']} (Age {intern['age']}) | Month {intern.get('intern_months_completed', 0)}/6"
                    )
                    surface.blit(
                        self.font_card_title.render(i_title, True, (180, 140, 255)), (i_rect.x + 28, i_rect.y + 6)
                    )

                    if is_done:
                        pot_val = intern.get("stat_potential", 70)
                        UITheme.draw_stat_item(
                            surface,
                            i_rect.x + 8,
                            i_rect.y + 26,
                            "zap",
                            f"Tryout Complete! True Potential: {pot_val}/100 (Ready for Full Contract)",
                            self.font_body,
                            text_color=(0, 255, 160),
                            icon_color=(180, 140, 255),
                            icon_size=12,
                            gap=4,
                        )
                    else:
                        m_info = "Shadowing Staff Mentor (Mentor takes -15% guidance penalty)"
                        surface.blit(
                            self.font_body.render(m_info, True, (200, 180, 220)), (i_rect.x + 8, i_rect.y + 26)
                        )
                else:
                    surface.blit(
                        self.font_body.render("No active intern tryout in this room.", True, (130, 140, 150)),
                        (i_rect.x + 10, i_rect.y + 16),
                    )
                    int_btn = pygame.Rect(i_rect.x + i_rect.width - 145, i_rect.y + 14, 135, 26)
                    UITheme.draw_button(
                        surface,
                        int_btn,
                        "ASSIGN INTERN",
                        self.font_btn,
                        bg_color=(120, 60, 180),
                        icon="graduation-cap",
                        icon_size=12,
                    )

            surface.set_clip(drawer_prev_clip)

            # Draw interactive scrollbar track & thumb for equipment drawer
            sb_track = pygame.Rect(drawer_x + 526 - 8, 280, 5, max(40, self.height - 75 - 280))
            pygame.draw.rect(surface, (20, 26, 36), sb_track, border_radius=2)
            scroll_range = 650.0
            visible_h = float(max(40, self.height - 355))
            visible_ratio = max(0.2, min(1.0, visible_h / (visible_h + scroll_range)))
            thumb_h = max(24, int(sb_track.height * visible_ratio))
            scroll_pct = -self.inspector_scroll_y / scroll_range
            thumb_y = sb_track.y + int((sb_track.height - thumb_h) * scroll_pct)
            thumb_rect = pygame.Rect(sb_track.x, thumb_y, sb_track.width, thumb_h)
            pygame.draw.rect(surface, UITheme.ACCENT_CYAN, thumb_rect, border_radius=2)

        # Bottom Status Message Bar
        stat_bar = pygame.Rect(24, self.height - 36, self.width - 48, 26)

        pygame.draw.rect(surface, (18, 24, 30), stat_bar, border_radius=3)
        pygame.draw.rect(surface, UITheme.PANEL_BORDER, stat_bar, width=1, border_radius=3)
        surface.blit(
            self.font_badge.render(f"FACTORY LOG: {self.status_message}", True, UITheme.ACCENT_CYAN),
            (stat_bar.x + 10, stat_bar.y + 6),
        )

        if pending_tooltip:
            t_title, t_text, t_pos, t_icon = pending_tooltip
            UITheme.draw_tooltip(
                surface,
                t_text,
                t_pos,
                title=t_title,
                icon=t_icon,
                font=self.font_badge,
                max_width=360,
            )
