REQUESTING_UNIT = "Baker/1-506IN/1MBDE"
REQUESTOR_EMAIL = "nathaniel.greene37.mil@army.mil"
SUPPORTED_UNIT_POC = "1LT Greene"
SUPPORTED_UNIT_POC_PHONE = "617-775-2674"
SUPPORTED_UNIT_REVIEWER = "1LT Deona Roberts"
UNIT_REVIEWER_EMAIL = "deona.l.roberts.mil@army.mil"

MISSION_PRIORITY = "3 - Infill/Exfill Resupply"
WEIGHT_PER_PERSON = "220"
AIRCRAFT_ASSIGNED = "1X"

TASK_1 = "CONDUCT AREA SECURITY"
PURPOSE_1 = "IOT DENY EN FOM"

MISSION_STATEMENT = (
    "In support of CBP, TF Baker conducts area security operations to control "
    "the U.S. Southern Border in AO Nogales in order to protect the territorial "
    "integrity of the United States"
)

TRAINING_INTENT = (
    "B CO successfully conducts air movement in order to deter IA and scout "
    "movement throughout Zone 19"
)

NATIONALITY = "US"
SERVICE = "ARMY"
MAX_LEGS = 10
MAX_MANIFEST_ROWS = 30
MAX_HLZ_ROWS = 5
MAX_TIMELINE_ROWS = 12
NO_TROOPS_LABEL = "NO TROOPS"
ARF_LZ_NAME = "ARF"

# Extra LZs not in the KMZ. MGRS is stored as given (10-digit, spaced).
EXTRA_LANDING_ZONES = (
    ("LZ BAKER", "12R WV 03141 68742"),
)


def is_arf_lz(name: str) -> bool:
    return (name or "").strip().upper() == ARF_LZ_NAME


def touches_arf(start_lz: str, end_lz: str) -> bool:
    return is_arf_lz(start_lz) or is_arf_lz(end_lz)

# Nogales / Arizona local time (MST, no DST).
LOCAL_TIMEZONE = "America/Phoenix"
LOCAL_UTC_OFFSET_HOURS = -7
