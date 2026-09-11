"""
Specialized Equipment Rigs, Machinery, and Tooling Catalog for Motorsport Facilities.
Each facility contains authentic specialized equipment pieces with level scaling,
tier-locking, dynamic monthly upkeep, and per-race 0.X performance and reliability knowledge bonuses.
"""

from typing import List, Tuple

# Tuple schema: (id, node_id, name, description, base_cost, base_upkeep, perf_bonus_per_level, rel_bonus_per_level, unlocked_at_facility_tier, max_level)
EQUIPMENT_CATALOG: List[Tuple[str, str, str, str, float, float, float, float, int, int]] = [
    # =========================================================================
    # LAYER 0: ROOT
    # =========================================================================
    # Central R&D Workshop (eng_workshop)
    ("eq_ws_wire_edm", "eng_workshop", "Precision Wire EDM Cutter", "Sub-micron electrical discharge contouring", 450000, 12000, 0.2, 0.3, 1, 5),
    ("eq_ws_cmm_scanner", "eng_workshop", "Multi-Axis CMM Coordinate Scanner", "Automated laser metrology tolerance verification", 480000, 14000, 0.2, 0.3, 1, 5),
    ("eq_ws_ultrasonic", "eng_workshop", "Ultrasonic Flaw NDT Station", "Deep non-destructive acoustic subsurface crack detection", 620000, 17000, 0.1, 0.5, 2, 5),
    ("eq_ws_cryo_tumbler", "eng_workshop", "Cryogenic Deburring Tumbler", "Liquid nitrogen flash edge deburring and surface finishing", 360000, 9000, 0.2, 0.2, 2, 5),
    ("eq_ws_laser_metrology", "eng_workshop", "Optical Laser Alignment Gantry", "Full vehicle datum leveling and geometric verification", 580000, 16000, 0.3, 0.3, 3, 5),

    # =========================================================================
    # LAYER 1: FOUNDATIONAL GATEWAYS & CORE DEPARTMENTS
    # =========================================================================
    # 1. Brakes Engineering Lab (eng_brakes)
    ("eq_brk_carbon_friction", "eng_brakes", "Carbon Friction Dyno Bed", "1000°C carbon-carbon braking friction profiler", 780000, 23000, 0.5, 0.3, 1, 5),
    ("eq_brk_hydraulic_caliper", "eng_brakes", "Hydraulic Caliper Flex Bench", "Monobloc caliper deflection and bite measurement", 490000, 14000, 0.4, 0.3, 1, 5),
    ("eq_brk_laser_pyrometer", "eng_brakes", "Laser Disc Pyrometer Array", "Real-time disc surface temperature telemetry", 560000, 16000, 0.4, 0.3, 2, 5),
    ("eq_brk_bbw_simulator", "eng_brakes", "Brake-by-Wire (BBW) Rig", "Electronic rear brake migration & regen response", 890000, 26000, 0.5, 0.4, 2, 5),
    ("eq_brk_bedding_auto", "eng_brakes", "Automated Disc Bedding Rig", "Uniform transfer layer bonding before race events", 380000, 11000, 0.3, 0.4, 3, 5),
    ("eq_brk_thermal_shield", "eng_brakes", "Thermal Radiant Barrier Cell", "Caliper seal and wheel rim heat protection", 450000, 13000, 0.2, 0.5, 3, 5),

    # 2. Front Aero & Wing Facility (eng_wings_front)
    ("eq_fw_cascade_jig", "eng_wings_front", "Front Wing Cascade Flow Jig", "Optimizes outwash flow around front tires", 620000, 18000, 0.6, 0.2, 1, 5),
    ("eq_fw_gurney_calibrator", "eng_wings_front", "Front Gurney Trim Bench", "Micro-adjustments for low-speed front bite", 380000, 11000, 0.4, 0.2, 1, 5),
    ("eq_fw_flex_sensor", "eng_wings_front", "Aero-Elastic Wing Flex Profiler", "Aggressive legal flex tuning under aero load", 750000, 22000, 0.8, -0.1, 2, 5),
    ("eq_fw_vortex_tracker", "eng_wings_front", "Y250 Vortex Particle Tracker", "Underfloor sealing airflow stability verification", 840000, 25000, 0.6, 0.2, 2, 5),
    ("eq_fw_endplate_tunnel", "eng_wings_front", "Front Endplate Deflection Rig", "Tire wake displacement channel optimizer", 510000, 15000, 0.4, 0.3, 3, 5),
    ("eq_fw_carbon_layup", "eng_wings_front", "Front Flap Ultra-Thin Layup Jig", "Maximum lightweighting with minimal structural fatigue", 690000, 20000, 0.5, 0.3, 3, 5),

    # 3. Rear Aero & Wing Facility (eng_wings_rear)
    ("eq_rw_drs_hydraulic", "eng_wings_rear", "DRS High-Speed Hydraulic Bench", "Sub-0.1s DRS flap deployment and flutter resistance", 680000, 20000, 0.6, 0.3, 1, 5),
    ("eq_rw_endplate_slits", "eng_wings_rear", "Endplate Louver Pressure Scanner", "Vortex shedding drag reduction mapper", 490000, 14000, 0.5, 0.2, 1, 5),
    ("eq_rw_beam_wing_jig", "eng_wings_rear", "Beam Wing Synergy Rig", "Diffuser upwash coupling for massive rear downforce", 820000, 24000, 0.7, 0.2, 2, 5),
    ("eq_rw_ultra_drs_actuator", "eng_wings_rear", "Extreme High-Boost DRS Flap Rig", "Ultra-wide DRS opening with slight flutter wear risk", 950000, 28000, 0.8, -0.1, 2, 5),
    ("eq_rw_mainplane_camber", "eng_wings_rear", "Mainplane Variable Camber Rig", "High-downforce vs low-drag aero setup calibrator", 580000, 17000, 0.5, 0.3, 3, 5),
    ("eq_rw_gurney_interchange", "eng_wings_rear", "Modular Carbon Gurney Cell", "Rapid race weekend aero trimming kit", 420000, 12000, 0.4, 0.2, 3, 5),

    # 4. Chassis & Suspension Workshop (eng_suspension)
    ("eq_sus_damper_dyno", "eng_suspension", "Multi-Velocity Damper Dyno", "Low and high-speed compression damping profiler", 620000, 18000, 0.4, 0.4, 1, 5),
    ("eq_sus_arb_torsion", "eng_suspension", "Anti-Roll Bar Torsion Bench", "Torsional stiffness rate and roll resistance", 420000, 12000, 0.3, 0.3, 1, 5),
    ("eq_sus_tire_slip_sim", "eng_suspension", "Tire Force & Slip Angle Bench", "Camber thrust and slip angle lateral grip profiler", 890000, 26000, 0.5, 0.3, 2, 5),
    ("eq_sus_hub_bearing", "eng_suspension", "Wheel Hub Friction & Play Rig", "Ultra-low resistance ceramic bearing test rig", 480000, 14000, 0.3, 0.4, 2, 5),
    ("eq_sus_pushrod_strain", "eng_suspension", "Pushrod Strain Gauge Calibrator", "Wheel load telemetry feedback calibration", 390000, 11000, 0.3, 0.3, 3, 5),
    ("eq_sus_upright_fea", "eng_suspension", "Titanium Upright Stress Rig", "Lightweight structural upright fatigue analyzer", 710000, 20000, 0.4, 0.5, 3, 5),

    # 5. Engine Tuning Facility (eng_tuning)
    ("eq_tun_ecu_programmer", "eng_tuning", "Bespoke ECU Mapping Workstation", "Custom spark advance and injection timing calibration", 580000, 17000, 0.6, 0.2, 1, 5),
    ("eq_tun_wideband_lambda", "eng_tuning", "Wideband Multi-Lambda Analyzer", "Real-time air-fuel ratio optimization across rev range", 420000, 12000, 0.5, 0.3, 1, 5),
    ("eq_tun_aggressive_boost", "eng_tuning", "High-Boost Electronic Wastegate Controller", "Aggressive peak turbo boost with slight thermal wear", 760000, 22000, 0.8, -0.1, 2, 5),
    ("eq_tun_throttle_flybywire", "eng_tuning", "Drive-by-Wire Pedal Linearity Bench", "Instantaneous driver throttle response calibration", 490000, 14000, 0.4, 0.3, 2, 5),
    ("eq_tun_knock_detection", "eng_tuning", "Individual Cylinder Knock Sensor Array", "Protects tuned engines against detonation under full load", 680000, 20000, 0.3, 0.6, 3, 5),
    ("eq_tun_anti_lag_mod", "eng_tuning", "Rotational Anti-Lag Calibration Module", "Keeps turbo spooled off-throttle for zero turbo lag", 820000, 24000, 0.7, 0.1, 3, 5),

    # 6. CAD/CAE Design Office (eng_cad_office)
    ("eq_cad_workstations", "eng_cad_office", "Parametric CAD Design Workstation Pods", "Accelerates chassis structural revisions and modeling", 420000, 12000, 0.4, 0.3, 1, 5),
    ("eq_cad_fea_solver", "eng_cad_office", "Non-Linear FEA Stress Solver", "Finite element structural simulation for weight reduction", 650000, 18000, 0.5, 0.3, 1, 5),
    ("eq_cad_topology_opt", "eng_cad_office", "Generative Topology Optimization Engine", "AI-driven lightweight generative component carving", 880000, 25000, 0.6, 0.2, 2, 5),
    ("eq_cad_aero_surfacing", "eng_cad_office", "Class-A Aero Surface Modeler", "Zero-discontinuity curvature surfacing for airflow attachment", 720000, 21000, 0.5, 0.3, 2, 5),
    ("eq_cad_pdm_vault", "eng_cad_office", "Secure PDM Version-Control Server", "Prevents design version regression and spec errors", 480000, 14000, 0.2, 0.5, 3, 5),

    # 7. Cleanroom & Autoclave Suite (mfg_cleanroom_autoclave)
    ("eq_cln_autoclave_20bar", "mfg_cleanroom_autoclave", "20-Bar Nitrogen Pressurized Autoclave", "Aerospace void-free carbon curing for maximum stiffness", 1100000, 32000, 0.4, 0.6, 1, 5),
    ("eq_cln_hepa_cleanroom", "mfg_cleanroom_autoclave", "Class 1000 Laminar Cleanroom Bay", "Eliminates dust contamination in pre-preg lamination", 680000, 20000, 0.3, 0.5, 1, 5),
    ("eq_cln_debulking_table", "mfg_cleanroom_autoclave", "Heated Vacuum Debulking Table", "Inter-ply air evacuation for ultra-light thin laminates", 520000, 15000, 0.4, 0.4, 2, 5),
    ("eq_cln_laser_projection", "mfg_cleanroom_autoclave", "Laser Ply Placement Projector", "Sub-millimeter carbon ply alignment over complex molds", 790000, 23000, 0.5, 0.4, 2, 5),
    ("eq_cln_pyrometry_cure", "mfg_cleanroom_autoclave", "Multi-Zone Thermal Cure Pyrometer", "Precise resin polymerization without thermal stress", 610000, 18000, 0.3, 0.5, 3, 5),

    # =========================================================================
    # LAYER 2: SPECIALIZED RESEARCH & MACHINING
    # =========================================================================
    # 8. CFD Supercomputing Cluster (eng_cfd)
    ("eq_cfd_gpu_blade", "eng_cfd", "GPU Tensor Supercomputer Rack", "Parallelized Navier-Stokes equation cluster", 1800000, 52000, 0.6, 0.1, 1, 5),
    ("eq_cfd_direct_cooling", "eng_cfd", "Direct-Die Liquid Cooling Loop", "Sustained sub-ambient thermal dissipation", 650000, 19000, 0.3, 0.2, 1, 5),
    ("eq_cfd_mesh_solver", "eng_cfd", "Adaptive Mesh Refinement Suite", "Automated dynamic boundary layer surface solver", 950000, 28000, 0.5, 0.2, 2, 5),
    ("eq_cfd_nvme_raid", "eng_cfd", "Petabyte NVMe Scratch Array", "High-throughput unsteady turbulence transient capture", 720000, 21000, 0.4, 0.1, 2, 5),
    ("eq_cfd_aero_thermal", "eng_cfd", "Coupled Aerothermal Solver", "Brake duct and radiator airflow heat modeling", 1100000, 32000, 0.5, 0.3, 3, 5),

    # 9. Computational Materials Lab (eng_comp_materials)
    ("eq_mat_sem_micro", "eng_comp_materials", "Scanning Electron Microscope", "Nano-scale composite matrix defect analysis", 1450000, 42000, 0.4, 0.5, 1, 5),
    ("eq_mat_rheometer", "eng_comp_materials", "Carbon Resin Rheometer", "Viscosity and curing kinetics characterization", 750000, 22000, 0.3, 0.4, 1, 5),
    ("eq_mat_xray_diff", "eng_comp_materials", "X-Ray Diffraction Spectrometer", "Titanium and Inconel crystal lattice inspection", 1250000, 36000, 0.4, 0.5, 2, 5),
    ("eq_mat_servo_tensile", "eng_comp_materials", "Servo-Hydraulic Tensile Tester", "Dynamic stress-strain breaking limit profiler", 1100000, 32000, 0.3, 0.5, 2, 5),
    ("eq_mat_thermal_dsc", "eng_comp_materials", "Differential Scanning Calorimeter", "Thermal transition and glass temperature analyzer", 820000, 24000, 0.3, 0.4, 3, 5),

    # 10. Thermal & Cooling Flow Test Rig (eng_thermal_rig)
    ("eq_thm_wind_calorimeter", "eng_thermal_rig", "Radiator Airflow Calorimeter Rig", "Core heat rejection efficiency at 300 km/h air speeds", 820000, 24000, 0.5, 0.4, 1, 5),
    ("eq_thm_brake_air_tunnel", "eng_thermal_rig", "Brake Caliper Thermal Wind Tunnel", "Eliminates brake fluid boiling and pad glazing", 710000, 21000, 0.4, 0.5, 1, 5),
    ("eq_thm_oil_cooler_bench", "eng_thermal_rig", "Dry Sump Oil Cooling Matrix Bench", "Optimizes engine oil viscosity under maximum thermal soak", 630000, 18000, 0.4, 0.4, 2, 5),
    ("eq_thm_ir_thermal_cam", "eng_thermal_rig", "High-Speed Infrared Thermal Imaging System", "Detects boundary layer hot-spots on bodywork", 550000, 16000, 0.3, 0.4, 2, 5),
    ("eq_thm_heat_pipe_sim", "eng_thermal_rig", "Phase-Change Heat Pipe Simulator", "Advanced cockpit and electronics thermal isolation", 490000, 14000, 0.2, 0.5, 3, 5),

    # 11. Aero Model Shop (eng_aero_model_shop)
    ("eq_ams_scale_jig", "eng_aero_model_shop", "60% Rapid Assembly Scale Alignment Jig", "Extreme accuracy model alignment for wind tunnel runs", 640000, 19000, 0.5, 0.3, 1, 5),
    ("eq_ams_rapid_sls", "eng_aero_model_shop", "High-Resolution SLS Scale Part Printer", "Produces scaled wings and floor fences in under 4 hours", 780000, 23000, 0.6, 0.2, 1, 5),
    ("eq_ams_micro_loadcell", "eng_aero_model_shop", "Internal Model Multi-Axis Strain Gauge Balance", "Separates wing load from total chassis downforce", 890000, 26000, 0.6, 0.3, 2, 5),
    ("eq_ams_pressure_taps", "eng_aero_model_shop", "256-Channel Micro Pressure Tap Array", "Surfaces scale models with hundreds of micro pressure sensors", 710000, 21000, 0.5, 0.3, 2, 5),
    ("eq_ams_surface_lapping", "eng_aero_model_shop", "Diamond Micro-Lapping Surface Polisher", "Achieves true aerodynamic boundary scale smoothness", 450000, 13000, 0.3, 0.3, 3, 5),

    # 12. Kinematics & Suspension Geometry Lab (eng_kinematics_lab)
    ("eq_kin_kc_rig", "eng_kinematics_lab", "Full-Scale Kinematics & Compliance (K&C) Rig", "Measures wheel deflection, roll center & bump steer", 1400000, 41000, 0.6, 0.4, 1, 5),
    ("eq_kin_anti_geometry", "eng_kinematics_lab", "Anti-Dive & Anti-Squat Geometry Profiler", "Optimizes chassis pitch stability under heavy braking", 850000, 25000, 0.5, 0.3, 1, 5),
    ("eq_kin_laser_camber", "eng_kinematics_lab", "Dynamic Laser Camber-Gain Scanner", "Tracks tire contact angle throughout suspension travel", 720000, 21000, 0.5, 0.3, 2, 5),
    ("eq_kin_scrub_radius", "eng_kinematics_lab", "Steering Axis Scrub Radius Balancer", "Minimizes steering kickback and tire scrub resistance", 590000, 17000, 0.4, 0.3, 2, 5),
    ("eq_kin_virtual_steer", "eng_kinematics_lab", "Ackermann Steering Geometry Calibrator", "Improves low-speed hairpin rotation and turn-in grip", 510000, 15000, 0.3, 0.4, 3, 5),

    # 13. 5-Axis Precision CNC Machine Shop (mfg_cnc_machining)
    ("eq_cnc_5axis_hsc", "mfg_cnc_machining", "High-Speed 5-Axis Milling Center (30,000 RPM)", "Precision alloy machining for uprights and gearbox cases", 980000, 29000, 0.5, 0.4, 1, 5),
    ("eq_cnc_twin_spindle", "mfg_cnc_machining", "Twin-Spindle CNC Turning & Milling Lathe", "Rapid suspension pins, wheel nuts and driveshaft fabrication", 740000, 22000, 0.4, 0.4, 1, 5),
    ("eq_cnc_cryo_milling", "mfg_cnc_machining", "Liquid Nitrogen Cryogenic Milling Head", "Machining titanium without micro-fractures or tool wear", 860000, 25000, 0.6, 0.3, 2, 5),
    ("eq_cnc_pallet_changer", "mfg_cnc_machining", "Automated 8-Pallet Fast-Exchange System", "Enables 24/7 continuous lights-out machining", 620000, 18000, 0.4, 0.3, 2, 5),
    ("eq_cnc_laser_toolsetter", "mfg_cnc_machining", "Non-Contact Laser Tool Metrology Probe", "Detects sub-micron tool deflection before part errors", 510000, 15000, 0.2, 0.5, 3, 5),

    # 14. Pre-Preg Freezers & Automated Pattern Cutters (mfg_prepreg_freezer)
    ("eq_ppf_subzero_vault", "mfg_prepreg_freezer", "-20°C Climate-Monitored Pre-Preg Storage Vault", "Maintains resin tack and prevents un-cured resin degradation", 520000, 15000, 0.2, 0.5, 1, 5),
    ("eq_ppf_ultrasonic_knife", "mfg_prepreg_freezer", "CNC Ultrasonic Oscillating Ply Cutter", "Fray-free slicing of exotic carbon weaves with zero waste", 780000, 23000, 0.5, 0.4, 1, 5),
    ("eq_ppf_nesting_ai", "mfg_prepreg_freezer", "Automated AI Ply Nesting Software", "Optimizes carbon sheet utilization and cuts scrap by 25%", 450000, 13000, 0.4, 0.3, 2, 5),
    ("eq_ppf_rfid_trace", "mfg_prepreg_freezer", "RFID Roll Out-Time Life Tracker", "Prevents expired resin rolls from being used in structural tubs", 380000, 11000, 0.1, 0.6, 2, 5),
    ("eq_ppf_auto_kitting", "mfg_prepreg_freezer", "Automated Vacuum Bagging Kitting Carousel", "Packages complete ply stacks directly for layup technicians", 590000, 17000, 0.3, 0.4, 3, 5),

    # 15. Rapid Tooling & Pattern Shop (mfg_rapid_tooling)
    ("eq_rtp_gantry_router", "mfg_rapid_tooling", "Large-Format 5-Axis Foam & Board Gantry Router", "Carves master aerodynamic plugs in record turnaround", 890000, 26000, 0.5, 0.3, 1, 5),
    ("eq_rtp_invar_tooling", "mfg_rapid_tooling", "Low-CTE Invar Alloy Master Tooling Rig", "Zero thermal expansion tooling for exact aero tolerances", 1150000, 34000, 0.6, 0.4, 1, 5),
    ("eq_rtp_epoxy_infusion", "mfg_rapid_tooling", "High-Temperature Epoxy Tooling Infuser", "Creates durable composite molds for full race season runs", 680000, 20000, 0.4, 0.4, 2, 5),
    ("eq_rtp_surface_sealer", "mfg_rapid_tooling", "Nanotech Mold Surface Sealing Station", "Achieves mirror-finish tool release with zero surface drag", 490000, 14000, 0.3, 0.3, 2, 5),
    ("eq_rtp_3d_sand_cast", "mfg_rapid_tooling", "3D Sand Core Mold Printer", "Rapid casting of complex hollow metal nodes and housings", 760000, 22000, 0.4, 0.3, 3, 5),

    # 16. Powertrain & Engine Dyno Cells (eng_dyno)
    ("eq_dyno_hydro_trans", "eng_dyno", "Transient Hydrostatic Dyno", "Simulates realistic gear shifts and throttle transients", 2400000, 70000, 0.6, 0.5, 1, 5),
    ("eq_dyno_coriolis_meter", "eng_dyno", "Coriolis Fuel Flow Mass Meter", "FIA-standard sub-milligram fuel rate telemetry", 820000, 24000, 0.4, 0.3, 1, 5),
    ("eq_dyno_piezo_sensors", "eng_dyno", "In-Cylinder Piezo Pressure Sensors", "Combustion flame front and knock peak telemetry", 950000, 28000, 0.5, 0.4, 2, 5),
    ("eq_dyno_intercooler_rig", "eng_dyno", "High-Capacity Intercooler Rig", "Maintains calibrated intake manifold charge temperatures", 740000, 22000, 0.4, 0.4, 2, 5),
    ("eq_dyno_octane_cell", "eng_dyno", "Fuel Detonation Resistance Cell", "Bespoke synthetic fuel combustion tuning", 1250000, 36000, 0.6, 0.4, 3, 5),

    # 17. Electronics & Harnessing Lab (mfg_electronics)
    ("eq_ele_mil_spec_crimper", "mfg_electronics", "MIL-SPEC High-Density Loom Assembly Benches", "Precision potting, raychem heat-shrinking and gold pins", 480000, 14000, 0.3, 0.5, 1, 5),
    ("eq_ele_automated_tester", "mfg_electronics", "Automated 500-Point Wire Loom Continuity Rig", "Instantly flags resistance drops and short circuits", 620000, 18000, 0.2, 0.6, 1, 5),
    ("eq_ele_sensor_calibrator", "mfg_electronics", "Multi-Axis Sensor Calibration Centrifuge", "Calibrates wheel speed, steering angle and inertia sensors", 540000, 16000, 0.4, 0.4, 2, 5),
    ("eq_ele_potted_ecu_bay", "mfg_electronics", "Vacuum Resin ECU Potting Enclosure", "Hermetically seals control units against oil, water and heat", 410000, 12000, 0.1, 0.6, 2, 5),
    ("eq_ele_canbus_analyzer", "mfg_electronics", "High-Frequency CAN-FD / Ethernet Bus Protocol Analyzer", "Zero packet loss on 1000Hz live telemetry channels", 590000, 17000, 0.3, 0.5, 3, 5),

    # =========================================================================
    # LAYER 3: ADVANCED RIGS, ADDITIVE MANUFACTURING & NDT
    # =========================================================================
    # 18. Rolling-Road Wind Tunnel (eng_windtunnel)
    ("eq_wt_steel_belt", "eng_windtunnel", "60% Steel Rolling Road Bed", "Synchronized high-speed tire contact belt", 2800000, 85000, 0.7, 0.2, 1, 5),
    ("eq_wt_bl_suction", "eng_windtunnel", "Boundary Layer Suction Plenum", "Prevents ground-plane flow stagnation under diffuser", 1400000, 42000, 0.5, 0.2, 1, 5),
    ("eq_wt_dynamic_yaw", "eng_windtunnel", "Dynamic Yaw & Roll Turntable", "Simulates cornering aero balance and yaw angles", 1750000, 50000, 0.6, 0.3, 2, 5),
    ("eq_wt_patch_sensors", "eng_windtunnel", "Tire Contact Patch Transducers", "Dynamic vertical load and scrubbing friction logging", 980000, 29000, 0.4, 0.2, 2, 5),
    ("eq_wt_gantry_swap", "eng_windtunnel", "Rapid Model Exchange Gantry", "Cuts wind tunnel configuration downtime by 60%", 1150000, 34000, 0.4, 0.3, 3, 5),

    # 19. Aero Surface Scanning & PIV Lab (eng_aero_scanning)
    ("eq_asp_piv_laser", "eng_aero_scanning", "Dual-Pulsed Nd:YAG PIV Laser Sheet System", "Illuminates microscopic particle streamlines in real time", 1650000, 48000, 0.7, 0.2, 1, 5),
    ("eq_asp_highspeed_cam", "eng_aero_scanning", "10,000 FPS Stereo Photogrammetry Cameras", "Captures boundary layer separation and turbulence bursts", 1250000, 36000, 0.6, 0.2, 1, 5),
    ("eq_asp_optical_profiler", "eng_aero_scanning", "Structured Blue-Light 3D Surface Scanner", "Sub-micron comparison of manufactured wings vs CAD intent", 880000, 25000, 0.4, 0.4, 2, 5),
    ("eq_asp_smoke_injection", "eng_aero_scanning", "Multi-Point Helium-Filled Bubble Injector", "Traces low-drag vortex cores over cockpit and rear wing", 640000, 19000, 0.5, 0.2, 2, 5),
    ("eq_asp_pressure_paint", "eng_aero_scanning", "Pressure-Sensitive Paint (PSP) UV System", "Full continuous surface pressure map without sensor taps", 980000, 28000, 0.6, 0.3, 3, 5),

    # 20. 7-Post Hydraulic Shaker Rig (test_shaker_rig)
    ("eq_shk_actuators", "test_shaker_rig", "7-Post Electro-Hydraulic Actuator System", "Simulates track bumps, kerb strikes and aero downforce heave", 1950000, 56000, 0.5, 0.6, 1, 5),
    ("eq_shk_gps_track_replay", "test_shaker_rig", "GPS Track Surface Profile Replay System", "Replicates bumpy tracks like Interlagos and Silverstone", 880000, 25000, 0.4, 0.4, 1, 5),
    ("eq_shk_porpoise_damper", "test_shaker_rig", "Aerodynamic Pitch & Heave Damper Tuning Cell", "Eliminates high-speed aerodynamic ground porpoising", 1200000, 35000, 0.6, 0.5, 2, 5),
    ("eq_shk_contact_loadcells", "test_shaker_rig", "High-Frequency Wheel Pad Load Cells", "Monitors tire contact patch load variations over kerbs", 760000, 22000, 0.4, 0.4, 2, 5),
    ("eq_shk_third_element", "test_shaker_rig", "Third Element Heave Spring Dynamometer", "Fine-tunes front and rear heave springs for stable ride heights", 690000, 20000, 0.5, 0.3, 3, 5),

    # 21. Additive Metal Manufacturing Lab (mfg_additive_metal)
    ("eq_amm_dmls_titanium", "mfg_additive_metal", "Quad-Laser DMLS Titanium 3D Printer", "Direct laser sintering of hollow lightweight titanium uprights", 2200000, 64000, 0.7, 0.4, 1, 5),
    ("eq_amm_inconel_printer", "mfg_additive_metal", "Inconel 718 Laser Powder Bed Fusion System", "Additive manufacturing of complex exhaust and turbo housings", 1850000, 54000, 0.6, 0.5, 1, 5),
    ("eq_amm_sieving_station", "mfg_additive_metal", "Automated Argon Powder Sieving & Recovery Unit", "Zero-waste metal powder recycling under inert atmosphere", 580000, 17000, 0.3, 0.4, 2, 5),
    ("eq_amm_vacuum_furnace", "mfg_additive_metal", "High-Vacuum Stress-Relief Heat Treatment Furnace", "Eliminates internal thermal stress in 3D-printed metal parts", 890000, 26000, 0.4, 0.6, 2, 5),
    ("eq_amm_wire_laser_dep", "mfg_additive_metal", "Directed Energy Deposition (DED) 5-Axis Cell", "Rapid buildup and repair of complex gearbox components", 1250000, 36000, 0.5, 0.4, 3, 5),

    # 22. Rapid Prototyping & 3D Printing Lab (mfg_rapid_proto)
    ("eq_rp_polyjet_multi", "mfg_rapid_proto", "Multi-Material PolyJet 3D Printer", "Produces rubber-gasket and rigid-composite hybrid test parts", 680000, 20000, 0.4, 0.3, 1, 5),
    ("eq_rp_carbon_fiber_fdm", "mfg_rapid_proto", "Continuous Carbon Fiber Reinforced FDM Printer", "Creates functional jig fixtures and test aero pieces", 540000, 16000, 0.4, 0.3, 1, 5),
    ("eq_rp_sla_optical", "mfg_rapid_proto", "Ultra-High Precision Micro-SLA Resin Printer", "Microscopic pitot tube and pressure sensor housing fabrication", 420000, 12000, 0.3, 0.4, 2, 5),
    ("eq_rp_fast_wash_cure", "mfg_rapid_proto", "Automated Ultrasonic Solvent Wash & UV Cure Station", "Prepares scale test parts in under 30 minutes", 350000, 10000, 0.2, 0.3, 2, 5),
    ("eq_rp_vacuum_casting", "mfg_rapid_proto", "Silicone Tooling & Vacuum Polyurethane Caster", "Produces short-run lightweight functional test enclosures", 480000, 14000, 0.3, 0.3, 3, 5),

    # 23. Monocoque Assembly Jig Bay (mfg_monocoque_jig)
    ("eq_jig_ground_chassis", "mfg_monocoque_jig", "Ground-Anchored Heavy Steel Monocoque Alignment Bed", "Laser-guided survival cell hardpoint alignment", 1350000, 39000, 0.4, 0.6, 1, 5),
    ("eq_jig_insert_pulltester", "mfg_monocoque_jig", "Hydraulic Threaded Insert Pull-Out Proof Tester", "Verifies suspension hardpoint pull strength over 50 kN", 680000, 20000, 0.2, 0.6, 1, 5),
    ("eq_jig_fia_rollhoop_rig", "mfg_monocoque_jig", "FIA Roll Hoop & Halo Static Proof-Load Rig", "Ensures driver safety survival cell passes mandatory tests", 920000, 27000, 0.3, 0.6, 2, 5),
    ("eq_jig_heated_bonding", "mfg_monocoque_jig", "Infrared Localized Structural Adhesive Curing Rig", "High-strength bonding of chassis bulkheads and floor mounts", 580000, 17000, 0.4, 0.4, 2, 5),
    ("eq_jig_datum_lasers", "mfg_monocoque_jig", "3D Coordinate Datum Laser Projector Array", "Maintains exact FIA chassis reference plane geometry", 740000, 22000, 0.3, 0.5, 3, 5),

    # 24. Quality Assurance & NDT Lab (test_qa_ndt)
    ("eq_ndt_ct_industrial", "test_qa_ndt", "Industrial 450kV CT Computed Tomography Scanner", "3D non-destructive internal scan for microscopic voids", 1950000, 56000, 0.2, 0.8, 1, 5),
    ("eq_ndt_ultrasound_phased", "test_qa_ndt", "Phased-Array Ultrasonic Flaw Detector", "Maps carbon fiber laminate delamination after track strikes", 820000, 24000, 0.2, 0.6, 1, 5),
    ("eq_ndt_eddy_current", "test_qa_ndt", "Eddy Current Surface Conductivity Tester", "Detects micro-fatigue cracks in titanium suspension joints", 610000, 18000, 0.1, 0.6, 2, 5),
    ("eq_ndt_dye_penetrant", "test_qa_ndt", "Fluorescent Dye Penetrant Inspection Line", "Fast UV verification of metallic brake and wheel parts", 430000, 13000, 0.1, 0.5, 2, 5),
    ("eq_ndt_optical_interferometer", "test_qa_ndt", "White-Light Optical Interferometer", "Nanometer-level surface roughness and seal verification", 780000, 23000, 0.3, 0.5, 3, 5),

    # 25. Exotic Alloy & TIG Welding Cell (mfg_exotic_welding)
    ("eq_wld_argon_chamber", "mfg_exotic_welding", "Argon-Purged Atmospheric Glove Box Welding Chamber", "Zero-oxygen titanium and Inconel paper-thin welding", 880000, 25000, 0.5, 0.5, 1, 5),
    ("eq_wld_pulsed_tig", "mfg_exotic_welding", "High-Frequency Pulsed Micro-TIG Inverter", "Precision welding of ultra-thin 0.5mm Inconel exhaust tubes", 640000, 19000, 0.4, 0.4, 1, 5),
    ("eq_wld_orbital_welder", "mfg_exotic_welding", "Automated Orbital Pipe Welding System", "Uniform circumferential welds on hydraulic and fuel pipes", 720000, 21000, 0.3, 0.6, 2, 5),
    ("eq_wld_backpurge_monitor", "mfg_exotic_welding", "Oxygen Back-Purge PPM Analyzer", "Prevents oxidation sugaring inside exhaust primary pipes", 410000, 12000, 0.2, 0.5, 2, 5),
    ("eq_wld_vacuum_braze", "mfg_exotic_welding", "Vacuum Alloy Brazing Furnace", "High-integrity joint bonding for oil coolers and heat shields", 830000, 24000, 0.4, 0.5, 3, 5),

    # 26. ERS & Hybrid Energy Facility (eng_ers)
    ("eq_ers_mguk_loadbank", "eng_ers", "High-Voltage MGU-K Load Bank", "120kW regenerative braking and torque deployment dyno", 1500000, 44000, 0.6, 0.4, 1, 5),
    ("eq_ers_cell_cycler", "eng_ers", "Lithium Battery High-Rate Cell Cycler", "Rapid charge-discharge thermal degradation profiler", 1100000, 32000, 0.4, 0.6, 1, 5),
    ("eq_ers_sic_inverter", "eng_ers", "Silicon-Carbide (SiC) Inverter Lab", "99% efficiency high-frequency power inverter test bay", 1750000, 50000, 0.7, 0.3, 2, 5),
    ("eq_ers_thermal_dielectric", "eng_ers", "Dielectric Immersion Cooling Rig", "Sub-ambient direct fluid battery thermal controller", 980000, 28000, 0.5, 0.5, 2, 5),
    ("eq_ers_ultra_cap", "eng_ers", "Supercapacitor Fast-Burst Module", "Maximum instantaneous torque boost out of slow hairpins", 1300000, 38000, 0.8, -0.1, 3, 5),

    # =========================================================================
    # LAYER 4: APEX FACILITIES & POLISH
    # =========================================================================
    # 27. Underbody & Diffuser Lab (eng_floor)
    ("eq_fl_venturi_laser", "eng_floor", "Venturi Tunnel Laser Profiler", "Sub-millimeter underbody ground-effect mapping", 920000, 27000, 0.7, 0.2, 1, 5),
    ("eq_fl_skirt_seal", "eng_floor", "Pneumatic Floor Edge Sealing Rig", "Vortex barrier sealing for massive suction grip", 780000, 23000, 0.6, 0.2, 1, 5),
    ("eq_fl_plank_wear_sensor", "eng_floor", "Titanium Skid Block Wear Monitor", "Ride height optimization without plank breach penalty", 540000, 16000, 0.3, 0.6, 2, 5),
    ("eq_fl_diffuser_expansion", "eng_floor", "Diffuser Expansion Angle Jig", "Prevents high-speed floor stalling and porpoising", 860000, 25000, 0.7, 0.3, 2, 5),
    ("eq_fl_stiffness_jig", "eng_floor", "Underbody Torsional Rigidity Frame", "Eliminates high-G bottoming out and flexing", 690000, 20000, 0.4, 0.5, 3, 5),

    # 28. Paint & Ultra-Thin Livery Bay (mfg_paint_bay)
    ("eq_pnt_electrostatic_gun", "mfg_paint_bay", "Electrostatic Micro-Sprayer Gun System", "Applies uniform 15-micron paint layer with zero runs", 460000, 13000, 0.3, 0.3, 1, 5),
    ("eq_pnt_low_weight_pigment", "mfg_paint_bay", "Ultra-Lightweight Micro-Pigment Dispersion Mill", "Saves 3.5 kg of total car weight across bodywork", 620000, 18000, 0.5, 0.1, 1, 5),
    ("eq_pnt_boundary_topcoat", "mfg_paint_bay", "Hydrophobic Riblet Aero Topcoat Cell", "Micro-grooved clearcoat reducing skin friction drag by 2%", 850000, 25000, 0.6, 0.2, 2, 5),
    ("eq_pnt_ir_curing_arch", "mfg_paint_bay", "Rapid Infrared Livery Curing Gantry", "Full livery paint curing in under 45 minutes", 390000, 11000, 0.2, 0.3, 2, 5),
    ("eq_pnt_matte_aero_finish", "mfg_paint_bay", "Matte Texture Boundary Layer Surface Polisher", "Eliminates boundary layer flow separation over sidepods", 520000, 15000, 0.4, 0.2, 3, 5),

    # 29. Chassis Rigidity & Torsional Rig (test_torsional_rig)
    ("eq_tor_hydraulic_frame", "test_torsional_rig", "Heavy Multi-Axis Hydraulic Torsion Bed", "Applies 30,000 Nm/deg torque loads to bare chassis tubs", 1250000, 36000, 0.5, 0.6, 1, 5),
    ("eq_tor_laser_deflection", "test_torsional_rig", "Optical Laser Grid Chassis Deflection Mapper", "Pinpoints micro-deflections between front and rear axles", 820000, 24000, 0.4, 0.5, 1, 5),
    ("eq_tor_suspension_load_sim", "test_torsional_rig", "Simulated Cornering Load Hardpoint Actuators", "Tests full lateral suspension load transfer into tub", 940000, 27000, 0.5, 0.4, 2, 5),
    ("eq_tor_cockpit_stiffness", "test_torsional_rig", "Cockpit Opening Reinforcement Proof Frame", "Maintains aero platform stability without chassis twist", 680000, 20000, 0.3, 0.6, 2, 5),
    ("eq_tor_dynamic_fatigue", "test_torsional_rig", "1,000,000-Cycle Dynamic Torsional Fatigue Shaker", "Guarantees monocoque integrity across multiple seasons", 1100000, 32000, 0.3, 0.7, 3, 5),

    # 30. Works Engine Factory (eng_works_powertrain)
    ("eq_wp_porting_cnc", "eng_works_powertrain", "5-Axis Cylinder Head Porting CNC", "Diamond-tooled intake and exhaust port profiling", 2500000, 72000, 0.8, 0.3, 1, 5),
    ("eq_wp_crank_balancer", "eng_works_powertrain", "Dynamic Crankshaft Balancer", "Sub-gram rotational balancing up to 16,000 RPM", 1400000, 40000, 0.5, 0.5, 1, 5),
    ("eq_wp_lmf_titanium_3d", "eng_works_powertrain", "Laser Metal Fusion 3D Titanium Printer", "Direct titanium hollow turbine and piston additive builder", 3200000, 95000, 0.9, 0.4, 1, 5),
    ("eq_wp_plasma_coating", "eng_works_powertrain", "Plasma Thermal Barrier Bore Coater", "Low-friction ceramic plasma cylinder wall deposition", 1800000, 52000, 0.6, 0.5, 2, 5),
    ("eq_wp_vtg_turbo_rig", "eng_works_powertrain", "Variable Geometry Turbo Test Rig", "Twin-scroll electronic wastegate response mapper", 1650000, 48000, 0.7, 0.4, 2, 5),
    ("eq_wp_800v_battery_pack", "eng_works_powertrain", "Liquid-Cooled 800V Battery Assembler", "High-discharge lithium prismatic cell balancing rig", 2600000, 76000, 0.8, 0.4, 3, 5),

    # =========================================================================
    # OPERATIONS, COMMERCIAL & DRIVER PERFORMANCE
    # =========================================================================
    # 31. Recruitment Desk (hr_recruitment)
    ("eq_hr_talent_db", "hr_recruitment", "Global Paddock Talent Scouting Index", "Scans worldwide motorsport engineer credentials", 280000, 8000, 0.0, 0.0, 1, 5),
    ("eq_hr_aptitude_term", "hr_recruitment", "Cognitive Aptitude Testing Terminals", "Psychometric engineer assessment testing", 220000, 6000, 0.0, 0.0, 1, 5),
    ("eq_hr_visa_suite", "hr_recruitment", "Automated Visa & Licensing Suite", "Rapid specialist international credentialing", 180000, 5000, 0.0, 0.0, 2, 5),
    ("eq_hr_ai_screening", "hr_recruitment", "Automated Resume AI Screening Bot", "Fast filtering of candidate specialist applications", 310000, 9000, 0.0, 0.0, 2, 5),
    ("eq_hr_onboarding_pod", "hr_recruitment", "Immersive VR Onboarding Station", "Rapid factory layout & safety orientation", 250000, 7000, 0.0, 0.0, 3, 5),

    # 32. Auto-Headhunter (hr_headhunter)
    ("eq_hh_rival_intel", "hr_headhunter", "Rival Engineer Poaching Database", "Monitors rival team staff contracts and expiration dates", 650000, 19000, 0.0, 0.0, 1, 5),
    ("eq_hh_comp_index", "hr_headhunter", "Paddock Compensation Benchmark Index", "Optimal salary offer generation to minimize wage disputes", 420000, 12000, 0.0, 0.0, 1, 5),
    ("eq_hh_nda_protocol", "hr_headhunter", "Confidential Outbound Negotiation AI", "Secures top department leads anonymously", 540000, 16000, 0.0, 0.0, 2, 5),
    ("eq_hh_retention_alert", "hr_headhunter", "Anti-Poaching Threat Alert System", "Detects when rival constructors approach your key personnel", 610000, 18000, 0.0, 0.0, 3, 5),

    # 33. Staff Campus (hr_welfare)
    ("eq_wf_cryo_recovery", "hr_welfare", "Cryotherapy Staff Recovery Pods", "Sub-zero recovery chambers for engineering burnout reduction", 480000, 14000, 0.0, 0.0, 1, 5),
    ("eq_wf_gym_physio", "hr_welfare", "Biomechanics Gym & Physio Suite", "High-performance fitness center for factory crew", 550000, 16000, 0.0, 0.0, 1, 5),
    ("eq_wf_cafeteria", "hr_welfare", "Michelin-Standard Staff Nutrition Cell", "Boosts daily staff cognitive alertness & morale", 390000, 11000, 0.0, 0.0, 2, 5),
    ("eq_wf_childcare", "hr_welfare", "On-Site Family & Childcare Facility", "Top talent retention boost and anti-poaching shield", 450000, 13000, 0.0, 0.0, 3, 5),

    # =========================================================================
    # COMMERCIAL & MARKETING FACILITIES
    # =========================================================================
    # 34. Press Office & Public Relations (mkt_press)
    ("eq_pr_wire_service", "mkt_press", "Global Motorsport PR Wire Syndication", "Direct syndication to 400+ international motorsport outlets", 280000, 8000, 0.0, 0.0, 1, 5),
    ("eq_pr_crisis_center", "mkt_press", "Crisis Communications & Embargo Room", "Rapid response messaging mitigating rep loss from crashes/penalties", 360000, 10000, 0.0, 0.0, 1, 5),
    ("eq_pr_media_briefing_lounge", "mkt_press", "Media Briefing & Press Conference Stage", "Elevates sponsor announcement broadcast production values", 420000, 12000, 0.0, 0.0, 2, 5),
    ("eq_pr_monitoring_suite", "mkt_press", "Broadcast & Editorial Sentiment Monitor", "Tracks worldwide sponsor brand exposure and impressions", 490000, 14000, 0.0, 0.0, 3, 5),

    # 35. Brand Strategy & Graphic Design Studio (mkt_brand_design)
    ("eq_des_wacom_cintiq", "mkt_brand_design", "32\" 4K Color-Accurate Design Displays", "High-precision livery styling and sponsor branding placement", 240000, 7000, 0.0, 0.0, 1, 5),
    ("eq_des_vinyl_plotter", "mkt_brand_design", "Precision CNC Livery Vinyl Cutter", "Fast on-demand sponsor decal fabrication for race weekends", 310000, 9000, 0.0, 0.0, 1, 5),
    ("eq_des_3d_render_farm", "mkt_brand_design", "Photorealistic 3D Livery Render Node", "Generates high-resolution sponsor presentation decks", 440000, 13000, 0.0, 0.0, 2, 5),
    ("eq_des_pantone_booth", "mkt_brand_design", "Pantone Color Proofing & Match Booth", "Ensures 100% color accuracy for corporate partner logos", 380000, 11000, 0.0, 0.0, 3, 5),

    # 36. Social Media & Digital Channels (mkt_digital)
    ("eq_dig_mobile_creators", "mkt_digital", "Paddock Mobile Creator & Gimbal Rig", "Instant behind-the-scenes social content for TikTok and Instagram", 220000, 6000, 0.0, 0.0, 1, 5),
    ("eq_dig_content_hub", "mkt_digital", "High-Speed Media Ingest & Clip Transcoder", "Live race-session highlights published within 60 seconds", 350000, 10000, 0.0, 0.0, 1, 5),
    ("eq_dig_community_bot", "mkt_digital", "AI Community Moderation & Engagement Bot", "Monitors fan discussions, memes, and boosts viral engagement", 290000, 8500, 0.0, 0.0, 2, 5),
    ("eq_dig_stream_rack", "mkt_digital", "Multi-Platform Live Streaming Ingest Server", "Direct paddock streaming to Twitch, YouTube, and Weibo", 460000, 13000, 0.0, 0.0, 3, 5),

    # 37. Merchandising Development & Retail Team (mkt_merch)
    ("eq_merch_dtg_printer", "mkt_merch", "Direct-to-Garment High-Speed Textile Printer", "Produces premium team caps, hoodies, and replica driver kits", 380000, 11000, 0.0, 0.0, 1, 5),
    ("eq_merch_heat_press", "mkt_merch", "Pneumatic 4-Station Heat Transfer Press", "Fast sponsor badge application onto official race teamwear", 260000, 7500, 0.0, 0.0, 1, 5),
    ("eq_merch_display_kiosk", "mkt_merch", "Trackside Pop-Up Merch Display Kiosks", "Maximizes trackside race weekend fan merchandise revenue", 420000, 12000, 0.0, 0.0, 2, 5),
    ("eq_merch_inventory_rfid", "mkt_merch", "Automated RFID Merch Inventory Tracker", "Zero stockouts on high-demand driver victory merchandise", 340000, 10000, 0.0, 0.0, 3, 5),

    # 38. Fan Club & Community Loyalty Program (mkt_fan_club)
    ("eq_fc_portal_server", "mkt_fan_club", "Exclusive Member Portal & Streaming Server", "Paid subscriber hub with exclusive video podcasts and blogs", 320000, 9000, 0.0, 0.0, 1, 5),
    ("eq_fc_badge_printer", "mkt_fan_club", "RFID Member Card & Paddock Pass Embosser", "Custom physical member cards and VIP factory tour passes", 240000, 7000, 0.0, 0.0, 1, 5),
    ("eq_fc_voting_rig", "mkt_fan_club", "Fan Voting & Interactive Poll Hardware Server", "Lets paid members vote on special liveries and driver helmet art", 380000, 11000, 0.0, 0.0, 2, 5),
    ("eq_fc_merch_packager", "mkt_fan_club", "Welcome Box Automated Fulfillment Station", "Dispatches quarterly exclusive gift boxes to loyal members", 450000, 13000, 0.0, 0.0, 3, 5),

    # 39. Media Production & Broadcast Studio (mkt_studio)
    ("eq_stu_soundstage", "mkt_studio", "Acoustic-Treated 800 sq ft In-House Soundstage", "Soundproof film studio for commercials and sponsor launches", 650000, 19000, 0.0, 0.0, 1, 5),
    ("eq_stu_green_screen", "mkt_studio", "Infinity Cyc Green Screen & LED Volume Wall", "Virtual cinematic background environments for car launches", 820000, 24000, 0.0, 0.0, 1, 5),
    ("eq_stu_4k_cameras", "mkt_studio", "Cinema-Grade 4K Studio Camera Array", "High frame-rate 240fps slow-motion capture of aero parts and drivers", 590000, 17000, 0.0, 0.0, 2, 5),
    ("eq_stu_audio_suite", "mkt_studio", "Dolby Atmos Voiceover & Sound Mixing Suite", "Documentary-grade audio mastering for Netflix-style series", 480000, 14000, 0.0, 0.0, 3, 5),

    # 40. VIP Hospitality Suite & Paddock Club (mkt_hospitality)
    ("eq_hosp_espresso_bar", "mkt_hospitality", "Artisanal Italian Espresso & Cocktail Bar", "Premium trackside hospitality bar delighting title sponsors", 420000, 12000, 0.0, 0.0, 1, 5),
    ("eq_hosp_chef_galley", "mkt_hospitality", "Modular Induction Chef Catering Galley", "Michelin-caliber culinary service in the Grand Prix paddock", 580000, 17000, 0.0, 0.0, 1, 5),
    ("eq_hosp_glass_terrace", "mkt_hospitality", "Climate-Controlled Paddock View Glass Terrace", "Unrivaled panoramic view directly above the pit garages", 950000, 28000, 0.0, 0.0, 2, 5),
    ("eq_hosp_vip_lounge", "mkt_hospitality", "Executive Leather Boardroom & Hologram Display", "Private soundproof multi-million dollar sponsor negotiation suite", 1100000, 32000, 0.0, 0.0, 3, 5),

    # 41. Licensing & Brand Partnerships (mkt_licensing)
    ("eq_lic_3d_scanner", "mkt_licensing", "High-Res Optical 3D Asset Scanner for Gaming", "Licenses CAD geometry to official racing games and sims", 460000, 13000, 0.0, 0.0, 1, 5),
    ("eq_lic_diecast_tooling", "mkt_licensing", "Scale Model Prototype & Diecast Tooling Lab", "Precision 1:18 and 1:43 collector car model licensing", 390000, 11000, 0.0, 0.0, 1, 5),
    ("eq_lic_apparel_archive", "mkt_licensing", "Historical Textile & Brand Style Guide Archive", "Licenses team brand to luxury streetwear and watchmakers", 520000, 15000, 0.0, 0.0, 2, 5),
    ("eq_lic_legal_vault", "mkt_licensing", "Encrypted IP Trademark & Royalty Accounting Suite", "Maximizes global licensing royalty collections and compliance", 580000, 17000, 0.0, 0.0, 3, 5),

    # 42. Sim Racing & Esports Operations (mkt_esports)
    ("eq_esp_sim_pods", "mkt_esports", "Pro-Grade Triple-Screen Motion Sim Pods", "Equips factory esports team for global virtual championships", 520000, 15000, 0.0, 0.0, 1, 5),
    ("eq_esp_broadcast_booth", "mkt_esports", "Esports Live Shoutcaster & Stream Booth", "Broadcasts virtual Grand Prix races with sponsor overlays", 410000, 12000, 0.0, 0.0, 1, 5),
    ("eq_esp_driver_coach", "mkt_esports", "Biometric Esports Reaction & Telemetry Rig", "Discovers prospective real-world junior driving talent", 360000, 10000, 0.0, 0.0, 2, 5),
    ("eq_esp_server_cluster", "mkt_esports", "Ultra-Low Latency Dedicated League Server Rack", "Flawless hosting for global esports tournaments", 490000, 14000, 0.0, 0.0, 3, 5),

    # 43. Heritage Collection & Public Showroom (mkt_heritage)
    ("eq_mus_carbon_plinths", "mkt_heritage", "Illuminated Carbon Chassis Display Plinths", "Showcases championship-winning chassis in museum hall", 680000, 20000, 0.0, 0.0, 1, 5),
    ("eq_mus_trophy_vitrine", "mkt_heritage", "Climate-Controlled Anti-Reflective Trophy Cases", "Preserves historic Grand Prix gold and crystal trophies", 450000, 13000, 0.0, 0.0, 1, 5),
    ("eq_mus_interactive_kiosks", "mkt_heritage", "Interactive Touchscreen History & Audio Kiosks", "Public tour exhibits narrating team heritage and legendary races", 380000, 11000, 0.0, 0.0, 2, 5),
    ("eq_mus_tour_audio_fleet", "mkt_heritage", "Multi-Language Digital Tour Headset Fleet", "Maximizes ticket revenue from international tourist visits", 320000, 9000, 0.0, 0.0, 3, 5),

    # 44. Customer Racing Sales & Client Relations (mkt_customer_racing)
    ("eq_cr_transporter", "mkt_customer_racing", "Dedicated Enclosed Historic F1 Transporter Rig", "Delivers retired race chassis to private client track events", 1400000, 42000, 0.0, 0.0, 1, 5),
    ("eq_cr_trackside_pit", "mkt_customer_racing", "VIP Track Day Pit Garage Support Rig", "Full engineer and mechanic crew support for wealthy owner-drivers", 1650000, 48000, 0.0, 0.0, 1, 5),
    ("eq_cr_telemetry_tutor", "mkt_customer_racing", "Dual-Seat Driver Coaching Data System", "Live video and telemetry coaching for gentleman drivers", 880000, 26000, 0.0, 0.0, 2, 5),
    ("eq_cr_concierge_lounge", "mkt_customer_racing", "Private Owner Lounge & Custom Race Suit Tailoring", "Ultra-luxury hospitality attracting billionaire investors", 1250000, 36000, 0.0, 0.0, 3, 5),

    # =========================================================================
    # TRACKSIDE & PIT CREW
    # =========================================================================
    ("eq_pit_guns_pneumatic", "track_pitrig", "15mm High-Flow Pneumatic Guns", "14,000 RPM wheel-nut attachment guns", 350000, 10000, 0.0, 0.0, 1, 5),
    ("eq_pit_front_jack", "track_pitrig", "Front Quick-Drop Pivot Jack Rig", "Sub-0.4s front car lifting mechanism", 280000, 8000, 0.0, 0.0, 1, 5),
    ("eq_pit_rear_steer_jack", "track_pitrig", "Rear Steerable Heavy Jack Rig", "Fast rear wheel alignment and car release", 290000, 8500, 0.0, 0.0, 1, 5),
    ("eq_pit_traffic_gantry", "track_pitrig", "Pit Stop Traffic Light Gantry", "Automated green-light pit release sensor array", 410000, 12000, 0.0, 0.0, 2, 5),
    ("eq_pit_laser_guide", "track_pitrig", "Laser Wheel-Nut Alignment Guidance", "Optical target overlay for wheel gunners", 480000, 14000, 0.0, 0.0, 3, 5),

    # 38. Carbon Wheel Guns (track_wheelguns)
    ("eq_wg_carbon_shell", "track_wheelguns", "Ultra-Light Carbon Fiber Gun Shells", "Cuts wheel gun weight by 45% for faster handling", 580000, 17000, 0.0, 0.0, 1, 5),
    ("eq_wg_torque_telemetry", "track_wheelguns", "Wireless Torque Telemetry Sockets", "Instant verification of 600 Nm locking torque", 640000, 19000, 0.0, 0.0, 1, 5),
    ("eq_wg_quick_lance", "track_wheelguns", "Coaxial Air-Supply High-Flow Lances", "Zero pressure drop during rapid wheel nut bursts", 420000, 12000, 0.0, 0.0, 2, 5),
    ("eq_wg_laser_targeting", "track_wheelguns", "Laser Hub Target Optical Lock", "Eliminates gunner misalignment cross-threading", 720000, 21000, 0.0, 0.0, 3, 5),

    # 39. Radar Station & Track Telemetry (track_telemetry)
    ("eq_tel_doppler_radar", "track_telemetry", "Doppler Live Weather Radar Array", "Minute-by-minute rain cloud tracking with 99% accuracy", 550000, 16000, 0.0, 0.0, 1, 5),
    ("eq_tel_pitwall_server", "track_telemetry", "Pit Wall Real-Time Strategy Server", "Monte Carlo undercut and tire delta predictor", 680000, 20000, 0.0, 0.0, 1, 5),
    ("eq_tel_radio_telemetry", "track_telemetry", "High-Bandwidth Encrypted Telemetry Link", "Live 1000Hz sensor data stream directly from cars", 480000, 14000, 0.0, 0.0, 2, 5),
    ("eq_tel_tire_ir_cam", "track_telemetry", "Pit Lane Infrared Tire Surface Camera", "Instant 4-wheel thermal degradation mapping", 520000, 15000, 0.0, 0.0, 3, 5),

    # 40. Rapid Repair Gantry (track_fast_repair)
    ("eq_rep_quick_latch_jig", "track_fast_repair", "Hydraulic Front Wing Quick-Latch Jig", "Cuts nose cone alignment & latch time by 0.3s per level", 450000, 13000, 0.0, 0.0, 1, 5),
    ("eq_rep_rapid_curing_resin", "track_fast_repair", "UV-Flash Composite Curing System", "Instant high-strength carbon bonding, raises emergency repair durability", 580000, 17000, 0.0, 0.0, 2, 5),
    ("eq_rep_pneumatic_riveter", "track_fast_repair", "Multi-Spindle Pneumatic Riveter", "High-speed bodywork fastener guns (-0.4s repair box time per level)", 620000, 18000, 0.0, 0.0, 3, 5),

    # 41. Active Jack & Release (track_jack_release)
    ("eq_jck_sub02_pivot", "track_jack_release", "Sub-0.2s Pneumatic Pivot Jack", "Rapid pneumatic lift gantry (-0.15s base pit stop per level)", 650000, 19000, 0.0, 0.0, 1, 5),
    ("eq_jck_laser_traffic", "track_jack_release", "Optical Green-Light Release Gantry", "Zero-lag automated release scanner, prevents unsafe release errors", 780000, 23000, 0.0, 0.0, 2, 5),
    ("eq_jck_magnesium_skids", "track_jack_release", "Magnesium Quick-Release Skids", "Ultra-low friction release pads shaving crucial split seconds", 720000, 21000, 0.0, 0.0, 3, 5),

    # 42. Paddock Recon Unit (track_rival_intel)
    ("eq_intel_telephoto_array", "track_rival_intel", "800mm High-Speed Pit Telephoto Array", "High-res optical capture of rival aero elements (+10% copy roll chance/level)", 480000, 14000, 0.0, 0.0, 1, 5),
    ("eq_intel_acoustic_microphones", "track_rival_intel", "Parabolic Acoustic Engine Listening Masts", "Acoustic frequency analysis of rival turbo spools (+5% copy success/level)", 560000, 16000, 0.0, 0.0, 2, 5),
    ("eq_intel_paddock_scouts", "track_rival_intel", "Encrypted Paddock Radio Scanner", "Intercepts rival tire degradation & strategy communications", 640000, 19000, 0.0, 0.0, 3, 5),

    # 43. Optical Telemetry Intercept (track_reverse_eng)
    ("eq_rev_lidar_scanner", "track_reverse_eng", "Pit-Straight LIDAR Dynamic Ride-Height Profiler", "Profiles competitor underfloor suction (+15% copy knowledge gain/level)", 820000, 24000, 0.0, 0.0, 1, 5),
    ("eq_rev_photogrammetry_ai", "track_reverse_eng", "Automated CAD Photogrammetry Reconstruction Suite", "Reconstructs 3D CAD surfaces from rival photos (reduces lockout time)", 950000, 28000, 0.0, 0.0, 2, 5),
    ("eq_rev_tire_thermal_imager", "track_reverse_eng", "Dual-Band Infrared Heat Signature Profiler", "Profiles rival tire surface pressure and thermal dissipation", 890000, 26000, 0.0, 0.0, 3, 5),

    # 44. Doppler Weather Radar (track_weather_station)
    ("eq_met_xband_doppler", "track_weather_station", "X-Band Dual-Polarization Mobile Weather Mast", "Extends weather radar lookahead horizon by +2 laps per level", 580000, 17000, 0.0, 0.0, 1, 5),
    ("eq_met_barometric_array", "track_weather_station", "Micro-Barometric Pressure Sensor Ring", "Detects localized rain fronts minutes ahead of cloud formation", 640000, 19000, 0.0, 0.0, 2, 5),
    ("eq_met_ai_cloud_tracking", "track_weather_station", "Supercomputer Trackside Microclimate Modeling Server", "Eliminates rain prediction error with 100% accurate intensity forecast", 820000, 24000, 0.0, 0.0, 3, 5),

    # 45. Setup Analytics (track_setup_telemetry)
    ("eq_set_laser_ride_sensors", "track_setup_telemetry", "4-Corner Dynamic Laser Ride Height Sensors", "Narrows aerodynamic wing setup target ranges in practice by 2 pts/level", 620000, 18000, 0.0, 0.0, 1, 5),
    ("eq_set_pushrod_strain_links", "track_setup_telemetry", "Pushrod Dynamic Strain Telemetry Links", "Accurately measures wheel loads to narrow suspension stiffness guidance", 690000, 20000, 0.0, 0.0, 2, 5),
    ("eq_set_brake_rotor_pyrometers", "track_setup_telemetry", "Wireless Wheel Hub Thermal Pyrometers", "Calibrates brake bias and gear spread sweet spot ranges", 750000, 22000, 0.0, 0.0, 3, 5),

    # 46. Virtual FP Solver (track_virtual_sim)
    ("eq_vsim_cloud_cluster", "track_virtual_sim", "Distributed Cloud Setup Solver Cluster", "Simulates 5,000 synthetic laps; seeds FP1 baseline closer to optimum", 980000, 29000, 0.0, 0.0, 1, 5),
    ("eq_vsim_tire_degrade_sim", "track_virtual_sim", "Hardware-in-the-Loop Rubber Friction Bench", "Boosts initial setup confidence by +5% per level", 1100000, 32000, 0.0, 0.0, 2, 5),
    ("eq_vsim_driver_neural_link", "track_virtual_sim", "Synthetic Driver Neural Simulation Matrix", "Virtually dials in gearing and wing balance before cars hit the circuit", 1350000, 39000, 0.0, 0.0, 3, 5),

    # 47. Factory Mission Control (track_comm_uplink)
    ("eq_uplink_satellite_transceiver", "track_comm_uplink", "Geostationary 10Gbps Ku-Band Satellite Transceiver", "Streams live car data to factory (+5% post-race knowledge across all parts/lvl)", 850000, 25000, 0.3, 0.2, 1, 5),
    ("eq_uplink_edge_telemetry", "track_comm_uplink", "Trackside Edge Telemetry Compression Engine", "Direct real-time CAD feed (+0.1% reliability gain to all parts per race/lvl)", 920000, 27000, 0.2, 0.3, 2, 5),
    ("eq_uplink_mission_control_desk", "track_comm_uplink", "Factory Operations Mission Control Bridge", "Integrated dual-site race engineers coordinating continuous upgrades", 1250000, 36000, 0.4, 0.3, 3, 5),

    # 48. Static Sim Rig (driver_sim)
    ("eq_sim_direct_drive", "driver_sim", "Direct-Drive Force Feedback Base", "30 Nm instantaneous torque steering wheel base", 290000, 8500, 0.0, 0.0, 1, 5),
    ("eq_sim_pano_screen", "driver_sim", "270° Cylindrical Panoramic Screen", "Immersive laser projection with zero input latency", 380000, 11000, 0.0, 0.0, 1, 5),
    ("eq_sim_hydraulic_pedals", "driver_sim", "Hydraulic 200kg Load Cell Pedals", "Accurate brake pressure modulation training", 240000, 7000, 0.0, 0.0, 2, 5),
    ("eq_sim_monocoque_shell", "driver_sim", "FIA Carbon Monocoque Cockpit Shell", "Exact real-world driving position familiarity", 320000, 9500, 0.0, 0.0, 3, 5),
    # 49. Driver-in-the-Loop Hexapod Sim (driver_motion_sim)
    ("eq_msim_6dof_hexapod", "driver_motion_sim", "6-DOF Electro-Hydraulic Hexapod Platform", "Full pitch, roll, yaw, heave, sway, and surge dynamics", 1850000, 55000, 0.0, 0.0, 1, 5),
    ("eq_msim_gseat_bladders", "driver_motion_sim", "Dynamic G-Seat Pressure Actuators", "Multi-cell pneumatic lateral G-force simulation", 890000, 26000, 0.0, 0.0, 1, 5),
    ("eq_msim_vr_helmet", "driver_motion_sim", "Ultra-HD 8K VR Helmet Tracking", "Eye-tracking and peripheral vision immersion", 620000, 18000, 0.0, 0.0, 2, 5),
    ("eq_msim_curb_shakers", "driver_motion_sim", "Tactile Kerb & Bump Transducer Array", "Sub-millisecond chassis vibration feedback", 480000, 14000, 0.0, 0.0, 3, 5),

    # 50. Neuro-Reflex Lab (driver_vr_cognitive)
    ("eq_cog_batak_pro", "driver_vr_cognitive", "Batak Pro LED Reaction Matrix", "High-speed reflex reaction & peripheral visual response", 320000, 9500, 0.0, 0.0, 1, 5),
    ("eq_cog_neuro_headset", "driver_vr_cognitive", "64-Channel EEG Cognitive Monitor", "Neural load & focus endurance telemetry under stress", 450000, 13000, 0.0, 0.0, 1, 5),
    ("eq_cog_eye_tracker", "driver_vr_cognitive", "Saccadic Eye-Tracking Glasses", "Apex fixations and track scanning efficiency analysis", 380000, 11000, 0.0, 0.0, 2, 5),
    ("eq_cog_strobe_glasses", "driver_vr_cognitive", "Stroboscopic Visual Reflex Lenses", "High-frequency visual occlusion for split-second decisions", 290000, 8500, 0.0, 0.0, 3, 5),

    # 51. Biometric Athletic Gym & Heat Chamber (driver_gym_conditioning)
    ("eq_gym_neck_dyno", "driver_gym_conditioning", "6-Axis Cervical Neck Dynamometer", "Simulates sustained 5G cornering loads on driver cervical muscles", 340000, 10000, 0.0, 0.0, 1, 5),
    ("eq_gym_heat_chamber", "driver_gym_conditioning", "45°C Humidity Heat Acclimation Cell", "Sauna endurance conditioning for high-temp races", 480000, 14000, 0.0, 0.0, 1, 5),
    ("eq_gym_vo2_ergometer", "driver_gym_conditioning", "Hypoxic VO2 Max Cycle Ergometer", "Altitude oxygen restriction cardiovascular conditioning", 420000, 12000, 0.0, 0.0, 2, 5),
    ("eq_gym_cable_rig", "driver_gym_conditioning", "Inertial Flywheel Core Strength Rig", "Zero-gravity eccentric core resistance trainer", 310000, 9000, 0.0, 0.0, 3, 5),

    # 52. Physio & Longevity Clinic (driver_physio_recovery)
    ("eq_phy_cryo_chamber", "driver_physio_recovery", "-130°C Cryotherapy Chamber", "Liquid nitrogen whole-body recovery & muscle inflammation reduction", 550000, 16000, 0.0, 0.0, 1, 5),
    ("eq_phy_hyperbaric_pod", "driver_physio_recovery", "2.0 ATA Hyperbaric Oxygen Pod", "Accelerated cellular rejuvenation and micro-tear healing", 680000, 20000, 0.0, 0.0, 1, 5),
    ("eq_phy_pneumatic_boots", "driver_physio_recovery", "Dynamic Sequential Compression Boots", "Rapid lactic acid flush and lymphatic drainage", 280000, 8000, 0.0, 0.0, 2, 5),
    ("eq_phy_myofascial_laser", "driver_physio_recovery", "Class IV Deep-Tissue Laser System", "Therapeutic deep tissue laser for tendon resilience", 490000, 14000, 0.0, 0.0, 3, 5),

    # 53. Media & PR Studio (driver_media_pr_coach)
    ("eq_med_press_podium", "driver_media_pr_coach", "FIA Press Conference Simulation Theater", "Realistic podium lighting and adversarial press scrum drills", 360000, 10500, 0.0, 0.0, 1, 5),
    ("eq_med_teleprompter", "driver_media_pr_coach", "Crisis Communications Prompt Rig", "Rapid rebuttal training during controversial incidents", 290000, 8500, 0.0, 0.0, 1, 5),
    ("eq_med_vocal_acoustics", "driver_media_pr_coach", "Broadcast Acoustic Voice Coach Booth", "Clarity, cadence, and broadcast charisma modulation", 340000, 9800, 0.0, 0.0, 2, 5),
    ("eq_med_body_language", "driver_media_pr_coach", "AI Facial & Eye-Contact Tracking Rig", "Refines body language confidence and poise on camera", 420000, 12000, 0.0, 0.0, 3, 5),

    # 54. Radio Comms Lab (driver_radio_comms_lab)
    ("eq_rad_cockpit_noise_gen", "driver_radio_comms_lab", "115dB Cockpit Acoustic Noise Sim", "Simulates deafening V6 turbo-hybrid roar and wind noise", 380000, 11000, 0.0, 0.0, 1, 5),
    ("eq_rad_dsp_intercom", "driver_radio_comms_lab", "Active Noise-Canceling DSP Intercom", "Military-spec speech intelligibility under extreme vibration", 440000, 12500, 0.0, 0.0, 1, 5),
    ("eq_rad_code_drills", "driver_radio_comms_lab", "Tactical Strategy Shorthand Console", "Split-second pit window & tire delta protocol drills", 320000, 9000, 0.0, 0.0, 2, 5),
    ("eq_rad_telemetry_sync", "driver_radio_comms_lab", "Synchronous Audio & Telemetry Replay", "Aligns driver corner feedback with physical suspension data", 510000, 15000, 0.0, 0.0, 3, 5),

    # 55. Sponsor & Corporate VIP Suite (driver_commercial_suite)
    ("eq_com_sponsor_keynote", "driver_commercial_suite", "Holographic Keynote Pitch Stage", "Corporate sponsor pitch rehearsals and product reveals", 540000, 15500, 0.0, 0.0, 1, 5),
    ("eq_com_social_studio", "driver_commercial_suite", "4K High-Speed Content Production Bay", "Rapid viral social media video and lifestyle filming", 390000, 11000, 0.0, 0.0, 1, 5),
    ("eq_com_merch_fit", "driver_commercial_suite", "Driver Signature Merch Styling Cell", "Personalized caps, helmets, and team wear design fittings", 310000, 9000, 0.0, 0.0, 2, 5),
    ("eq_com_vip_hospitality", "driver_commercial_suite", "Executive Sponsor Meet-and-Greet Dining Suite", "Private dining for corporate partners and title sponsors", 620000, 18000, 0.0, 0.0, 3, 5),

    # 56. Driver Academy (driver_academy)
    ("eq_acad_scout_network", "driver_academy", "Global Karting Talent Scouting Index", "Identifies future world champion junior talent early", 450000, 13000, 0.0, 0.0, 1, 5),
    ("eq_acad_telemetry_comp", "driver_academy", "Junior Telemetry Comparison Software", "Direct overlay of junior driver telemetry vs pro telemetry", 380000, 11000, 0.0, 0.0, 1, 5),
    ("eq_acad_reaction_board", "driver_academy", "Batak Pro Reaction Light Wall", "Improves reflex speed and peripheral hand-eye coordination", 240000, 7000, 0.0, 0.0, 2, 5),
    ("eq_acad_sim_fleet", "driver_academy", "Feeder Series Junior Simulator Fleet", "Multi-driver racecraft and overtake scenario drills", 560000, 16000, 0.0, 0.0, 3, 5),

    # 57. Grassroots Karting Foundation (driver_karting_scholarship)
    ("eq_kart_telemetry_beacon", "driver_karting_scholarship", "Global Karting Telemetry Beacon Net", "GPS micro-sector tracking across regional karting circuits", 460000, 13500, 0.0, 0.0, 1, 5),
    ("eq_kart_chassis_bench", "driver_karting_scholarship", "Homologated Kart Chassis Alignment Rig", "Precision laser straightening for scholarship test karts", 350000, 10000, 0.0, 0.0, 1, 5),
    ("eq_kart_engine_dyno", "driver_karting_scholarship", "125cc 2-Stroke Kart Engine Dyno", "Peak power and carburetion tuning for academy karts", 390000, 11500, 0.0, 0.0, 2, 5),
    ("eq_kart_talent_db", "driver_karting_scholarship", "Predictive AI Karting Talent Algorithm", "Early pattern recognition identifying generational prodigies", 580000, 17000, 0.0, 0.0, 3, 5),

    # 58. Single-Seater Junior Boot Camp (driver_f4_bootcamp)
    ("eq_f4_fleet_spec", "driver_f4_bootcamp", "Spec F4 Private Test Fleet", "Dedicated junior chassis and extensive spares cache", 850000, 25000, 0.0, 0.0, 1, 5),
    ("eq_f4_setup_rig", "driver_f4_bootcamp", "Junior Kinematics & Setup Pad", "Teaches academy drivers car balance and damper response", 480000, 14000, 0.0, 0.0, 1, 5),
    ("eq_f4_pit_intercom", "driver_f4_bootcamp", "Junior Trackside Race Intercom", "Direct live feedback between senior race engineers and rookies", 370000, 10500, 0.0, 0.0, 2, 5),
    ("eq_f4_video_debrief", "driver_f4_bootcamp", "360° Multi-Angle Cockpit Replay Suite", "Synchronous video and apex delta review with senior drivers", 520000, 15000, 0.0, 0.0, 3, 5),

    # Executive Boardroom (mgmt_boardroom) - Single-Node Factory Leadership Engine
    ("eq_mgmt_strategy_war_room", "mgmt_boardroom", "Strategic Operations War Room", "Cross-department executive alignment (+1.5 Factory Leadership per level)", 480000, 14000, 0.0, 0.0, 1, 5),
    ("eq_mgmt_exec_telemetry", "mgmt_boardroom", "Factory Leadership Operations Dashboard", "Unified factory telemetry and cross-divisional coordination (+1.0 Leadership & +1.0 Composure per level)", 380000, 11000, 0.0, 0.0, 1, 5),
    ("eq_mgmt_mentorship_suite", "mgmt_boardroom", "Executive Mentorship & Coaching Suite", "Accelerates weekly leadership stat growth (+0.05/wk per level for all factory personnel)", 440000, 12500, 0.0, 0.0, 2, 5),
    ("eq_mgmt_board_display", "mgmt_boardroom", "Holographic Strategy & Alignment Wall", "Global company alignment and leadership communication (+1.5 Leadership per level)", 520000, 15000, 0.0, 0.0, 3, 5),
]
