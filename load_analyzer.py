import csv
import math
from pathlib import Path

import matplotlib.pyplot as plt


CSV_PATH = Path(__file__).resolve().with_name("load_data.csv")
OUTPUT_PATH = Path(__file__).resolve().with_name("load_result.csv")
PLOT_PATH = Path(__file__).resolve().with_name("stress_plot.png")
AREA_MM2 = 100
REFERENCE_STRESS_MPA = 6


def load_data(csv_path: Path):
    with csv_path.open("r", encoding="utf-8-sig", newline="") as file:
        reader = csv.DictReader(file)

        required_columns = {"time_s", "force_N"}
        if reader.fieldnames is None or not required_columns.issubset(set(reader.fieldnames)):
            raise ValueError(
                f"CSV 파일에 필요한 컬럼이 없습니다. 필요 컬럼: {sorted(required_columns)} | 실제 컬럼: {reader.fieldnames}"
            )

        data = []
        invalid_values = []
        for row in reader:
            row_number = reader.line_num
            parsed_values = {}
            row_is_valid = True

            for column in ("time_s", "force_N"):
                raw_value = row.get(column)
                try:
                    parsed_value = float(raw_value)
                    if not math.isfinite(parsed_value):
                        raise ValueError
                except (TypeError, ValueError):
                    invalid_values.append((row_number, column, raw_value))
                    row_is_valid = False
                else:
                    parsed_values[column] = parsed_value

            if not row_is_valid:
                continue

            time_value = parsed_values["time_s"]
            force_value = parsed_values["force_N"]
            data.append((time_value, force_value))

    return data, invalid_values


def find_max_force(data):
    if not data:
        raise ValueError("CSV 파일에 데이터가 없습니다.")

    max_time = data[0][0]
    max_force = data[0][1]

    for time_value, force_value in data[1:]:
        if force_value > max_force:
            max_force = force_value
            max_time = time_value

    return max_time, max_force


def save_results(data):
    output_path = OUTPUT_PATH
    suffix = 1

    while True:
        try:
            with output_path.open("x", encoding="utf-8", newline="") as file:
                writer = csv.DictWriter(
                    file,
                    fieldnames=["time_s", "force_N", "stress_MPa"],
                )
                writer.writeheader()
                writer.writerows(
                    {
                        "time_s": time_value,
                        "force_N": force_value,
                        "stress_MPa": force_value / AREA_MM2,
                    }
                    for time_value, force_value in data
                )
            return output_path
        except FileExistsError:
            output_path = OUTPUT_PATH.with_name(
                f"{OUTPUT_PATH.stem}_{suffix}{OUTPUT_PATH.suffix}"
            )
            suffix += 1


def save_stress_plot(stress_data, max_stress_time, max_stress):
    times = [time_value for time_value, _, _ in stress_data]
    stresses = [stress_value for _, _, stress_value in stress_data]
    above_reference_data = [
        (time_value, stress_value)
        for time_value, _, stress_value in stress_data
        if stress_value > REFERENCE_STRESS_MPA
    ]

    figure, axes = plt.subplots()
    axes.plot(times, stresses, marker="o", linestyle="-", label="Stress")
    axes.axhline(
        REFERENCE_STRESS_MPA,
        color="gray",
        linestyle="--",
        label=f"Reference ({REFERENCE_STRESS_MPA} MPa)",
    )
    if above_reference_data:
        axes.scatter(
            [time_value for time_value, _ in above_reference_data],
            [stress_value for _, stress_value in above_reference_data],
            color="orange",
            label="Above reference",
            zorder=3,
        )
    axes.scatter(
        [max_stress_time],
        [max_stress],
        color="red",
        label="Maximum stress",
        zorder=4,
    )
    axes.annotate(
        f"Max: {max_stress:.2f} MPa",
        xy=(max_stress_time, max_stress),
        xytext=(10, 10),
        textcoords="offset points",
        arrowprops={"arrowstyle": "->"},
    )
    axes.set_xlabel("Time (s)")
    axes.set_ylabel("Stress (MPa)")
    axes.grid(True, linestyle=":", alpha=0.6)
    axes.legend()
    figure.savefig(PLOT_PATH)
    plt.close(figure)
    return PLOT_PATH


def main():
    data, invalid_values = load_data(CSV_PATH)
    for row_number, column, value in invalid_values:
        print(
            f"잘못된 값: 원본 CSV {row_number}행, {column}={value!r} "
            "(해당 행 제외)"
        )

    print(f"제외한 행 수: {len({row_number for row_number, _, _ in invalid_values})}개")
    print(f"유효한 데이터 수: {len(data)}개")
    if not data:
        print("유효한 데이터가 없어 계산과 파일 저장을 중단합니다.")
        return

    max_time, max_force = find_max_force(data)
    stress_data = [
        (time_value, force_value, force_value / AREA_MM2)
        for time_value, force_value in data
    ]
    max_stress_time, max_stress = max(
        ((time_value, stress_value) for time_value, _, stress_value in stress_data),
        key=lambda item: item[1],
    )
    above_reference_count = sum(
        stress_value > REFERENCE_STRESS_MPA
        for _, _, stress_value in stress_data
    )
    output_path = save_results(data)
    plot_path = save_stress_plot(stress_data, max_stress_time, max_stress)

    print(f"최대 하중: {max_force:.0f} N")
    print(f"해당 시간: {max_time:.0f} s")
    print(f"최대 응력: {max_stress:.2f} MPa")
    print(f"해당 시간: {max_stress_time:.0f} s")
    print(f"기준 응력 {REFERENCE_STRESS_MPA} MPa 초과 데이터 개수: {above_reference_count}개")
    print(f"결과 파일: {output_path.name}")
    print(f"그래프 파일: {plot_path.name}")


if __name__ == "__main__":
    main()
