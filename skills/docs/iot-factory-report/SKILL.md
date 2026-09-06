---
name: iot-factory-report
loop: shared
pdca: do
description: >
  Analyze factory IoT/SCADA time-series (CSV/Excel) → visual report with charts + PPTX.
  Covers UPW/RO, compressors, chillers. Cycle detection, anomaly marking, trend analysis.
  TRIGGER: "廠務報告", "設備分析", "IoT 資料分析", "UPW 分析", "壓縮機報告", "冷凍機分析".
  SKIP: generic CSV (office-xlsx); business reports without sensor data.
tags: [docs, workflow]
version: 1.0.0
user-invocable: true
allowed-tools: "Read, Write, Edit, Bash, Glob, Grep"
---

# IoT Factory Report

Industrial equipment time-series analysis → visual HTML charts → PPTX report.

## Supported Equipment Types

| Equipment | Key Metrics | Analysis Focus |
|-----------|-------------|----------------|
| UPW/RO (純水系統) | conductivity, flow rate, pressure, rejection rate | Membrane degradation trend, cleaning cycle detection |
| Compressor (壓縮機) | discharge pressure, temperature, power, vibration | Efficiency curve, overload events |
| Chiller (冷凍機) | supply/return temp, tonnage, COP | COP trend, capacity utilization |
| AHU (空調箱) | supply air temp, humidity, filter ΔP | Filter lifecycle, setpoint tracking |
| Boiler (鍋爐) | steam pressure, fuel consumption, stack temp | Combustion efficiency, blowdown frequency |

## Analysis Pipeline

### Step 1: Data Ingestion

Read CSV/Excel with time-series sensor data:
```python
import pandas as pd
df = pd.read_csv("sensor_data.csv", parse_dates=["timestamp"])
```

Detect:
- Timestamp column (auto-detect datetime formats)
- Sensor columns (numeric with units in header)
- Equipment ID / tag columns
- Sampling interval (1s, 1min, 5min, 1hr)

### Step 2: Time-Series Grouping

Group data by meaningful time windows:
- **Shift-based**: 日班/夜班 (08:00-20:00 / 20:00-08:00)
- **Daily**: Aggregate to daily min/max/avg/std
- **Weekly**: Week-over-week comparison
- **Event-based**: Group by equipment start/stop cycles

### Step 3: Analysis

For each metric:
1. **Trend**: Moving average (7-day or 30-day) with upper/lower bounds
2. **Anomalies**: Z-score > 3 or IQR method, mark with red dots
3. **Cycles**: Detect periodic patterns (FFT or autocorrelation)
4. **Correlations**: Cross-metric correlation matrix (e.g., temp vs. power)

### Step 4: HTML Chart Generation

Generate interactive charts using Python matplotlib or Chart.js:

```python
# Example: trend chart with anomaly markers
fig, ax = plt.subplots(figsize=(12, 4))
ax.plot(df["timestamp"], df["value"], color="#2563eb", linewidth=0.8)
ax.scatter(anomalies["timestamp"], anomalies["value"], color="red", s=20, zorder=5)
ax.fill_between(df["timestamp"], lower_bound, upper_bound, alpha=0.1, color="#2563eb")
```

Embed charts as base64 in HTML for self-contained reports.

### Step 5: PPTX Export

Use `office-pptx` skill or `python-pptx` to:
1. Title slide with equipment name, date range, summary
2. One slide per metric with chart + key statistics table
3. Anomaly summary slide with event list
4. Recommendation slide with maintenance suggestions

## Report Structure

```
# {Equipment Name} 分析報告
## 期間: {start_date} ~ {end_date}

### 摘要
- 資料點數: {N}
- 異常事件: {anomaly_count} 次
- 整體趨勢: {trend_direction}

### {Metric 1} 趨勢
[Chart]
| 統計 | 值 |
|------|-----|
| 平均 | xxx |
| 最大 | xxx |
| 最小 | xxx |
| 標準差 | xxx |

### 異常事件列表
| 時間 | 指標 | 值 | 嚴重度 |
|------|------|-----|--------|

### 建議
1. [Maintenance action based on trend]
2. [Optimization suggestion based on correlations]
```

## Domain Knowledge

- **UPW conductivity** should be < 0.056 μS/cm; rising trend = membrane degradation
- **Compressor discharge temperature** > 95°C = potential overload
- **Chiller COP** < 3.0 for water-cooled = investigate; normal range 4.0-6.0
- **Filter ΔP** > nameplate value × 1.5 = schedule replacement
