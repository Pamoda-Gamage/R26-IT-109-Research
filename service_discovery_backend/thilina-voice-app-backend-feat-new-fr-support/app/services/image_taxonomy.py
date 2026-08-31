"""
Image-recognition taxonomy — pure data, no ML imports.

Defines the label space the local (zero-shot CLIP) recogniser and the Gemini
fallback both speak:

  * object_type  — coarse domain of what the photo shows (single-label)
  * subtype      — the fine, routing-critical discriminator (single-label,
                   namespaced under an object_type). This is the field a future
                   provider-matching step keys on so a *lorry* job never routes
                   to a car-only mechanic — `service_type` alone (a flat
                   "mechanic" label) is deliberately insufficient for that.
  * condition    — what looks wrong (multi-label situation tags)
  * service_type — one of the existing 26 dispatch categories the text
                   classifier already knows (kept in sync via `validate()`).

Also holds the zero-shot PROMPT_BANK (natural-language prompts per label) and
Sinhala strings for the bilingual clarifying questions.
"""
from __future__ import annotations

# The closed service-type vocabulary the text classifier was trained on
# (app/training/dataset_with_index.csv). Duplicated here as plain data so this
# module stays import-light; image_recognition_service asserts it still matches
# predict_service.SERVICE_TYPE_LABELS at load time.
KNOWN_SERVICE_TYPES: tuple[str, ...] = (
    "air_condition_technician", "ambulance_service", "appliance_repair_service",
    "battery_jump_start_service", "car_care", "carpenter", "cctv_installer",
    "cleaning_service", "computer_repair_service", "electrician", "gardner",
    "hospital_service", "laptop_repair", "locksmith", "mason", "mechanic",
    "mobile_phone_repair", "movers", "network_operator", "nursing_assistance",
    "painter", "pest_controller", "plumber", "request_service",
    "solar_technician", "tv_repair", "water_pump_repair_service",
)

# ---------------------------------------------------------------------------
# object_type — coarse, single-label
# ---------------------------------------------------------------------------
OBJECT_TYPES: tuple[str, ...] = (
    "vehicle", "appliance", "electronic_device", "plumbing_fixture",
    "electrical_fixture", "structure_surface", "outdoor_area",
    "security_equipment", "person_medical", "other",
)

# ---------------------------------------------------------------------------
# subtype — single-label, namespaced by object_type
# ---------------------------------------------------------------------------
SUBTYPE_LABELS: dict[str, list[str]] = {
    "vehicle": [
        "car", "van", "suv_jeep", "pickup", "lorry_truck", "bus",
        "motorcycle", "scooter", "three_wheeler", "bicycle", "tractor",
        "heavy_equipment",
    ],
    "appliance": [
        "refrigerator", "washing_machine", "air_conditioner", "water_pump",
        "water_heater_geyser", "microwave", "oven_stove", "dishwasher",
        "ceiling_fan", "television",
    ],
    "electronic_device": [
        "laptop", "desktop_computer", "mobile_phone", "tablet", "monitor",
        "printer", "router_modem", "cctv_camera", "gaming_console",
    ],
    "plumbing_fixture": [
        "toilet", "sink_basin", "faucet_tap", "pipe", "water_tank",
        "drain_gully", "shower", "water_meter",
    ],
    "electrical_fixture": [
        "distribution_board", "wall_wiring", "socket_switch", "light_fixture",
        "solar_panel", "generator", "meter_box",
    ],
    "structure_surface": [
        "wall", "ceiling", "roof", "floor", "door", "window", "gate", "fence",
        "furniture", "staircase",
    ],
    "outdoor_area": [
        "garden_lawn", "tree", "driveway", "swimming_pool", "drain_canal",
    ],
    "security_equipment": [
        "cctv_system", "alarm_panel", "door_lock", "safe", "gate_motor",
    ],
    "person_medical": ["patient", "visible_injury", "elderly_person"],
    "other": ["other"],
}

