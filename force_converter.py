import ast
import math
import operator
import re
import tkinter as tk
from tkinter import ttk


CATEGORY_UNITS = {
    "길이": ["mm", "cm", "m", "km", "inch", "ft", "yd", "mile"],
    "무게": ["mg", "g", "kg", "lb", "oz"],
    "힘": ["N", "kN", "kgf", "lbf"],
    "부피": ["ml", "L", "cup", "pint", "quart", "gallon"],
    "온도": ["℃", "℉", "K"],
    "속도": ["m/s", "km/h", "mph", "knot"],
}

BASE_FACTORS = {
    "길이": {
        "mm": 0.001,
        "cm": 0.01,
        "m": 1.0,
        "km": 1000.0,
        "inch": 0.0254,
        "ft": 0.3048,
        "yd": 0.9144,
        "mile": 1609.344,
    },
    "무게": {
        "mg": 0.000001,
        "g": 0.001,
        "kg": 1.0,
        "lb": 0.45359237,
        "oz": 0.028349523125,
    },
    "힘": {
        "N": 1.0,
        "kN": 1000.0,
        "kgf": 9.80665,
        "lbf": 4.4482216152605,
    },
    "부피": {
        "ml": 0.001,
        "L": 1.0,
        "cup": 0.24,
        "pint": 0.473176473,
        "quart": 0.946352946,
        "gallon": 3.785411784,
    },
    "속도": {
        "m/s": 1.0,
        "km/h": 0.2777777778,
        "mph": 0.44704,
        "knot": 0.5144444444,
    },
}


def convert_temperature(value, from_unit, to_unit):
    if from_unit == "℃":
        celsius = value
    elif from_unit == "℉":
        celsius = (value - 32) * 5 / 9
    else:
        celsius = value - 273.15

    if to_unit == "℃":
        return celsius
    if to_unit == "℉":
        return celsius * 9 / 5 + 32
    return celsius + 273.15


def convert_value(value, category, from_unit, to_unit):
    if category == "온도":
        return convert_temperature(value, from_unit, to_unit)

    base_value = value * BASE_FACTORS[category][from_unit]
    return base_value / BASE_FACTORS[category][to_unit]


def format_number(value):
    if abs(value) >= 1000000 or (0 < abs(value) < 0.0001):
        return f"{value:.6e}"
    return f"{value:,.6f}".rstrip("0").rstrip(".")


