import math
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure

from load_analyzer import find_max_force, load_data


SECTION_DIMENSIONS = {
    "사각형": (("b_rect", "폭 b"), ("h_rect", "높이 h")),
    "원형봉(속이 참)": (("d_bar", "지름 d"),),
    "원형관(속이 빈)": (("D_tube", "바깥지름 D"), ("t_tube", "두께 t")),
    "사각형관(속이 빈)": (
        ("B_box", "바깥 폭 B"),
        ("H_box", "바깥 높이 H"),
        ("t_box", "두께 t"),
    ),
    "H형강": (
        ("B_h", "플랜지 폭 B"),
        ("H_h", "전체 높이 H"),
        ("tw", "웨브 두께 tw"),
        ("tf", "플랜지 두께 tf"),
    ),
}


def calculate_section_area(section_type, dimensions):
    if section_type not in SECTION_DIMENSIONS:
        raise ValueError("지원하지 않는 단면 종류입니다.")

    values = {}
    for key, label in SECTION_DIMENSIONS[section_type]:
        try:
            raw_value = dimensions[key]
        except (KeyError, TypeError, ValueError) as exc:
            raise ValueError(f"{label}를 숫자로 입력해주세요.") from exc
        if raw_value is None or not str(raw_value).strip():
            raise ValueError(f"{label}를 입력해주세요.")
        try:
            value = float(raw_value)
        except (TypeError, ValueError) as exc:
            raise ValueError(f"{label}는 숫자로 입력해주세요.") from exc
        if not math.isfinite(value) or value <= 0:
            raise ValueError(f"{label}는 0보다 큰 유한한 숫자여야 합니다.")
        values[key] = value

    try:
        if section_type == "사각형":
            area_mm2 = values["b_rect"] * values["h_rect"]
        elif section_type == "원형봉(속이 참)":
            area_mm2 = math.pi * values["d_bar"] ** 2 / 4
        elif section_type == "원형관(속이 빈)":
            if 2 * values["t_tube"] >= values["D_tube"]:
                raise ValueError(
                    "원형관 내부 공간이 없어집니다. 두께 t는 바깥지름 D의 절반보다 작아야 합니다."
                )
            inner_diameter = values["D_tube"] - 2 * values["t_tube"]
            area_mm2 = math.pi * (
                values["D_tube"] ** 2 - inner_diameter ** 2
            ) / 4
        elif section_type == "사각형관(속이 빈)":
            if 2 * values["t_box"] >= min(values["B_box"], values["H_box"]):
                raise ValueError("두께 t는 바깥 폭과 바깥 높이의 절반보다 작아야 합니다.")
            area_mm2 = (
                values["B_box"] * values["H_box"]
                - (values["B_box"] - 2 * values["t_box"])
                * (values["H_box"] - 2 * values["t_box"])
            )
        else:
            if 2 * values["tf"] >= values["H_h"]:
                raise ValueError("플랜지 두께 tf의 합은 전체 높이 H보다 작아야 합니다.")
            if values["tw"] >= values["B_h"]:
                raise ValueError("웨브 두께 tw는 플랜지 폭 B보다 작아야 합니다.")
            area_mm2 = (
                2 * values["B_h"] * values["tf"]
                + (values["H_h"] - 2 * values["tf"]) * values["tw"]
            )
    except OverflowError as exc:
        raise ValueError("치수가 너무 커서 단면적을 계산할 수 없습니다.") from exc

    if not math.isfinite(area_mm2) or area_mm2 <= 0:
        raise ValueError("계산된 단면적이 유효하지 않습니다.")
    return area_mm2


class LoadAnalyzerApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("하중 데이터 분석")
        self.geometry("900x700")
        self.minsize(760, 520)

        self.csv_path_var = tk.StringVar()
        self.section_type_var = tk.StringVar(value="사각형")
        self.dimension_vars = {
            key: tk.StringVar() for dims in SECTION_DIMENSIONS.values() for key, _ in dims
        }
        self.area_var = tk.StringVar(value="A = - mm²")
        self.data_count_var = tk.StringVar(value="CSV 파일을 선택한 뒤 분석을 누르세요.")

        self._build_ui()
        for dimension_var in self.dimension_vars.values():
            dimension_var.trace_add("write", self._update_area)
        self._update_dimension_fields()

    def _build_ui(self):
        container = ttk.Frame(self, padding=12)
        container.pack(fill="both", expand=True)
        container.columnconfigure(0, weight=1)
        container.rowconfigure(3, weight=1)

        file_frame = ttk.Frame(container)
        file_frame.grid(row=0, column=0, sticky="ew")
        file_frame.columnconfigure(1, weight=1)

        ttk.Button(
            file_frame,
            text="CSV 찾아보기",
            command=self._browse_csv,
        ).grid(row=0, column=0, padx=(0, 8))
        ttk.Entry(
            file_frame,
            textvariable=self.csv_path_var,
            state="readonly",
        ).grid(row=0, column=1, sticky="ew")

        section_frame = ttk.LabelFrame(container, text="단면 설정", padding=8)
        section_frame.grid(row=1, column=0, sticky="ew", pady=(10, 0))

        ttk.Label(section_frame, text="단면 종류").grid(row=0, column=0, padx=(0, 6), sticky="w")
        self.section_type_combo = ttk.Combobox(
            section_frame,
            textvariable=self.section_type_var,
            values=tuple(SECTION_DIMENSIONS),
            state="readonly",
            width=22,
        )
        self.section_type_combo.grid(row=0, column=1, sticky="w")
        self.section_type_combo.bind("<<ComboboxSelected>>", self._on_section_type_selected)

        self.dimensions_frame = ttk.Frame(section_frame)
        self.dimensions_frame.grid(row=1, column=0, columnspan=2, sticky="ew", pady=(10, 0))
        ttk.Label(section_frame, textvariable=self.area_var).grid(
            row=2, column=0, sticky="w", pady=(10, 0)
        )
        ttk.Button(
            section_frame,
            text="분석",
            command=self._analyze,
        ).grid(row=2, column=1, sticky="e", pady=(10, 0))
        section_frame.columnconfigure(1, weight=1)

        ttk.Label(
            container,
            textvariable=self.data_count_var,
            anchor="w",
        ).grid(row=2, column=0, sticky="ew", pady=(10, 8))

        graph_frame = ttk.LabelFrame(container, text="시간-응력 그래프", padding=8)
        graph_frame.grid(row=3, column=0, sticky="nsew")
        graph_frame.columnconfigure(0, weight=1)
        graph_frame.rowconfigure(0, weight=1)

        self.figure = Figure(figsize=(7, 4), dpi=100)
        self.axes = self.figure.add_subplot(111)
        self._show_empty_graph()
        self.canvas = FigureCanvasTkAgg(self.figure, master=graph_frame)
        self.canvas.get_tk_widget().grid(row=0, column=0, sticky="nsew")
        self.canvas.draw()

    def _browse_csv(self):
        selected_path = filedialog.askopenfilename(
            title="CSV 파일 선택",
            filetypes=[("CSV 파일", "*.csv"), ("모든 파일", "*.*")],
        )
        if not selected_path:
            return

        self.csv_path_var.set(selected_path)
        self.data_count_var.set("분석 버튼을 눌러 데이터를 불러오세요.")

    def _update_dimension_fields(self):
        for child in self.dimensions_frame.winfo_children():
            child.destroy()

        for column, (key, label) in enumerate(
            SECTION_DIMENSIONS[self.section_type_var.get()]
        ):
            ttk.Label(self.dimensions_frame, text=label).grid(
                row=column, column=0, padx=(0, 4), pady=2, sticky="w"
            )
            ttk.Entry(
                self.dimensions_frame,
                textvariable=self.dimension_vars[key],
                width=10,
            ).grid(row=column, column=1, padx=(0, 4), pady=2, sticky="w")
            ttk.Label(self.dimensions_frame, text="mm").grid(
                row=column, column=2, padx=(0, 12), pady=2, sticky="w"
            )
        self._update_area()

    def _on_section_type_selected(self, event):
        self.section_type_var.set(event.widget.get())
        self._update_dimension_fields()

    def _get_dimensions(self):
        section_type = self.section_type_var.get()
        dimensions = {
            key: self.dimension_vars[key].get()
            for key, _ in SECTION_DIMENSIONS[section_type]
        }
        return section_type, dimensions

    def _update_area(self, *_):
        section_type, dimensions = self._get_dimensions()
        try:
            area_mm2 = calculate_section_area(section_type, dimensions)
        except ValueError:
            self.area_var.set("A = - mm²")
            return

        self.area_var.set(f"A = {area_mm2:g} mm²")

    def _analyze(self):
        selected_path = self.csv_path_var.get()
        if not selected_path:
            messagebox.showerror("입력 오류", "먼저 CSV 파일을 선택해주세요.", parent=self)
            return

        section_type, dimensions = self._get_dimensions()
        try:
            area_mm2 = calculate_section_area(section_type, dimensions)
        except ValueError as exc:
            self.data_count_var.set(f"분석 중단: {exc}")
            self._show_empty_graph("유효한 단면 치수를 입력한 뒤 분석하세요.")
            self.canvas.draw()
            messagebox.showerror("단면 치수 오류", str(exc), parent=self)
            return

        try:
            data, invalid_values = load_data(Path(selected_path))
        except (OSError, ValueError) as exc:
            self.data_count_var.set("CSV 파일을 읽을 수 없습니다.")
            self._show_empty_graph()
            self.canvas.draw()
            messagebox.showerror("CSV 읽기 오류", str(exc), parent=self)
            return

        invalid_row_count = len({row_number for row_number, _, _ in invalid_values})
        count_text = f"유효 데이터 수: {len(data)}개 | 단면적: {area_mm2:g} mm²"
        if data:
            max_time, max_force = find_max_force(data)
            max_stress = max_force / area_mm2
            count_text += (
                f" | 최대 하중: {max_force:g} N ({max_time:g} s)"
                f" | 최대 응력: {max_stress:g} MPa"
            )
        if invalid_row_count:
            count_text += f" (잘못된 값이 있는 {invalid_row_count}개 행 제외)"
        self.data_count_var.set(count_text)
        self._draw_stress_graph(data, area_mm2)

    def _show_empty_graph(self, message="CSV 파일을 선택하세요."):
        self.axes.clear()
        self.axes.set_xlabel("Time (s)")
        self.axes.set_ylabel("Stress (MPa)")
        self.axes.grid(True, linestyle=":", alpha=0.6)
        self.axes.text(
            0.5,
            0.5,
            message,
            ha="center",
            va="center",
            transform=self.axes.transAxes,
        )

    def _draw_stress_graph(self, data, area_mm2):
        self.axes.clear()
        if data:
            times = [time_value for time_value, _ in data]
            stresses = [force_value / area_mm2 for _, force_value in data]
            self.axes.plot(times, stresses, marker="o", linestyle="-")
        else:
            self.axes.text(
                0.5,
                0.5,
                "표시할 유효 데이터가 없습니다.",
                ha="center",
                va="center",
                transform=self.axes.transAxes,
            )
        self.axes.set_xlabel("Time (s)")
        self.axes.set_ylabel("Stress (MPa)")
        self.axes.grid(True, linestyle=":", alpha=0.6)
        self.figure.tight_layout()
        self.canvas.draw()


if __name__ == "__main__":
    app = LoadAnalyzerApp()
    app.mainloop()
