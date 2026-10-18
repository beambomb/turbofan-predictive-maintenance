import pandas as pd
import numpy as np
import joblib

raw_cols = ['engine_id', 'cycle', 'setting_1', 'setting_2', 'setting_3'] + [f's_{i}' for i in range(1, 22)]
test_df = pd.read_csv('data/raw/test_FD001.txt', sep=r'\s+', header=None, names=raw_cols)

rename_map = {
    's_2': 'sensor_2_lpc_temp', 's_3': 'sensor_3_hpc_temp', 's_4': 'sensor_4_lpt_temp',
    's_7': 'sensor_7_hpc_pressure', 's_8': 'sensor_8_fan_speed', 's_9': 'sensor_9_core_speed',
    's_11': 'sensor_11_static_hpc_pressure', 's_12': 'sensor_12_fuel_flow_ratio',
    's_13': 'sensor_13_corrected_fan_speed', 's_14': 'sensor_14_corrected_core_speed',
    's_15': 'sensor_15_bypass_ratio', 's_17': 'sensor_17_bleed_enthalpy',
    's_20': 'sensor_20_hpt_coolant_bleed', 's_21': 'sensor_21_lpt_coolant_bleed'
}
test_df = test_df.rename(columns=rename_map)

dfs = []
for eng, grp in test_df.groupby('engine_id'):
    grp = grp.sort_values('cycle').copy()
    
    grp['s2_drift_initial'] = grp['sensor_2_lpc_temp'] - grp['sensor_2_lpc_temp'].iloc[0]
    grp['s3_drift_initial'] = grp['sensor_3_hpc_temp'] - grp['sensor_3_hpc_temp'].iloc[0]
    grp['s4_drift_initial'] = grp['sensor_4_lpt_temp'] - grp['sensor_4_lpt_temp'].iloc[0]
    grp['s7_drift_initial'] = grp['sensor_7_hpc_pressure'] - grp['sensor_7_hpc_pressure'].iloc[0]
    grp['s11_drift_initial'] = grp['sensor_11_static_hpc_pressure'] - grp['sensor_11_static_hpc_pressure'].iloc[0]
    grp['s12_drift_initial'] = grp['sensor_12_fuel_flow_ratio'] - grp['sensor_12_fuel_flow_ratio'].iloc[0]
    
    grp['s2_roll_mean_5'] = grp['sensor_2_lpc_temp'].rolling(5, min_periods=1).mean()
    grp['s3_roll_mean_5'] = grp['sensor_3_hpc_temp'].rolling(5, min_periods=1).mean()
    grp['s4_roll_mean_5'] = grp['sensor_4_lpt_temp'].rolling(5, min_periods=1).mean()
    grp['s7_roll_mean_5'] = grp['sensor_7_hpc_pressure'].rolling(5, min_periods=1).mean()
    grp['s8_roll_mean_5'] = grp['sensor_8_fan_speed'].rolling(5, min_periods=1).mean()
    grp['s9_roll_mean_5'] = grp['sensor_9_core_speed'].rolling(5, min_periods=1).mean()
    grp['s11_roll_mean_5'] = grp['sensor_11_static_hpc_pressure'].rolling(5, min_periods=1).mean()
    grp['s12_roll_mean_5'] = grp['sensor_12_fuel_flow_ratio'].rolling(5, min_periods=1).mean()
    grp['s15_roll_mean_5'] = grp['sensor_15_bypass_ratio'].rolling(5, min_periods=1).mean()
    
    grp['s2_roll_std_5'] = grp['sensor_2_lpc_temp'].rolling(5, min_periods=1).std(ddof=1).fillna(0.0)
    grp['s3_roll_std_5'] = grp['sensor_3_hpc_temp'].rolling(5, min_periods=1).std(ddof=1).fillna(0.0)
    grp['s4_roll_std_5'] = grp['sensor_4_lpt_temp'].rolling(5, min_periods=1).std(ddof=1).fillna(0.0)
    grp['s7_roll_std_5'] = grp['sensor_7_hpc_pressure'].rolling(5, min_periods=1).std(ddof=1).fillna(0.0)
    grp['s11_roll_std_5'] = grp['sensor_11_static_hpc_pressure'].rolling(5, min_periods=1).std(ddof=1).fillna(0.0)
    grp['s12_roll_std_5'] = grp['sensor_12_fuel_flow_ratio'].rolling(5, min_periods=1).std(ddof=1).fillna(0.0)
    
    dfs.append(grp)

test_features_df = pd.concat(dfs, ignore_index=True)
last_cycles = test_features_df.groupby('engine_id').tail(1)

FEATURE_COLUMNS = [
    'setting_1', 'setting_2', 'setting_3',
    'sensor_2_lpc_temp', 'sensor_3_hpc_temp', 'sensor_4_lpt_temp',
    'sensor_7_hpc_pressure', 'sensor_8_fan_speed', 'sensor_9_core_speed',
    'sensor_11_static_hpc_pressure', 'sensor_12_fuel_flow_ratio',
    'sensor_13_corrected_fan_speed', 'sensor_14_corrected_core_speed',
    'sensor_15_bypass_ratio', 'sensor_17_bleed_enthalpy',
    'sensor_20_hpt_coolant_bleed', 'sensor_21_lpt_coolant_bleed',
    's2_drift_initial', 's3_drift_initial', 's4_drift_initial',
    's7_drift_initial', 's11_drift_initial', 's12_drift_initial',
    's2_roll_mean_5', 's3_roll_mean_5', 's4_roll_mean_5',
    's7_roll_mean_5', 's8_roll_mean_5', 's9_roll_mean_5',
    's11_roll_mean_5', 's12_roll_mean_5', 's15_roll_mean_5',
    's2_roll_std_5', 's3_roll_std_5', 's4_roll_std_5',
    's7_roll_std_5', 's11_roll_std_5', 's12_roll_std_5'
]

m = joblib.load('models/best_rul_model.joblib')
y_pred = np.clip(m.predict(last_cycles[FEATURE_COLUMNS]), 0, 125)
y_true_raw = pd.read_csv('data/raw/RUL_FD001.txt', sep=r'\s+', header=None)[0].values
y_true_clipped = np.clip(y_true_raw, 0, 125)

d_clip = y_pred - y_true_clipped
rmse_clip = np.sqrt(np.mean(d_clip**2))
mae_clip = np.mean(np.abs(d_clip))
nasa_score_clip = np.where(d_clip < 0, np.exp(-d_clip / 13.0) - 1.0, np.exp(d_clip / 10.0) - 1.0).sum()

print('Official NASA C-MAPSS FD001 Test Benchmark (100 Engines):')
print(f'RMSE: {rmse_clip:.2f}')
print(f'MAE:  {mae_clip:.2f}')
print(f'NASA Score: {nasa_score_clip:.2f}')
