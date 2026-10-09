# AMR Helper notes

JTF-SB AMR Form Version 4.0 JUL26. Template is a 4-page AcroForm with 768 fields.

## Shared / misnamed widgets

- Cover "Requesting Unit" is field `Supported Unit` (also page 2 Supported Unit and CONOP header).
- Cover "Requestors Email" is field `Supported Unit POC Email`.
- Cover date box is `MSN Dates`, not `Mission Date`.
- CONOP "Mission Description" is `Special-Instructions1`.
- CONOP requestor name/email reuse `Supported Unit POC` / `Supported Unit POC Email`.
- CONOP BDE BAE POC/email reuse `Supported Unit Reviewer` / `Unit Reviewer Email`.
- `UH_2` is both CONOP UH-60 assigned and the tiny page-2 "# of Aircraft Allocated" UH box. Write `1X`.

## Exact dropdown / button values

- Mission priority: `3 - Infill/Exfill Resupply` (spelling is Infill/Exfill).
- Named JTF-SB operation radio `Group1`: on-states `/Yes` and `/No`. Set `No`.
- Section 3 Yes/No checkboxes are independent. Each `No`/`No2`–`No6` on-state is `/Yes`. Turn those on and turn `Yes`–`Yes6` off.
- `waiver1`–`waiver5` and `Special1`–`Special8` already default to `No`.

## Tables

- Aviation HLZs: `Dep TimeN`, `FROMN`, `TON`, `Arr TimeN` for N=1..10. Dep/Arr times come from matching DEPART/ARRIVE timeline events, not the Legs tab.
- CONOP timeline: 12 rows (`Date N`, `Time(MPT)N`, `EventRowN`, `LocationRowN`). Editable on the Timeline tab; defaults to DEPART/ARRIVE per leg. Up/Down reorder; per-row Delete; Auto fills time from the previous event using straight-line distance at 200 kph (ceil to 5 min, min 15). Location entry is 18 characters wide.
- Times are entered in local Arizona MST (`America/Phoenix`, UTC-7, no DST) and written as `HHMML/HHMMZ` (e.g. `1400L/2100Z`).
- CONOP HLZs: 5 rows (`HLZ NameRowN`, `GridsRowN`, `MarkingRowN`).
- Manifest: 30 rows per page. `NRowK` is the X-column for leg N on row K. One row per person per leg.
- Empty legs write one row with Last Name `NO TROOPS`, PickUp/DropOff from that leg’s LZs, and an `X` in that leg’s column.
- More than 30 manifest rows appends a baked (non-form) blank manifest page with the same header text and only the leftover rows. Baking prevents AcroForm field merge from overwriting page 1.
- `NTotal Pax Count Per Leg` for N=1..10.

## Source files

- LZs: `chosen-plt-map.kmz` → `doc.kml` folder `NOGALES LZs`, 39 point placemarks named `LZ …`.
- Extra LZs (not in the KMZ) are listed in `defaults.EXTRA_LANDING_ZONES`. Includes `LZ BAKER` at `12R WV 03141 68742`.
- `ARF` is a virtual LZ (no grid). Legs to/from ARF are omitted from the CONOP map. ARF is omitted from the three micro pictures.
- LZ satellite chips: cached under `%LOCALAPPDATA%\AMR Helper\lz_images\` (250 m ESRI World Imagery, captioned). Dev/verify may still use the repo `lz_images/` folder.
- Page 3 Additional Information image buttons `Image13_af_image`, `Image14_af_image`, `Image15_af_image` get the first three unique route LZs (left to right), skipping ARF.
- Large CONOP map is `Image2_af_image` (PDF page 3, landscape). Extent is the LZs used on non-ARF legs plus a 20% buffer (then fit to the slot aspect). Only those LZs are labeled, with leader lines and Axis of Advance — Aviation symbols per depicted route (crossed stem + open triangle head), black with a white halo. Duplicate start→end legs share one arrow labeled `Leg 1,2,…`. Satellite bases are cached as `lz_images/overview_base_*.jpg`; the labeled overlay is `lz_images/overview.jpg`.
- Save validates the mission; if checks fail, the user can confirm and save anyway.
- Roster: CSV columns Rank, Last, DODID (L4), Squad. On first launch the user picks the roster CSV and LZ KMZ (paths stored in `%LOCALAPPDATA%\AMR Helper\config.json`). Re-select from Mission → Data sources.
- LZ chips download on first start (progress + ETA dialog); cache lives in `%LOCALAPPDATA%\AMR Helper\lz_images\`. Distribute with `Build\build.bat` → `dist\AMR-Form-Helper-Portable.zip` (users run `AMR Form Helper.bat`). Optional signed EXE: `Build\build_exe.bat` + `Build\sign.bat`.
- Browser build: `web/` is static. Roster CSV, KMZ, and the filled PDF stay in the user’s browser. Host with Cloudflare Pages, GitHub Pages, or an internal file share (`web/README.md`).
- Dates written as `DD MMM YY`. Times written as `HHMML/HHMMZ` from local Arizona time.
- Grids: 10-digit MGRS with spaces, e.g. `12S WD 12345 67890`.
