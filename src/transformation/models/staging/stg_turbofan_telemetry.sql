{{ config(materialized='view') }}

WITH source AS (
    SELECT * FROM {{ source('raw_data', 'raw_turbofan_telemetry') }}
),

renamed_and_pruned AS (
    SELECT
        -- Identifiers
        engine_id,
        cycle,

        -- Operational Settings
        setting_1,
        setting_2,
        setting_3,

        -- 14 Active Degrading Sensors (Sensor konstan/mati s1, s5, s10, s16, s18, s19 dibuang)
        s_2  AS sensor_2_lpc_temp,
        s_3  AS sensor_3_hpc_temp,
        s_4  AS sensor_4_lpt_temp,
        s_7  AS sensor_7_hpc_pressure,
        s_8  AS sensor_8_fan_speed,
        s_9  AS sensor_9_core_speed,
        s_11 AS sensor_11_static_hpc_pressure,
        s_12 AS sensor_12_fuel_flow_ratio,
        s_13 AS sensor_13_corrected_fan_speed,
        s_14 AS sensor_14_corrected_core_speed,
        s_15 AS sensor_15_bypass_ratio,
        s_17 AS sensor_17_bleed_enthalpy,
        s_20 AS sensor_20_hpt_coolant_bleed,
        s_21 AS sensor_21_lpt_coolant_bleed,

        -- Metadata
        event_timestamp,
        ingested_at
    FROM source
)

SELECT * FROM renamed_and_pruned
