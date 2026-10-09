from __future__ import annotations

import threading
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

from amr_helper import config as app_config
from amr_helper.imagery import ensure_lz_images, missing_lz_images, route_images
from amr_helper.kmz_lzs import load_landing_zones
from amr_helper.manifest import page_values as manifest_pages
from amr_helper.models import Mission, Person
from amr_helper.overview_map import build_overview
from amr_helper.paths import lz_images_dir
from amr_helper.pdf_fields import build_field_values
from amr_helper.pdf_fill import fill_pdf
from amr_helper.personnel import load_roster, people_by_key
from amr_helper.timeline import default_timeline
from amr_helper.ui.download_dialog import LzDownloadDialog
from amr_helper.ui.legs_tab import LegsTab
from amr_helper.ui.manifest_tab import ManifestTab
from amr_helper.ui.mission_tab import MissionTab
from amr_helper.ui.review_tab import ReviewTab
from amr_helper.ui.setup_sources import choose_csv, choose_kmz, prompt_for_sources
from amr_helper.ui.timeline_tab import TimelineTab
from amr_helper.validate import validate_mission


def main() -> None:
    app = AmrApp()
    app.after(50, app.bootstrap)
    app.mainloop()


class AmrApp(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title("AMR Form Helper")
        self.geometry("920x740")
        self.withdraw()
        self.zones = []
        self.roster: list[Person] = []
        self.extras: list[Person] = []
        self._ui_ready = False

    def bootstrap(self) -> None:
        if not prompt_for_sources(self):
            self.destroy()
            return
        try:
            self._load_sources()
        except Exception as exc:
            messagebox.showerror("Startup failed", str(exc), parent=self)
            self.destroy()
            return
        self._download_lz_images_if_needed()
        self._build()
        self._ui_ready = True
        self._refresh_source_labels()
        self.deiconify()
        self.lift()

    def _load_sources(self) -> None:
        csv_file = app_config.get_csv_path()
        kmz_file = app_config.get_kmz_path()
        if csv_file is None or kmz_file is None:
            raise RuntimeError("CSV and KMZ paths must be configured")
        self.roster = load_roster(csv_file)
        self.zones = load_landing_zones(kmz_file)
        if not self.roster:
            raise RuntimeError(f"No personnel found in {csv_file}")
        if not self.zones:
            raise RuntimeError(f"No landing zones found in {kmz_file}")

    def _download_lz_images_if_needed(self) -> None:
        missing = missing_lz_images(self.zones)
        if not missing:
            return
        dialog = LzDownloadDialog(self, len(missing))
        error: list[BaseException] = []

        def work() -> None:
            try:
                ensure_lz_images(
                    self.zones,
                    on_progress=lambda done, total, name: self.after(
                        0, dialog.set_progress, done, total, name
                    ),
                )
            except BaseException as exc:  # noqa: BLE001
                error.append(exc)
            finally:
                self.after(0, dialog.destroy)

        threading.Thread(target=work, daemon=True).start()
        self.wait_window(dialog)
        if error:
            messagebox.showwarning(
                "LZ images",
                f"Some LZ images could not be downloaded:\n{error[0]}",
                parent=self,
            )

    def _build(self) -> None:
        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=8, pady=8)
        lz_names = [zone.name for zone in self.zones]
        lz_mgrs = {zone.name: zone.mgrs for zone in self.zones}
        self.mission_tab = MissionTab(
            self.notebook,
            Mission(),
            on_choose_csv=self._reselect_csv,
            on_choose_kmz=self._reselect_kmz,
        )
        self.legs_tab = LegsTab(self.notebook, lz_names)
        self.timeline_tab = TimelineTab(
            self.notebook, lz_mgrs, get_context=self._timeline_context
        )
        self.manifest_tab = ManifestTab(self.notebook, self.roster, self.extras)
        self.legs_tab.on_change = lambda: self.manifest_tab.sync_leg_count(
            len(self.legs_tab.rows)
        )
        self.review_tab = ReviewTab(self.notebook)
        self.notebook.add(self.mission_tab, text="Mission")
        self.notebook.add(self.legs_tab, text="Legs")
        self.notebook.add(self.timeline_tab, text="Timeline")
        self.notebook.add(self.manifest_tab, text="Manifest")
        self.notebook.add(self.review_tab, text="Review")
        self.notebook.bind("<<NotebookTabChanged>>", self._on_tab)
        ttk.Button(self, text="Save filled PDF", command=self.save_pdf).pack(pady=(0, 8))

    def _refresh_source_labels(self) -> None:
        if not self._ui_ready:
            return
        self.mission_tab.set_source_paths(
            app_config.get_csv_path(), app_config.get_kmz_path()
        )

    def _reselect_csv(self) -> None:
        path = choose_csv(self)
        if path is None:
            return
        try:
            self.roster = load_roster(path)
            self.extras = []
            self.manifest_tab.extras = self.extras
            self.manifest_tab.set_roster(self.roster)
            self._refresh_source_labels()
        except Exception as exc:
            messagebox.showerror("Roster CSV", str(exc), parent=self)

    def _reselect_kmz(self) -> None:
        path = choose_kmz(self)
        if path is None:
            return
        try:
            self.zones = load_landing_zones(path)
            names = [zone.name for zone in self.zones]
            mgrs = {zone.name: zone.mgrs for zone in self.zones}
            self.legs_tab.set_lz_names(names)
            self.timeline_tab.set_lz_mgrs(mgrs)
            self._refresh_source_labels()
            self._download_lz_images_if_needed()
        except Exception as exc:
            messagebox.showerror("LZ KMZ", str(exc), parent=self)

    def _on_tab(self, _event: tk.Event | None = None) -> None:
        self.manifest_tab.sync_leg_count(len(self.legs_tab.rows))
        title = self.notebook.tab(self.notebook.select(), "text")
        if title == "Timeline":
            self.timeline_tab.sync_from_legs()
        if title == "Review":
            self.review_tab.show(self.collect_mission(), self.zones)

    def _timeline_context(self) -> Mission:
        mission = self.mission_tab.collect()
        mission.legs = self.legs_tab.collect_legs()
        return mission

    def collect_mission(self) -> Mission:
        self.manifest_tab.sync_leg_count(len(self.legs_tab.rows))
        mission = self.mission_tab.collect()
        mission.legs = self.legs_tab.collect_legs()
        self.manifest_tab.apply_to_legs(mission.legs)
        mission.extra_people = list(self.extras)
        lz_mgrs = {zone.name: zone.mgrs for zone in self.zones}
        if self.timeline_tab.dirty:
            mission.timeline = self.timeline_tab.collect()
        else:
            mission.timeline = default_timeline(mission, lz_mgrs)
        return mission

    def save_pdf(self) -> None:
        mission = self.collect_mission()
        known = {zone.name for zone in self.zones}
        errors = validate_mission(mission, known)
        if errors and not self._confirm_save_anyway(errors):
            return
        dest = filedialog.asksaveasfilename(
            parent=self,
            defaultextension=".pdf",
            filetypes=[("PDF", "*.pdf")],
            initialfile="AMR_filled.pdf",
        )
        if not dest:
            return
        self._write_pdf(mission, Path(dest))

    def _confirm_save_anyway(self, errors: list[str]) -> bool:
        detail = "\n".join(f"• {err}" for err in errors)
        return messagebox.askyesno(
            "Validation errors",
            f"Issues found:\n\n{detail}\n\nSave anyway?",
            parent=self,
        )

    def _write_pdf(self, mission: Mission, dest: Path) -> None:
        self.configure(cursor="watch")
        self.update_idletasks()
        try:
            saved = ensure_lz_images(self.zones, lz_images_dir())
            photos = route_images(mission.unique_lz_names(), saved)
            overview = _try_overview(self.zones, mission.legs)
            lz_mgrs = {zone.name: zone.mgrs for zone in self.zones}
            people = people_by_key(self.roster, mission.extra_people)
            values = build_field_values(mission, lz_mgrs, people)
            extra = manifest_pages(mission, people)[1:]
            fill_pdf(
                values,
                dest,
                lz_images=photos,
                overview=overview,
                extra_manifest=extra,
            )
        finally:
            self.configure(cursor="")
        messagebox.showinfo("Saved", f"Wrote {dest}", parent=self)


def _try_overview(zones, legs):
    try:
        return build_overview(zones, legs, lz_images_dir())
    except Exception as exc:
        print(f"overview skipped: {exc}")
        return None
