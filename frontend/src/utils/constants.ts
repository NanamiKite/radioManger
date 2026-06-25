/** 波段 → 默认频率映射 (MHz) */
export const BAND_FREQUENCY_MAP: Record<string, string> = {
  '2190m': '0.1375',
  '160m': '1.800',
  '80m': '3.500',
  '40m': '7.000',
  '20m': '14.000',
  '15m': '21.000',
  '10m': '28.000',
  '6m': '50.000',
  '4m': '70.000',
  '2m': '144.000',
  '70cm': '430.000',
  '23cm': '1240.000',
  '13cm': '2300.000',
  '5cm': '5760.000',
  '3cm': '10000.000',
  '1.2cm': '24000.000',
  '6mm': '47000.000',
}

/** 根据波段获取默认频率 */
export function getDefaultFrequency(band: string): string | undefined {
  return BAND_FREQUENCY_MAP[band]
}

/** 光速 (m/s) */
export const SPEED_OF_LIGHT = 299792458

/** 线材类型与缩短系数 */
export const WIRE_TYPES = [
  { label: '裸铜线 (Bare Copper)', vf: 0.95 },
  { label: 'PVC 绝缘线 (PVC Insulated)', vf: 0.66 },
  { label: 'PE 绝缘线 (PE Insulated)', vf: 0.78 },
  { label: '特氟龙绝缘线 (Teflon/PTFE)', vf: 0.84 },
  { label: '铝管 (Aluminum Tubing)', vf: 0.95 },
  { label: '铜管 (Copper Tubing)', vf: 0.95 },
  { label: '镀铜钢线 (Copper-Clad Steel)', vf: 0.90 },
  { label: '不锈钢线 (Stainless Steel)', vf: 0.92 },
  { label: '自定义 (Custom)', vf: 0.95 },
]

/** 业余波段速查 */
export const HAM_BANDS = [
  { band: '160m', freq: '1.800 – 2.000', wavelength: '166.6 – 150.0' },
  { band: '80m', freq: '3.500 – 3.800', wavelength: '85.7 – 78.9' },
  { band: '40m', freq: '7.000 – 7.300', wavelength: '42.8 – 41.1' },
  { band: '30m', freq: '10.100 – 10.150', wavelength: '29.7 – 29.5' },
  { band: '20m', freq: '14.000 – 14.350', wavelength: '21.4 – 20.9' },
  { band: '17m', freq: '18.068 – 18.168', wavelength: '16.6 – 16.5' },
  { band: '15m', freq: '21.000 – 21.450', wavelength: '14.3 – 14.0' },
  { band: '12m', freq: '24.890 – 24.990', wavelength: '12.0 – 12.0' },
  { band: '10m', freq: '28.000 – 29.700', wavelength: '10.7 – 10.1' },
  { band: '6m', freq: '50.000 – 54.000', wavelength: '6.0 – 5.6' },
  { band: '2m', freq: '144.000 – 148.000', wavelength: '2.08 – 2.03' },
]

/** 偶极天线波段速查 */
export const DIPOLE_BAND_TABLE = [
  { band: '160m', freq: '1.830', totalFt: '255.7', totalM: '77.9', legFt: '127.9' },
  { band: '80m', freq: '3.550', totalFt: '131.8', totalM: '40.2', legFt: '65.9' },
  { band: '40m', freq: '7.150', totalFt: '65.5', totalM: '20.0', legFt: '32.7' },
  { band: '30m', freq: '10.125', totalFt: '46.2', totalM: '14.1', legFt: '23.1' },
  { band: '20m', freq: '14.175', totalFt: '33.0', totalM: '10.1', legFt: '16.5' },
  { band: '17m', freq: '18.118', totalFt: '25.8', totalM: '7.9', legFt: '12.9' },
  { band: '15m', freq: '21.225', totalFt: '22.0', totalM: '6.7', legFt: '11.0' },
  { band: '12m', freq: '24.940', totalFt: '18.8', totalM: '5.7', legFt: '9.4' },
  { band: '10m', freq: '28.850', totalFt: '16.2', totalM: '4.9', legFt: '8.1' },
  { band: '6m', freq: '52.000', totalFt: '9.0', totalM: '2.7', legFt: '4.5' },
]

/** GP 垂直天线波段速查 */
export const GP_BAND_TABLE = [
  { band: '160m', freq: '1.830', vertFt: '127.9', vertM: '39.0', radFt: '127.9' },
  { band: '80m', freq: '3.550', vertFt: '65.9', vertM: '20.1', radFt: '65.9' },
  { band: '40m', freq: '7.150', vertFt: '32.7', vertM: '10.0', radFt: '32.7' },
  { band: '30m', freq: '10.125', vertFt: '23.1', vertM: '7.0', radFt: '23.1' },
  { band: '20m', freq: '14.175', vertFt: '16.5', vertM: '5.0', radFt: '16.5' },
  { band: '17m', freq: '18.118', vertFt: '12.9', vertM: '3.9', radFt: '12.9' },
  { band: '15m', freq: '21.225', vertFt: '11.0', vertM: '3.4', radFt: '11.0' },
  { band: '12m', freq: '24.940', vertFt: '9.4', vertM: '2.9', radFt: '9.4' },
  { band: '10m', freq: '28.850', vertFt: '8.1', vertM: '2.5', radFt: '8.1' },
  { band: '6m', freq: '52.000', vertFt: '4.5', vertM: '1.4', radFt: '4.5' },
]

/** SWR 参考表 */
export const SWR_REF_TABLE = [
  { swr: '1.0', refl: '0.00', rl: '∞', status: 'Ideal' },
  { swr: '1.5', refl: '4.00', rl: '14.0', status: 'Good' },
  { swr: '2.0', refl: '11.1', rl: '9.5', status: 'OK' },
  { swr: '3.0', refl: '25.0', rl: '6.0', status: 'Fair' },
  { swr: '5.0', refl: '44.4', rl: '3.5', status: 'Poor' },
  { swr: '10.0', refl: '66.9', rl: '1.7', status: 'Bad' },
]

/** AWG 线规表 */
export const AWG_TABLE = [
  { awg: 4, dia_mm: '5.19', dia_in: '0.204', ohm_km: '0.815', amps: '60' },
  { awg: 6, dia_mm: '4.11', dia_in: '0.162', ohm_km: '1.30', amps: '37' },
  { awg: 8, dia_mm: '3.26', dia_in: '0.129', ohm_km: '2.06', amps: '24' },
  { awg: 10, dia_mm: '2.59', dia_in: '0.102', ohm_km: '3.28', amps: '15' },
  { awg: 12, dia_mm: '2.05', dia_in: '0.081', ohm_km: '5.21', amps: '9.3' },
  { awg: 14, dia_mm: '1.63', dia_in: '0.064', ohm_km: '8.28', amps: '5.9' },
  { awg: 16, dia_mm: '1.29', dia_in: '0.051', ohm_km: '13.2', amps: '3.7' },
  { awg: 18, dia_mm: '1.02', dia_in: '0.040', ohm_km: '20.9', amps: '2.3' },
  { awg: 20, dia_mm: '0.81', dia_in: '0.032', ohm_km: '33.3', amps: '1.5' },
  { awg: 22, dia_mm: '0.64', dia_in: '0.025', ohm_km: '52.9', amps: '0.92' },
  { awg: 24, dia_mm: '0.51', dia_in: '0.020', ohm_km: '84.2', amps: '0.58' },
  { awg: 26, dia_mm: '0.40', dia_in: '0.016', ohm_km: '134', amps: '0.36' },
]
