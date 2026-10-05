import tkinter as tk
from tkinter import ttk, messagebox


# 단위 정의
UNIT_SYSTEMS = {
    "length": {
        "label": "길이",
        "base": "m",
        "units": {
            "m": 1.0,
            "km": 1000.0,
            "cm": 0.01,
            "mm": 0.001,
            "in": 0.0254,
            "ft": 0.3048,
            "yd": 0.9144,
            "mi": 1609.344,
        },
        "display": {"m": "미터(m)", "km": "킬로미터(km)", "cm": "센티미터(cm)", "mm": "밀리미터(mm)", "in": "인치(in)", "ft": "피트(ft)", "yd": "야드(yd)", "mi": "마일(mi)"},
    },
    "weight": {
        "label": "무게",
        "base": "kg",
        "units": {
            "kg": 1.0,
            "g": 0.001,
            "mg": 0.000001,
            "lb": 0.45359237,
            "oz": 0.028349523125,
            "ton": 1000.0,
        },
        "display": {"kg": "킬로그램(kg)", "g": "그램(g)", "mg": "밀리그램(mg)", "lb": "파운드(lb)", "oz": "온스(oz)", "ton": "톤(ton)"},
    },
    "temperature": {
        "label": "온도",
        "base": "C",
        "units": {
            "C": "C",
            "F": "F",
            "K": "K",
        },
        "display": {"C": "섭씨(°C)", "F": "화씨(°F)", "K": "켈빈(K)"},
    },
    "volume": {
        "label": "부피",
        "base": "L",
        "units": {
            "L": 1.0,
            "mL": 0.001,
            "gal": 3.785411784,
            "cup": 0.2365882365,
            "pt": 0.473176473,
            "qt": 0.946352946,
        },
        "display": {"L": "리터(L)", "mL": "밀리리터(mL)", "gal": "갤런(gal)", "cup": "컵(cup)", "pt": "파인트(pt)", "qt": "쿼트(qt)"},
    },
    "speed": {
        "label": "속도",
        "base": "m/s",
        "units": {
            "m/s": 1.0,
            "km/h": 0.2777777778,
            "mph": 0.44704,
            "knot": 0.5144444444,
            "ft/s": 0.3048,
        },
        "display": {"m/s": "미터/초(m/s)", "km/h": "킬로미터/시(km/h)", "mph": "마일/시(mph)", "knot": "노트(knot)", "ft/s": "피트/초(ft/s)"},
    },
}


def to_celsius(value, unit):
    if unit == "C":
        return value
    if unit == "F":
        return (value - 32) * 5 / 9
    if unit == "K":
        return value - 273.15
    raise ValueError(f"지원하지 않는 온도 단위: {unit}")


def from_celsius(value, unit):
    if unit == "C":
        return value
    if unit == "F":
        return (value * 9 / 5) + 32
    if unit == "K":
        return value + 273.15
    raise ValueError(f"지원하지 않는 온도 단위: {unit}")


def linear_convert(value, from_unit, to_unit, unit_group):
    units = UNIT_SYSTEMS[unit_group]["units"]
    base_value = value * units[from_unit]
    return base_value / units[to_unit]


def convert_value(value, category, from_unit, to_unit):
    if category == "temperature":
        c_value = to_celsius(value, from_unit)
        return from_celsius(c_value, to_unit)

    return linear_convert(value, from_unit, to_unit, category)


class UnitConverterApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("단위 변환기")
        self.geometry("500x420")
        self.resizable(False, False)

        self.category_var = tk.StringVar(value="length")
        self.from_var = tk.StringVar()
        self.to_var = tk.StringVar()

        self._build_ui()
        self._update_unit_options()

    def _build_ui(self):
        container = ttk.Frame(self, padding=20)
        container.pack(fill="both", expand=True)

        ttk.Label(container, text="카테고리", font=("Malgun Gothic", 10, "bold")).grid(
            row=0, column=0, sticky="w", pady=(0, 5)
        )
        self.category_combo = ttk.Combobox(
            container,
            textvariable=self.category_var,
            values=[(info["label"], key) for key, info in UNIT_SYSTEMS.items()],
            state="readonly",
            width=20,
        )
        self.category_combo.grid(row=0, column=1, padx=(10, 0), sticky="ew")
        self.category_combo.bind("<<ComboboxSelected>>", lambda event: self._update_unit_options())

        ttk.Label(container, text="값", font=("Malgun Gothic", 10, "bold")).grid(
            row=1, column=0, sticky="w", pady=(15, 5)
        )
        self.value_entry = ttk.Entry(container, width=25)
        self.value_entry.grid(row=1, column=1, padx=(10, 0), sticky="ew")
        self.value_entry.insert(0, "1")

        ttk.Label(container, text="변환 전", font=("Malgun Gothic", 10, "bold")).grid(
            row=2, column=0, sticky="w", pady=(15, 5)
        )
        self.from_combo = ttk.Combobox(container, textvariable=self.from_var, state="readonly", width=20)
        self.from_combo.grid(row=2, column=1, padx=(10, 0), sticky="ew")

        ttk.Label(container, text="변환 후", font=("Malgun Gothic", 10, "bold")).grid(
            row=3, column=0, sticky="w", pady=(15, 5)
        )
        self.to_combo = ttk.Combobox(container, textvariable=self.to_var, state="readonly", width=20)
        self.to_combo.grid(row=3, column=1, padx=(10, 0), sticky="ew")

        convert_btn = ttk.Button(container, text="변환", command=self.convert)
        convert_btn.grid(row=4, column=0, columnspan=2, pady=(20, 10), sticky="ew")

        result_frame = ttk.LabelFrame(container, text="결과", padding=(10, 10))
        result_frame.grid(row=5, column=0, columnspan=2, sticky="nsew", pady=(10, 0))
        result_frame.grid_columnconfigure(0, weight=1)

        self.result_var = tk.StringVar(value="결과가 여기에 표시됩니다.")
        ttk.Label(result_frame, textvariable=self.result_var, wraplength=380, justify="center").grid(
            row=0, column=0, sticky="nsew"
        )

        self.value_entry.focus()

    def _update_unit_options(self):
        category = self.category_var.get()
        unit_group = UNIT_SYSTEMS[category]

        display_units = list(unit_group["display"].items())
        options = [label for _, label in display_units]
        self.from_combo["values"] = options
        self.to_combo["values"] = options

        first_key = list(unit_group["units"].keys())[0]
        second_key = list(unit_group["units"].keys())[1] if len(unit_group["units"]) > 1 else first_key

        self.from_var.set(unit_group["display"][first_key])
        self.to_var.set(unit_group["display"][second_key])

    def convert(self):
        category = self.category_var.get()
        try:
            value = float(self.value_entry.get())
        except ValueError:
            messagebox.showerror("오류", "숫자를 입력해주세요.")
            return

        from_label = self.from_var.get()
        to_label = self.to_var.get()

        display_map = UNIT_SYSTEMS[category]["display"]
        reverse_map = {v: k for k, v in display_map.items()}

        from_unit = reverse_map.get(from_label)
        to_unit = reverse_map.get(to_label)

        if from_unit is None or to_unit is None:
            messagebox.showerror("오류", "단위를 다시 선택해주세요.")
            return

        try:
            result = convert_value(value, category, from_unit, to_unit)
            self.result_var.set(f"{value} {display_map[from_unit]} = {result:.6g} {display_map[to_unit]}")
        except Exception as exc:
            messagebox.showerror("오류", str(exc))


if __name__ == "__main__":
    app = UnitConverterApp()
    app.mainloop()