# ---------------------------------------------------------------------------
# condition / situation — MULTI-label
# ---------------------------------------------------------------------------
CONDITION_TAGS: tuple[str, ...] = (
    "water_leak", "burst_pipe", "clog_blockage", "flooding_standing_water",
    "no_power_dead", "sparking_short_circuit", "overheating_or_smoke",
    "active_fire", "physical_break_broken", "crack", "collision_dent_damage",
    "rust_corrosion", "flat_or_damaged_tyre", "will_not_start",
    "abnormal_noise_or_vibration", "error_code_or_warning_light",
    "cracked_or_shattered_screen", "liquid_or_water_damage", "worn_out_aged",
    "loose_or_disconnected_part", "pest_infestation", "dirty_needs_cleaning",
    "gas_or_chemical_smell", "structural_sag_or_collapse", "no_visible_problem",
)

# ---------------------------------------------------------------------------
# subtype -> best-fit service_type (None when nothing on the 26-list fits)
# ---------------------------------------------------------------------------
SUBTYPE_TO_SERVICE_TYPE: dict[str, str | None] = {
    # vehicle — all collapse to the flat "mechanic" label; the subtype itself
    # is the routing discriminator, not this value.
    "car": "mechanic", "van": "mechanic", "suv_jeep": "mechanic",
    "pickup": "mechanic", "lorry_truck": "mechanic", "bus": "mechanic",
    "motorcycle": "mechanic", "scooter": "mechanic", "three_wheeler": "mechanic",
    "bicycle": "mechanic", "tractor": "mechanic", "heavy_equipment": "mechanic",
    # appliance
    "refrigerator": "appliance_repair_service",
    "washing_machine": "appliance_repair_service",
    "air_conditioner": "air_condition_technician",
    "water_pump": "water_pump_repair_service",
    "water_heater_geyser": "plumber",
    "microwave": "appliance_repair_service",
    "oven_stove": "appliance_repair_service",
    "dishwasher": "appliance_repair_service",
    "ceiling_fan": "electrician",
    "television": "tv_repair",
    # electronic_device
    "laptop": "laptop_repair",
    "desktop_computer": "computer_repair_service",
    "mobile_phone": "mobile_phone_repair",
    "tablet": "mobile_phone_repair",
    "monitor": "computer_repair_service",
    "printer": "computer_repair_service",
    "router_modem": "network_operator",
    "cctv_camera": "cctv_installer",
    "gaming_console": "computer_repair_service",
    # plumbing_fixture
    "toilet": "plumber", "sink_basin": "plumber", "faucet_tap": "plumber",
    "pipe": "plumber", "water_tank": "plumber", "drain_gully": "plumber",
    "shower": "plumber", "water_meter": "plumber",
    # electrical_fixture
    "distribution_board": "electrician", "wall_wiring": "electrician",
    "socket_switch": "electrician", "light_fixture": "electrician",
    "solar_panel": "solar_technician", "generator": "electrician",
    "meter_box": "electrician",
    # structure_surface
    "wall": "mason", "ceiling": "mason", "roof": "mason", "floor": "mason",
    "door": "carpenter", "window": "carpenter", "gate": "carpenter",
    "fence": "carpenter", "furniture": "carpenter", "staircase": "carpenter",
    # outdoor_area
    "garden_lawn": "gardner", "tree": "gardner", "driveway": "mason",
    "swimming_pool": "cleaning_service", "drain_canal": "cleaning_service",
    # security_equipment
    "cctv_system": "cctv_installer", "alarm_panel": "cctv_installer",
    "door_lock": "locksmith", "safe": "locksmith", "gate_motor": "electrician",
    # person_medical
    "patient": "ambulance_service", "visible_injury": "ambulance_service",
    "elderly_person": "nursing_assistance",
    # other
    "other": None,
}

