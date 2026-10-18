{{ config(materialized='table') }}

WITH stg AS (
    SELECT * FROM {{ ref('stg_turbofan_telemetry') }}
),

engine_lifecycle AS (
    SELECT
        engine_id,
        MAX(cycle) AS max_cycle
    FROM stg
    GROUP BY engine_id
),

with_rul_and_drift AS (
    SELECT
        s.*,
        el.max_cycle,
        (el.max_cycle - s.cycle) AS raw_rul,
        LEAST(el.max_cycle - s.cycle, 125) AS target_rul,

        -- Degradasi/Drift relatif terhadap siklus pertama mesin (Cycle 1)
        s.sensor_2_lpc_temp - FIRST_VALUE(s.sensor_2_lpc_temp) OVER (PARTITION BY s.engine_id ORDER BY s.cycle) AS s2_drift_initial,
        s.sensor_3_hpc_temp - FIRST_VALUE(s.sensor_3_hpc_temp) OVER (PARTITION BY s.engine_id ORDER BY s.cycle) AS s3_drift_initial,
        s.sensor_4_lpt_temp - FIRST_VALUE(s.sensor_4_lpt_temp) OVER (PARTITION BY s.engine_id ORDER BY s.cycle) AS s4_drift_initial,
        s.sensor_7_hpc_pressure - FIRST_VALUE(s.sensor_7_hpc_pressure) OVER (PARTITION BY s.engine_id ORDER BY s.cycle) AS s7_drift_initial,
        s.sensor_11_static_hpc_pressure - FIRST_VALUE(s.sensor_11_static_hpc_pressure) OVER (PARTITION BY s.engine_id ORDER BY s.cycle) AS s11_drift_initial,
        s.sensor_12_fuel_flow_ratio - FIRST_VALUE(s.sensor_12_fuel_flow_ratio) OVER (PARTITION BY s.engine_id ORDER BY s.cycle) AS s12_drift_initial,

        -- Rolling Mean (Window 5 cycles) untuk sensor vital
        AVG(s.sensor_2_lpc_temp) OVER (PARTITION BY s.engine_id ORDER BY s.cycle ROWS BETWEEN 4 PRECEDING AND CURRENT ROW) AS s2_roll_mean_5,
        AVG(s.sensor_3_hpc_temp) OVER (PARTITION BY s.engine_id ORDER BY s.cycle ROWS BETWEEN 4 PRECEDING AND CURRENT ROW) AS s3_roll_mean_5,
        AVG(s.sensor_4_lpt_temp) OVER (PARTITION BY s.engine_id ORDER BY s.cycle ROWS BETWEEN 4 PRECEDING AND CURRENT ROW) AS s4_roll_mean_5,
        AVG(s.sensor_7_hpc_pressure) OVER (PARTITION BY s.engine_id ORDER BY s.cycle ROWS BETWEEN 4 PRECEDING AND CURRENT ROW) AS s7_roll_mean_5,
        AVG(s.sensor_8_fan_speed) OVER (PARTITION BY s.engine_id ORDER BY s.cycle ROWS BETWEEN 4 PRECEDING AND CURRENT ROW) AS s8_roll_mean_5,
        AVG(s.sensor_9_core_speed) OVER (PARTITION BY s.engine_id ORDER BY s.cycle ROWS BETWEEN 4 PRECEDING AND CURRENT ROW) AS s9_roll_mean_5,
        AVG(s.sensor_11_static_hpc_pressure) OVER (PARTITION BY s.engine_id ORDER BY s.cycle ROWS BETWEEN 4 PRECEDING AND CURRENT ROW) AS s11_roll_mean_5,
        AVG(s.sensor_12_fuel_flow_ratio) OVER (PARTITION BY s.engine_id ORDER BY s.cycle ROWS BETWEEN 4 PRECEDING AND CURRENT ROW) AS s12_roll_mean_5,
        AVG(s.sensor_15_bypass_ratio) OVER (PARTITION BY s.engine_id ORDER BY s.cycle ROWS BETWEEN 4 PRECEDING AND CURRENT ROW) AS s15_roll_mean_5,

        -- Rolling Standard Deviation (Window 5 cycles) untuk mendeteksi osilasi/fluktuasi keausan
        COALESCE(STDDEV(s.sensor_2_lpc_temp) OVER (PARTITION BY s.engine_id ORDER BY s.cycle ROWS BETWEEN 4 PRECEDING AND CURRENT ROW), 0.0) AS s2_roll_std_5,
        COALESCE(STDDEV(s.sensor_3_hpc_temp) OVER (PARTITION BY s.engine_id ORDER BY s.cycle ROWS BETWEEN 4 PRECEDING AND CURRENT ROW), 0.0) AS s3_roll_std_5,
        COALESCE(STDDEV(s.sensor_4_lpt_temp) OVER (PARTITION BY s.engine_id ORDER BY s.cycle ROWS BETWEEN 4 PRECEDING AND CURRENT ROW), 0.0) AS s4_roll_std_5,
        COALESCE(STDDEV(s.sensor_7_hpc_pressure) OVER (PARTITION BY s.engine_id ORDER BY s.cycle ROWS BETWEEN 4 PRECEDING AND CURRENT ROW), 0.0) AS s7_roll_std_5,
        COALESCE(STDDEV(s.sensor_11_static_hpc_pressure) OVER (PARTITION BY s.engine_id ORDER BY s.cycle ROWS BETWEEN 4 PRECEDING AND CURRENT ROW), 0.0) AS s11_roll_std_5,
        COALESCE(STDDEV(s.sensor_12_fuel_flow_ratio) OVER (PARTITION BY s.engine_id ORDER BY s.cycle ROWS BETWEEN 4 PRECEDING AND CURRENT ROW), 0.0) AS s12_roll_std_5

    FROM stg s
    JOIN engine_lifecycle el ON s.engine_id = el.engine_id
)

SELECT * FROM with_rul_and_drift
