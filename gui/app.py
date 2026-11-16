"""Tkinter GUI for Subtitle Merger."""

from __future__ import annotations

import sys
import threading
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

# Allow running as `python gui/app.py` as well as a package import.
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from subtitle_merger.merger import DEFAULT_THRESHOLD, merge_cues
from subtitle_merger.srt_parser import parse_srt_file
from subtitle_merger.srt_writer import format_srt, write_srt_file

APP_TITLE = "Subtitle Merger — دمج الترجمات ثنائية اللغة"


class MergeApp(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title(APP_TITLE)
        self.geometry("760x640")
        self.minsize(680, 560)

        self.primary_cues: list[Cue] | None = None
        self.secondary_cues: list[Cue] | None = None
        self.primary_path: str | None = None
        self.secondary_path: str | None = None

        self._build_ui()

    # ------------------------------------------------------------------ UI --
    def _build_ui(self) -> None:
        pad = {"padx": 12, "pady": 6}

        top = ttk.LabelFrame(self, text=" 1. Select subtitle files ")
        top.pack(fill="x", **pad)

        ttk.Label(top, text="Primary (base timing):").grid(row=0, column=0, sticky="w", padx=8, pady=4)
        self.primary_var = tk.StringVar(value="")
        ttk.Button(top, text="Choose…", command=self._pick_primary).grid(row=0, column=1, padx=6, pady=4)
        ttk.Label(top, textvariable=self.primary_var, foreground="#0a58ca").grid(row=0, column=2, sticky="w")

        ttk.Label(top, text="Secondary:").grid(row=1, column=0, sticky="w", padx=8, pady=4)
        self.secondary_var = tk.StringVar(value="")
        ttk.Button(top, text="Choose…", command=self._pick_secondary).grid(row=1, column=1, padx=6, pady=4)
        ttk.Label(top, textvariable=self.secondary_var, foreground="#0a58ca").grid(row=1, column=2, sticky="w")

        top.columnconfigure(2, weight=1)

        opts = ttk.LabelFrame(self, text=" 2. Options ")
        opts.pack(fill="x", **pad)

        ttk.Label(opts, text="Language order in output:").grid(row=0, column=0, sticky="w", padx=8, pady=4)
        self.order_var = tk.StringVar(value="Primary on top")
        ttk.Combobox(
            opts, textvariable=self.order_var, state="readonly", width=22,
            values=["Primary on top", "Secondary on top"],
        ).grid(row=0, column=1, sticky="w")

        ttk.Label(opts, text="Match threshold (%):").grid(row=1, column=0, sticky="w", padx=8, pady=4)
        self.threshold_var = tk.StringVar(value=str(int(DEFAULT_THRESHOLD * 100)))
        ttk.Spinbox(
            opts, textvariable=self.threshold_var, from_=0, to=100, width=6,
        ).grid(row=1, column=1, sticky="w")

        self.merge_btn = ttk.Button(opts, text="Merge & Save…", command=self._on_merge)
        self.merge_btn.grid(row=0, column=2, rowspan=2, padx=16, pady=6)
        self.merge_btn.state(["disabled"])

        opts.columnconfigure(2, weight=1)

        prev = ttk.LabelFrame(self, text=" 3. Preview (first 10 merged cues) ")
        prev.pack(fill="both", expand=True, **pad)

        self.preview = tk.Text(prev, height=14, wrap="none", state="disabled")
        scroll_y = ttk.Scrollbar(prev, orient="vertical", command=self.preview.yview)
        scroll_x = ttk.Scrollbar(prev, orient="horizontal", command=self.preview.xview)
        self.preview.configure(yscrollcommand=scroll_y.set, xscrollcommand=scroll_x.set)
        scroll_y.pack(side="right", fill="y")
        scroll_x.pack(side="bottom", fill="x")
        self.preview.pack(fill="both", expand=True, padx=4, pady=4)

        self.status = tk.StringVar(value="Load both files to begin.")
        ttk.Label(self, textvariable=self.status, relief="sunken", anchor="w", padding=(8, 3)).pack(
            fill="x", padx=12, pady=(0, 8)
        )

    # ------------------------------------------------------------- actions --
    def _pick_primary(self) -> None:
        self._pick_file("primary", self.primary_var)

    def _pick_secondary(self) -> None:
        self._pick_file("secondary", self.secondary_var)

    def _pick_file(self, slot: str, var: tk.StringVar) -> None:
        path = filedialog.askopenfilename(
            title="Choose an SRT file",
            filetypes=[("SubRip subtitles", "*.srt"), ("All files", "*.*")],
        )
        if not path:
            return
        try:
            cues = parse_srt_file(path)
        except (ValueError, OSError) as exc:
            messagebox.showerror("Cannot read file", str(exc))
            return
        if slot == "primary":
            self.primary_path, self.primary_cues = path, cues
        else:
            self.secondary_path, self.secondary_cues = path, cues
        var.set(f"{Path(path).name}  ({len(cues)} cues)")
        self._refresh_state()

    def _refresh_state(self) -> None:
        ready = self.primary_cues is not None and self.secondary_cues is not None
        if ready:
            self.merge_btn.state(["!disabled"])
            self.status.set(
                f"Ready: {len(self.primary_cues)} primary cues + "
                f"{len(self.secondary_cues)} secondary cues."
            )
        else:
            self.merge_btn.state(["disabled"])
            self.status.set("Load both files to begin.")

    def _on_merge(self) -> None:
        try:
            threshold = int(self.threshold_var.get()) / 100.0
            if not 0.0 <= threshold <= 1.0:
                raise ValueError
        except ValueError:
            messagebox.showerror("Invalid option", "Threshold must be a number between 0 and 100.")
            return

        # Run the merge in a background thread so the UI stays responsive.
        self.merge_btn.state(["disabled"])
        self.status.set("Merging…")
        threading.Thread(target=self._merge_worker, args=(threshold,), daemon=True).start()

    def _merge_worker(self, threshold: float) -> None:
        try:
            # merge_cues never mutates its inputs, so no copies are needed.
            primary = self.primary_cues or []
            secondary = self.secondary_cues or []
            if self.order_var.get() == "Secondary on top":
                primary, secondary = secondary, primary
            result = merge_cues(primary, secondary, threshold=threshold)

            # Continue on the UI thread: preview, ask where to save, write.
            self.after(0, lambda: self._finish_merge(result))
        except Exception as exc:  # noqa: BLE001 — surface any error to the user
            message = str(exc)
            self.after(0, lambda: messagebox.showerror("Merge failed", message))
            self.after(0, lambda: self.status.set("Merge failed."))
            self.after(0, lambda: self.merge_btn.state(["!disabled"]))

    def _finish_merge(self, result) -> None:
        try:
            self._show_preview(format_srt(result.cues[:10]))
            out_path = self._ask_save_path()
            if not out_path:
                self.status.set("Merge done — save cancelled.")
                return
            write_srt_file(result.cues, out_path)
            summary = (
                f"Matched pairs: {result.matched}\n"
                f"Contained: {result.contained}\n"
                f"Primary-only: {result.primary_only}\n"
                f"Secondary-only: {result.secondary_only}"
            )
            self.status.set(
                f"Saved {len(result.cues)} cues → {out_path}   ({summary.replace(chr(10), ' | ')})"
            )
            messagebox.showinfo(
                "Done", f"Saved {len(result.cues)} merged cues to:\n{out_path}\n\n{summary}"
            )
        except Exception as exc:  # noqa: BLE001
            messagebox.showerror("Save failed", str(exc))
            self.status.set("Save failed.")
        finally:
            self.merge_btn.state(["!disabled"])

    def _show_preview(self, text: str) -> None:
        self.preview.configure(state="normal")
        self.preview.delete("1.0", "end")
        self.preview.insert("1.0", text)
        self.preview.configure(state="disabled")

    def _ask_save_path(self) -> str | None:
        return filedialog.asksaveasfilename(
            title="Save merged subtitles",
            defaultextension=".srt",
            filetypes=[("SubRip subtitles", "*.srt")],
            initialfile="merged.srt",
        )


def main() -> None:
    app = MergeApp()
    app.mainloop()


if __name__ == "__main__":
    main()