# ---------------------------------------------------------------------------
# object_type -> the 26-vocab labels that are plausible for it. Used to mask
# and renormalise the zero-shot service_type head. "other" imposes no mask.
# ---------------------------------------------------------------------------
OBJECT_TYPE_TO_SERVICE_TYPES: dict[str, set[str]] = {
    "vehicle": {"mechanic", "car_care", "battery_jump_start_service", "movers"},
    "appliance": {
        "appliance_repair_service", "air_condition_technician",
        "water_pump_repair_service", "tv_repair", "electrician", "plumber",
    },
    "electronic_device": {
        "laptop_repair", "computer_repair_service", "mobile_phone_repair",
        "network_operator", "cctv_installer",
    },
    "plumbing_fixture": {"plumber", "water_pump_repair_service"},
    "electrical_fixture": {"electrician", "solar_technician"},
    "structure_surface": {"mason", "carpenter", "painter"},
    "outdoor_area": {"gardner", "mason", "cleaning_service", "pest_controller"},
    "security_equipment": {"cctv_installer", "locksmith", "electrician"},
    "person_medical": {"ambulance_service", "hospital_service", "nursing_assistance"},
    "other": set(KNOWN_SERVICE_TYPES),
}

# ---------------------------------------------------------------------------
# Zero-shot prompt bank — one list per label across every head. Fine-grained
# disambiguating phrasing is the load-bearing part; tune accuracy by editing
# text here.
# ---------------------------------------------------------------------------
PROMPT_BANK: dict[str, list[str]] = {
    # ---- object_type ----
    "vehicle": ["a photo of a vehicle", "a car, truck or motorbike",
                "a road vehicle"],
    "appliance": ["a photo of a home appliance",
                  "a household appliance like a fridge or washing machine",
                  "a large electrical appliance"],
    "electronic_device": ["a photo of an electronic device",
                          "a laptop, phone or computer", "a consumer gadget"],
    "plumbing_fixture": ["a photo of a plumbing fixture",
                         "a toilet, sink, tap or water pipe", "bathroom plumbing"],
    "electrical_fixture": ["a photo of an electrical fixture",
                           "a fuse board, wiring, switch or light fitting",
                           "house electrical installation"],
    "structure_surface": ["a photo of a building surface",
                          "a wall, ceiling, roof, floor or door",
                          "part of a building structure"],
    "outdoor_area": ["a photo of an outdoor area",
                     "a garden, lawn, tree or driveway", "an outdoor space"],
    "security_equipment": ["a photo of security equipment",
                           "a CCTV camera, alarm panel or door lock",
                           "a home security device"],
    "person_medical": ["a photo of a person needing medical help",
                       "an injured or sick person", "a patient or an injury"],
    "other": ["a photo of something else", "an unclear or unrelated photo",
              "none of the usual service categories"],

    # ---- subtype: vehicle ----
    "car": ["a photo of a car", "a passenger sedan or hatchback car",
            "a small private car"],
    "van": ["a photo of a van", "a passenger or delivery van",
            "a boxy minivan"],
    "suv_jeep": ["a photo of an SUV", "a jeep or four-wheel-drive",
                 "a tall off-road passenger vehicle"],
    "pickup": ["a photo of a pickup truck", "a double-cab pickup with an open tray",
               "a light utility truck"],
    "lorry_truck": ["a photo of a large lorry", "a heavy goods cargo truck",
                    "a truck with a big load bed or container"],
    "bus": ["a photo of a bus", "a passenger bus or coach",
            "a long vehicle with many windows"],
    "motorcycle": ["a photo of a motorcycle", "a geared motorbike with a large engine",
                   "a two-wheeler motorbike"],
    "scooter": ["a photo of a motor scooter", "a step-through scooter with small wheels",
                "a small automatic scooter"],
    "three_wheeler": ["a photo of a three-wheeler auto rickshaw",
                      "a tuk tuk three-wheel taxi",
                      "a small three-wheeled passenger vehicle"],
    "bicycle": ["a photo of a bicycle", "a pedal bicycle", "a push bike"],
    "tractor": ["a photo of a farm tractor", "an agricultural tractor",
                "a tractor with large rear wheels"],
    "heavy_equipment": ["a photo of heavy construction equipment",
                        "an excavator, bulldozer or backhoe loader",
                        "a large earth-moving machine"],

    # ---- subtype: appliance ----
    "refrigerator": ["a photo of a refrigerator", "a fridge or freezer"],
    "washing_machine": ["a photo of a washing machine", "a clothes washer"],
    "air_conditioner": ["a photo of an air conditioner", "an AC indoor or outdoor unit",
                        "a split-type air conditioning unit"],
    "water_pump": ["a photo of a water pump motor", "an electric water pump with pipes"],
    "water_heater_geyser": ["a photo of a water heater", "a geyser hot water tank"],
    "microwave": ["a photo of a microwave oven"],
    "oven_stove": ["a photo of a stove or cooker", "a gas hob or oven"],
    "dishwasher": ["a photo of a dishwasher"],
    "ceiling_fan": ["a photo of a ceiling fan", "an electric fan mounted on the ceiling"],
    "television": ["a photo of a television", "a flat-screen TV"],

    # ---- subtype: electronic_device ----
    "laptop": ["a photo of a laptop computer", "an open notebook laptop"],
    "desktop_computer": ["a photo of a desktop computer tower", "a PC and monitor"],
    "mobile_phone": ["a photo of a mobile phone", "a smartphone"],
    "tablet": ["a photo of a tablet", "an iPad-style tablet"],
    "monitor": ["a photo of a computer monitor", "a standalone display screen"],
    "printer": ["a photo of a printer", "an inkjet or laser printer"],
    "router_modem": ["a photo of a wifi router", "a broadband modem with antennas"],
    "cctv_camera": ["a photo of a single CCTV camera", "a surveillance camera"],
    "gaming_console": ["a photo of a game console", "a PlayStation or Xbox console"],

    # ---- subtype: plumbing_fixture ----
    "toilet": ["a photo of a toilet", "a WC pan and cistern"],
    "sink_basin": ["a photo of a sink", "a wash basin"],
    "faucet_tap": ["a photo of a tap", "a faucet or mixer tap"],
    "pipe": ["a photo of a water pipe", "plumbing pipework"],
    "water_tank": ["a photo of a water storage tank", "an overhead water tank"],
    "drain_gully": ["a photo of a floor drain", "a gully or drain outlet"],
    "shower": ["a photo of a shower", "a shower head and valve"],
    "water_meter": ["a photo of a water meter"],

    # ---- subtype: electrical_fixture ----
    "distribution_board": ["a photo of an electrical distribution board",
                           "a consumer unit with circuit breakers"],
    "wall_wiring": ["a photo of exposed electrical wiring", "wall cabling and conduits"],
    "socket_switch": ["a photo of a wall socket or switch", "a power outlet plate"],
    "light_fixture": ["a photo of a light fitting", "a ceiling or wall lamp"],
    "solar_panel": ["a photo of a solar panel", "rooftop photovoltaic panels"],
    "generator": ["a photo of a backup generator", "a portable power generator"],
    "meter_box": ["a photo of an electricity meter box", "a utility meter panel"],

    # ---- subtype: structure_surface ----
    "wall": ["a photo of a wall", "a plastered building wall"],
    "ceiling": ["a photo of a ceiling"],
    "roof": ["a photo of a roof", "roof tiles or sheeting"],
    "floor": ["a photo of a floor surface", "floor tiles"],
    "door": ["a photo of a door"],
    "window": ["a photo of a window"],
    "gate": ["a photo of a gate", "a metal entrance gate"],
    "fence": ["a photo of a fence", "a boundary fence"],
    "furniture": ["a photo of a piece of furniture", "a wooden cabinet, table or chair"],
    "staircase": ["a photo of a staircase", "indoor stairs and railing"],

    # ---- subtype: outdoor_area ----
    "garden_lawn": ["a photo of a garden lawn", "an overgrown grass lawn"],
    "tree": ["a photo of a tree", "a large tree or fallen branch"],
    "driveway": ["a photo of a driveway", "a paved vehicle driveway"],
    "swimming_pool": ["a photo of a swimming pool"],
    "drain_canal": ["a photo of an outdoor drain or canal", "a blocked storm drain"],

    # ---- subtype: security_equipment ----
    "cctv_system": ["a photo of a CCTV system with DVR and multiple cameras",
                    "a surveillance camera setup"],
    "alarm_panel": ["a photo of a burglar alarm panel", "a security alarm keypad"],
    "door_lock": ["a photo of a door lock", "a deadbolt or mortice lock"],
    "safe": ["a photo of a safe", "a security strongbox"],
    "gate_motor": ["a photo of an automatic gate motor", "a sliding gate operator"],

    # ---- subtype: person_medical ----
    "patient": ["a photo of a sick person lying down", "a person who has collapsed"],
    "visible_injury": ["a photo of a visible injury", "a bleeding wound or fracture"],
    "elderly_person": ["a photo of an elderly person needing assistance"],

    # ---- condition tags ----
    "water_leak": ["water leaking from something", "a dripping leak and wet patch"],
    "burst_pipe": ["a burst pipe spraying water", "a broken pipe with gushing water"],
    "clog_blockage": ["a clogged drain or blocked pipe", "standing dirty water from a blockage"],
    "flooding_standing_water": ["a flooded floor", "standing water covering the ground"],
    "no_power_dead": ["a device that is completely dead with no power",
                      "an appliance that will not switch on"],
    "sparking_short_circuit": ["electrical sparking", "a burnt scorched socket or wire",
                               "a short circuit with burn marks"],
    "overheating_or_smoke": ["something overheating and smoking", "smoke rising from a machine"],
    "active_fire": ["an active fire with flames", "something on fire"],
    "physical_break_broken": ["a broken snapped part", "something physically broken in pieces"],
    "crack": ["a crack in a surface", "a cracked wall or panel"],
    "collision_dent_damage": ["collision damage on a vehicle", "a dented crumpled panel"],
    "rust_corrosion": ["heavy rust and corrosion", "a badly corroded metal part"],
    "flat_or_damaged_tyre": ["a flat tyre", "a punctured or shredded tyre"],
    "will_not_start": ["a vehicle or engine that will not start"],
    "abnormal_noise_or_vibration": ["a machine that looks like it is shaking or vibrating badly"],
    "error_code_or_warning_light": ["a warning light or error code on a display",
                                    "a dashboard warning light lit up"],
    "cracked_or_shattered_screen": ["a cracked phone or laptop screen", "a shattered glass screen"],
    "liquid_or_water_damage": ["water damage on electronics", "a liquid spill on a device"],
    "worn_out_aged": ["a worn out, aged, degraded part", "something old and deteriorated"],
    "loose_or_disconnected_part": ["a loose or disconnected part hanging off",
                                   "a detached component"],
    "pest_infestation": ["a pest infestation", "termites, cockroaches or rodents and their damage"],
    "dirty_needs_cleaning": ["a very dirty surface that needs cleaning", "heavy grime and dirt"],
    "gas_or_chemical_smell": ["an LPG gas cylinder and its regulator",
                              "a corroded gas pipe or valve"],
    "structural_sag_or_collapse": ["a sagging or partially collapsed structure",
                                   "a caved-in ceiling or roof"],
    "no_visible_problem": ["an object in normal working condition",
                           "nothing obviously wrong in the photo"],

    # ---- service_type (26 + request_service), phrased for a photo ----
    "air_condition_technician": ["an air conditioner that needs a technician",
                                 "a faulty AC unit"],
    "ambulance_service": ["a medical emergency needing an ambulance",
                          "an injured person needing urgent transport"],
    "appliance_repair_service": ["a home appliance that needs repair",
                                 "a broken fridge, washing machine or microwave"],
    "battery_jump_start_service": ["a car with a dead battery needing a jump start",
                                   "jumper cables on a car battery"],
    "car_care": ["a car needing washing, detailing or routine care",
                 "car cleaning and maintenance"],
    "carpenter": ["woodwork that needs a carpenter", "a broken door, window or furniture"],
    "cctv_installer": ["CCTV cameras that need installation or repair",
                       "a surveillance camera setup"],
    "cleaning_service": ["a space that needs professional cleaning", "heavy dirt and mess"],
    "computer_repair_service": ["a desktop computer that needs repair"],
    "electrician": ["house wiring or electrical fittings that need an electrician",
                    "a fuse board, socket or light problem"],
    "gardner": ["a garden or lawn that needs a gardener", "overgrown plants and grass"],
    "hospital_service": ["a person who needs to get to a hospital"],
    "laptop_repair": ["a laptop that needs repair", "a damaged notebook computer"],
    "locksmith": ["a lock or key problem needing a locksmith", "a broken door lock"],
    "mason": ["brickwork, plaster or concrete that needs a mason",
              "a cracked wall or damaged floor"],
    "mechanic": ["a vehicle that needs a mechanic", "a broken-down car, van or motorbike"],
    "mobile_phone_repair": ["a mobile phone that needs repair", "a cracked smartphone"],
    "movers": ["furniture and boxes being moved", "a house move needing movers"],
    "network_operator": ["home internet equipment needing a network technician",
                         "a router or broadband fault"],
    "nursing_assistance": ["an elderly or sick person needing a nursing assistant at home"],
    "painter": ["a wall or surface that needs painting", "peeling or faded paint"],
    "pest_controller": ["a pest problem needing pest control", "insect or rodent infestation"],
    "plumber": ["a plumbing problem needing a plumber", "a leaking tap, pipe or toilet"],
    "request_service": ["a general service request", "a household job that needs a professional"],
    "solar_technician": ["a rooftop solar power system needing a technician",
                         "faulty solar panels"],
    "tv_repair": ["a television that needs repair", "a broken TV screen"],
    "water_pump_repair_service": ["a water pump that needs repair", "a faulty motor pump"],
}