class UnitConverterApp(tk.Tk):
    def __init__(self):
        super().__init__()

        self.title("단위 변환기 GUI 계산기")
        self.geometry("1000x700")
        self.minsize(900, 600)
        self.configure(bg="#f3f4f6")

        self.category_var = tk.StringVar(value="길이")
        self.from_var = tk.StringVar()
        self.to_var = tk.StringVar()
        self.result_var = tk.StringVar(
            value="변환 결과가 여기에 표시됩니다."
        )
        self.calc_var = tk.StringVar()
        self.calc_just_calculated = False

        self.main_frame = tk.Frame(self, bg="#f3f4f6")
        self.main_frame.grid(
            row=0,
            column=0,
            sticky="nsew",
            padx=18,
            pady=18,
        )

        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        self.main_frame.grid_rowconfigure(0, weight=1)
        self.main_frame.grid_columnconfigure(0, weight=3)
        self.main_frame.grid_columnconfigure(1, weight=2)

        self.create_converter_ui()
        self.create_calculator_ui()
        self.create_history_ui()
        self.update_unit_options()

    def create_converter_ui(self):
        self.left_frame = tk.Frame(
            self.main_frame,
            bg="#f3f4f6",
        )
        self.left_frame.grid(
            row=0,
            column=0,
            sticky="nsew",
            padx=(0, 12),
        )

        self.left_frame.grid_columnconfigure(0, weight=1)

        title = tk.Label(
            self.left_frame,
            text="단위 변환기",
            font=("Malgun Gothic", 20, "bold"),
            bg="#f3f4f6",
            fg="#1f2937",
        )
        title.grid(
            row=0,
            column=0,
            sticky="w",
            pady=(0, 15),
        )

        self.settings_frame = tk.LabelFrame(
            self.left_frame,
            text="변환 설정",
            font=("Malgun Gothic", 11, "bold"),
            bg="#f3f4f6",
            padx=18,
            pady=12,
        )
        self.settings_frame.grid(
            row=1,
            column=0,
            sticky="ew",
        )
        self.settings_frame.grid_columnconfigure(1, weight=1)

        tk.Label(
            self.settings_frame,
            text="분류",
            font=("Malgun Gothic", 11, "bold"),
            bg="#f3f4f6",
        ).grid(row=0, column=0, sticky="w", pady=8)

        category_combo = ttk.Combobox(
            self.settings_frame,
            textvariable=self.category_var,
            values=list(CATEGORY_UNITS.keys()),
            state="readonly",
        )
        category_combo.grid(
            row=0,
            column=1,
            sticky="ew",
            padx=(12, 0),
        )
        category_combo.bind(
            "<<ComboboxSelected>>",
            self.update_unit_options,
        )

        tk.Label(
            self.settings_frame,
            text="값",
            font=("Malgun Gothic", 11, "bold"),
            bg="#f3f4f6",
        ).grid(row=1, column=0, sticky="w", pady=8)

        self.value_entry = ttk.Entry(self.settings_frame)
        self.value_entry.grid(
            row=1,
            column=1,
            sticky="ew",
            padx=(12, 0),
        )
        self.value_entry.insert(0, "1")

        tk.Label(
            self.settings_frame,
            text="변환 전",
            font=("Malgun Gothic", 11, "bold"),
            bg="#f3f4f6",
        ).grid(row=2, column=0, sticky="w", pady=8)

        self.from_combo = ttk.Combobox(
            self.settings_frame,
            textvariable=self.from_var,
            state="readonly",
        )
        self.from_combo.grid(
            row=2,
            column=1,
            sticky="ew",
            padx=(12, 0),
        )

        tk.Label(
            self.settings_frame,
            text="변환 후",
            font=("Malgun Gothic", 11, "bold"),
            bg="#f3f4f6",
        ).grid(row=3, column=0, sticky="w", pady=8)

        self.to_combo = ttk.Combobox(
            self.settings_frame,
            textvariable=self.to_var,
            state="readonly",
        )
        self.to_combo.grid(
            row=3,
            column=1,
            sticky="ew",
            padx=(12, 0),
        )

        tk.Button(
            self.settings_frame,
            text="변환하기",
            command=self.convert,
            bg="#2563eb",
            fg="white",
            font=("Malgun Gothic", 10, "bold"),
            bd=0,
            height=2,
        ).grid(
            row=4,
            column=0,
            columnspan=2,
            sticky="ew",
            pady=(14, 4),
        )

        self.result_frame = tk.Frame(
            self.left_frame,
            bg="white",
            bd=1,
            relief="solid",
            padx=16,
            pady=16,
        )
        self.result_frame.grid(
            row=2,
            column=0,
            sticky="ew",
            pady=(14, 0),
        )

        tk.Label(
            self.result_frame,
            textvariable=self.result_var,
            font=("Malgun Gothic", 12, "bold"),
            bg="white",
            fg="#111827",
            anchor="w",
        ).grid(
            row=0,
            column=0,
            sticky="ew",
        )

    def create_calculator_ui(self):
        self.calculator_frame = tk.LabelFrame(
            self.left_frame,
            text="계산기",
            font=("Malgun Gothic", 11, "bold"),
            bg="#f3f4f6",
            padx=10,
            pady=10,
        )
        self.calculator_frame.grid(
            row=3,
            column=0,
            sticky="ew",
            pady=(18, 0),
        )

        for column in range(4):
            self.calculator_frame.grid_columnconfigure(
                column,
                weight=1,
            )

        entry = ttk.Entry(
            self.calculator_frame,
            textvariable=self.calc_var,
            justify="right",
            font=("Arial", 16),
            state="readonly",
        )
        entry.grid(
            row=0,
            column=0,
            columnspan=4,
            sticky="ew",
            pady=(0, 8),
        )

        buttons = [
            ["C", "⌫", "(", ")"],
            ["7", "8", "9", "÷"],
            ["4", "5", "6", "×"],
            ["1", "2", "3", "-"],
            ["0", ".", "=", "+"],
        ]

        for row, button_row in enumerate(buttons, start=1):
            for column, text in enumerate(button_row):
                tk.Button(
                    self.calculator_frame,
                    text=text,
                    height=2,
                    font=("Arial", 11, "bold"),
                    command=lambda value=text: self.calculator_input(
                        value
                    ),
                ).grid(
                    row=row,
                    column=column,
                    padx=2,
                    pady=2,
                    sticky="ew",
                )

    def create_history_ui(self):
        self.history_frame = tk.LabelFrame(
            self.main_frame,
            text="최근 계산 기록",
            font=("Malgun Gothic", 11, "bold"),
            bg="#f3f4f6",
            padx=10,
            pady=10,
        )
        self.history_frame.grid(
            row=0,
            column=1,
            sticky="nsew",
        )

        self.history_frame.grid_rowconfigure(0, weight=1)
        self.history_frame.grid_columnconfigure(0, weight=1)

        self.history_listbox = tk.Listbox(
            self.history_frame,
            font=("Malgun Gothic", 10),
            activestyle="none",
        )
        self.history_listbox.grid(
            row=0,
            column=0,
            sticky="nsew",
        )

        scrollbar = ttk.Scrollbar(
            self.history_frame,
            orient="vertical",
            command=self.history_listbox.yview,
        )
        scrollbar.grid(
            row=0,
            column=1,
            sticky="ns",
        )

        self.history_listbox.configure(
            yscrollcommand=scrollbar.set,
        )

        tk.Button(
            self.history_frame,
            text="기록 지우기",
            command=self.clear_history,
            bg="#6b7280",
            fg="white",
            bd=0,
            height=2,
        ).grid(
            row=1,
            column=0,
            columnspan=2,
            sticky="ew",
            pady=(10, 0),
        )

    def update_unit_options(self, event=None):
        units = CATEGORY_UNITS[self.category_var.get()]
        self.from_combo["values"] = units
        self.to_combo["values"] = units
        self.from_var.set(units[0])
        self.to_var.set(units[-1])

    def convert(self):
        try:
            input_text = self.value_entry.get().strip()
            category = self.category_var.get()

            unit_pattern = "|".join(
                re.escape(unit)
                for unit in sorted(
                    CATEGORY_UNITS[category],
                    key=len,
                    reverse=True,
                )
            )

            pattern = (
                rf"^([+-]?(?:\d+(?:\.\d*)?|\.\d+)"
                rf"(?:[eE][+-]?\d+)?)"
                rf"(?:\s*({unit_pattern}))?$"
            )

            match = re.fullmatch(pattern, input_text)

            if not match:
                raise ValueError

            value = float(match.group(1))

            if not math.isfinite(value):
                raise ValueError

            input_unit = match.group(2)
            from_unit = input_unit or self.from_var.get()
            to_unit = self.to_var.get()

            if from_unit not in CATEGORY_UNITS[category]:
                raise ValueError

            if input_unit and input_unit != self.from_var.get():
                self.from_var.set(input_unit)

            result = convert_value(
                value,
                category,
                from_unit,
                to_unit,
            )

            if not math.isfinite(result):
                raise ValueError

            input_display = f"{format_number(value)} {from_unit}"
            result_display = f"{result:.2f} {to_unit}"

            self.result_var.set(
                f"{input_display} = {result_display}"
            )

            self.history_listbox.insert(
                0,
                f"[변환] {input_display} = {result_display}",
            )

        except (
            ValueError,
            KeyError,
            OverflowError,
            TypeError,
        ):
            self.result_var.set(
                "숫자와 단위를 올바르게 입력해 주세요."
            )

    def calculator_input(self, value):
        if value == "C":
            self.calc_var.set("")
            self.calc_just_calculated = False
            return

        if value == "⌫":
            self.calc_var.set(
                self.calc_var.get()[:-1]
            )
            self.calc_just_calculated = False
            return

        if value == "=":
            self.calculate_expression()
            return

        current = self.calc_var.get()

        if current == "오류":
            current = ""

        if self.calc_just_calculated:
            if value not in "+-×÷":
                current = ""
            else:
                current = current.replace(",", "")

        self.calc_var.set(current + value)
        self.calc_just_calculated = False

    def calculate_expression(self):
        expression = self.calc_var.get().strip()

        python_expression = (
            expression.replace(",", "")
            .replace("×", "*")
            .replace("÷", "/")
        )

        try:
            tree = ast.parse(
                python_expression,
                mode="eval",
            )
            result = self.evaluate_node(tree.body)

            if not isinstance(result, (int, float)):
                raise ValueError

            if not math.isfinite(result):
                raise ValueError

            formatted_result = format_number(result)

            self.history_listbox.insert(
                0,
                f"{expression} = {formatted_result}",
            )

            self.calc_var.set(formatted_result)
            self.calc_just_calculated = True

        except (
            SyntaxError,
            ValueError,
            ZeroDivisionError,
            TypeError,
            OverflowError,
        ):
            self.calc_var.set("오류")
            self.calc_just_calculated = False

    def evaluate_node(self, node):
        if isinstance(node, ast.Constant):
            if (
                isinstance(node.value, (int, float))
                and not isinstance(node.value, bool)
            ):
                return node.value
            raise ValueError

        if isinstance(node, ast.UnaryOp):
            if isinstance(node.op, (ast.UAdd, ast.USub)):
                value = self.evaluate_node(node.operand)

                if isinstance(node.op, ast.UAdd):
                    return value

                return -value

            raise ValueError

        if isinstance(node, ast.BinOp):
            left = self.evaluate_node(node.left)
            right = self.evaluate_node(node.right)

            operations = {
                ast.Add: operator.add,
                ast.Sub: operator.sub,
                ast.Mult: operator.mul,
                ast.Div: operator.truediv,
            }

            for operation_type, operation in operations.items():
                if isinstance(node.op, operation_type):
                    return operation(left, right)

            raise ValueError

        raise ValueError

    def clear_history(self):
        self.history_listbox.delete(0, tk.END)


if __name__ == "__main__":
    app = UnitConverterApp()
    app.mainloop()