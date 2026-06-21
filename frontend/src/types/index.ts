export interface User {
  id: number
  username: string
  email: string
  full_name?: string
  timezone: string
  language: string
  role: string
  is_active: boolean
  created_at: string
}

export interface Station {
  id: number
  user_id: number
  callsign: string
  created_at: string
  updated_at: string
}

export interface Location {
  id: number
  user_id: number
  station_id: number
  station_callsign?: string
  name: string
  grid_square?: string
  radio_model?: string
  antenna_model?: string
  antenna_height?: number
  qth?: string
  is_active: boolean
  created_at: string
  updated_at: string
}

export interface QSOLog {
  id: number
  user_id: number
  station_id: number
  location_id?: number
  location_name?: string
  station_callsign?: string
  call_sign: string
  qso_date: string
  qso_date_off?: string
  time_on?: string
  time_off?: string
  freq?: number
  band?: string
  mode?: string
  rst_sent?: string
  rst_rcvd?: string
  grid_square?: string
  dxcc?: string
  tx_pwr?: number
  my_gridsquare?: string
  qsl_sent: string
  qsl_rcvd: string
  comment?: string
  created_at: string
  updated_at: string
}

export interface CallsignInfo {
  call_sign: string
  first_name?: string
  last_name?: string
  full_name?: string
  country?: string
  grid_square?: string
  latitude?: number
  longitude?: number
  class_type?: string
  license_date?: string
  license_exp?: string
  previous_call?: string
  qrz_url?: string
  address?: string
  zip_code?: string
  url?: string
  phone?: string
  cq_zone?: string
  itu_zone?: string
  email?: string
  image?: string
  cached: boolean
  cached_at?: string
  offline?: boolean
}

export interface Statistics {
  total_qso: number
  total_dxcc: number
  confirmed_dxcc?: number
  total_waz: number
  qsl_sent: number
  qsl_rcvd: number
  eqsl_sent: number
  eqsl_rcvd: number
  lotw_confirmed: number
  total_distance: number
  average_distance?: number
  last_qso_date?: string
  monthly_qso?: number
  yearly_qso?: number
  confirmed_qso?: number
  station_count?: number
}

export interface BandStatEntry {
  band: string
  qso_count: number
  percentage: number
}

export interface ModeStatEntry {
  mode: string
  qso_count: number
  percentage: number
}