# ---------------------------------------------------------------------------
# Sinhala strings for the bilingual clarifying questions. Anything missing
# falls back to the humanised English label (see the *_si helpers).
# ---------------------------------------------------------------------------
_OBJECT_TYPE_SI: dict[str, str] = {
    "vehicle": "වාහනයක්",
    "appliance": "ගෘහ උපකරණයක්",
    "electronic_device": "ඉලෙක්ට්‍රොනික උපකරණයක්",
    "plumbing_fixture": "ජල නල උපකරණයක්",
    "electrical_fixture": "විදුලි උපකරණයක්",
    "structure_surface": "ගොඩනැගිලි කොටසක්",
    "outdoor_area": "එළිමහන් ප්‍රදේශයක්",
    "security_equipment": "ආරක්ෂක උපකරණයක්",
    "person_medical": "රෝගී පුද්ගලයෙක්",
    "other": "වෙනත් දෙයක්",
}

_SUBTYPE_SI: dict[str, str] = {
    "car": "කාර් එකක්",
    "van": "වෑන් එකක්",
    "suv_jeep": "ජීප් රථයක්",
    "pickup": "පිකප් එකක්",
    "lorry_truck": "ලොරියක්",
    "bus": "බස් එකක්",
    "motorcycle": "මෝටර් සයිකලයක්",
    "scooter": "ස්කූටර් එකක්",
    "three_wheeler": "ත්‍රිරෝද රථයක්",
    "bicycle": "බයිසිකලයක්",
    "tractor": "ට්‍රැක්ටරයක්",
    "heavy_equipment": "බර යන්ත්‍රෝපකරණයක්",
    "refrigerator": "ශීතකරණයක්",
    "washing_machine": "රෙදි සෝදන යන්ත්‍රයක්",
    "air_conditioner": "වායු සමීකරණයක්",
    "water_pump": "ජල පොම්පයක්",
    "television": "රූපවාහිනියක්",
    "laptop": "ලැප්ටොප් එකක්",
    "desktop_computer": "පරිගණකයක්",
    "mobile_phone": "ජංගම දුරකථනයක්",
}

