export const REQUESTING_UNIT = "Baker/1-506IN/1MBDE";
export const REQUESTOR_EMAIL = "nathaniel.greene37.mil@army.mil";
export const SUPPORTED_UNIT_POC = "1LT Greene";
export const SUPPORTED_UNIT_POC_PHONE = "617-775-2674";
export const SUPPORTED_UNIT_REVIEWER = "1LT Deona Roberts";
export const UNIT_REVIEWER_EMAIL = "deona.l.roberts.mil@army.mil";

export const MISSION_PRIORITY = "3 - Infill/Exfill Resupply";
export const WEIGHT_PER_PERSON = "220";
export const AIRCRAFT_ASSIGNED = "1X";
export const TASK_1 = "CONDUCT AREA SECURITY";
export const PURPOSE_1 = "IOT DENY EN FOM";

export const MISSION_STATEMENT =
  "In support of CBP, TF Baker conducts area security operations to control " +
  "the U.S. Southern Border in AO Nogales in order to protect the territorial " +
  "integrity of the United States";

export const TRAINING_INTENT =
  "B CO successfully conducts air movement in order to deter IA and scout " +
  "movement throughout Zone 19";

export const NATIONALITY = "US";
export const SERVICE = "ARMY";
export const MAX_LEGS = 10;
export const MAX_MANIFEST_ROWS = 30;
export const MAX_HLZ_ROWS = 5;
export const MAX_TIMELINE_ROWS = 12;
export const NO_TROOPS_LABEL = "NO TROOPS";
export const ARF_LZ_NAME = "ARF";
export const EXTRA_LANDING_ZONES = [["LZ BAKER", "12R WV 03141 68742"]];
export const LOCAL_UTC_OFFSET_HOURS = -7;
export const SQUAD_ORDER = ["HQ", "1st", "2nd", "3rd"];
export const TEMPLATE_URL = "assets/template.pdf";
export const MANIFEST_PAGE = 3;

export function isArfLz(name) {
  return (name || "").trim().toUpperCase() === ARF_LZ_NAME;
}

export function touchesArf(startLz, endLz) {
  return isArfLz(startLz) || isArfLz(endLz);
}