_CONDITION_SI: dict[str, str] = {
    "water_leak": "වතුර ලීක් වීම",
    "burst_pipe": "නළයක් පිපිරීම",
    "clog_blockage": "අවහිර වීම",
    "flooding_standing_water": "වතුර පිරී තිබීම",
    "no_power_dead": "විදුලිය නොමැති වීම",
    "sparking_short_circuit": "විදුලි ෂෝට් එකක්",
    "overheating_or_smoke": "අධික උණුසුම හෝ දුම",
    "active_fire": "ගින්නක්",
    "physical_break_broken": "කැඩීමක්",
    "crack": "පැළීමක්",
    "collision_dent_damage": "හැප්පීමේ හානි",
    "flat_or_damaged_tyre": "ටයරයක් පැත්තට වීම",
    "will_not_start": "ස්ටාට් නොවීම",
    "cracked_or_shattered_screen": "තිරය පැළී තිබීම",
    "pest_infestation": "පළිබෝධ උවදුරක්",
    "dirty_needs_cleaning": "පිරිසිදු කිරීම අවශ්‍යයි",
    "no_visible_problem": "පෙනෙන ගැටලුවක් නැත",
}

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
ALL_SUBTYPES: list[str] = [s for subs in SUBTYPE_LABELS.values() for s in subs]


def humanize(label: str | None) -> str:
    return (label or "").replace("_", " ")


def subtypes_for(object_type: str) -> list[str]:
    """Subtypes valid under `object_type`, always including 'other' as an
    escape hatch."""
    subs = list(SUBTYPE_LABELS.get(object_type, []))
    if "other" not in subs:
        subs.append("other")
    return subs


def service_type_for_subtype(subtype: str | None) -> str | None:
    if not subtype:
        return None
    return SUBTYPE_TO_SERVICE_TYPE.get(subtype)


def allowed_service_types(object_type: str) -> set[str]:
    return OBJECT_TYPE_TO_SERVICE_TYPES.get(object_type, set(KNOWN_SERVICE_TYPES))


def object_type_si(label: str) -> str:
    return _OBJECT_TYPE_SI.get(label, humanize(label))


def subtype_si(label: str) -> str:
    return _SUBTYPE_SI.get(label, humanize(label))


def condition_si(label: str) -> str:
    return _CONDITION_SI.get(label, humanize(label))


def validate() -> None:
    """Fail fast on an inconsistent taxonomy. Called at image_recognition_service
    import and exercised directly by tests/CI."""
    known = set(KNOWN_SERVICE_TYPES)

    # object_type coverage
    assert set(SUBTYPE_LABELS) == set(OBJECT_TYPES), (
        set(SUBTYPE_LABELS) ^ set(OBJECT_TYPES)
    )
    assert set(OBJECT_TYPE_TO_SERVICE_TYPES) == set(OBJECT_TYPES)

    # subtypes are globally unique (no namespace collisions) so a flat encoder
    # and the reverse maps stay unambiguous.
    seen: set[str] = set()
    for subs in SUBTYPE_LABELS.values():
        for s in subs:
            assert s not in seen or s == "other", f"duplicate subtype {s!r}"
            seen.add(s)

    # every subtype maps to a real service_type or None
    for subs in SUBTYPE_LABELS.values():
        for s in subs:
            assert s in SUBTYPE_TO_SERVICE_TYPE, f"unmapped subtype {s!r}"
            v = SUBTYPE_TO_SERVICE_TYPE[s]
            assert v is None or v in known, f"{s!r} -> bad service_type {v!r}"

    # object_type service masks reference real labels
    for ot, allowed in OBJECT_TYPE_TO_SERVICE_TYPES.items():
        bad = allowed - known
        assert not bad, f"{ot!r} allows unknown service_types {bad}"

    # every label used by any head has at least one prompt
    labels_needing_prompts = (
        set(OBJECT_TYPES)
        | seen
        | set(CONDITION_TAGS)
        | known
    )
    missing = labels_needing_prompts - set(PROMPT_BANK)
    assert not missing, f"PROMPT_BANK missing entries for {sorted(missing)}"
    for label, prompts in PROMPT_BANK.items():
        assert prompts, f"PROMPT_BANK[{label!r}] is empty"


if __name__ == "__main__":
    validate()
    print("image_taxonomy OK:",
          len(OBJECT_TYPES), "object types,",
          len(ALL_SUBTYPES), "subtypes,",
          len(CONDITION_TAGS), "condition tags,",
          len(PROMPT_BANK), "prompt-bank entries")
