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
  station_callsign?: string
  call_sign: string
  qso_date: string
  time_on?: string
  time_off?: string
  freq?: number
  band?: string
  mode?: string
  rst_sent?: string
  rst_rcvd?: string
  grid_square?: string
  dxcc?: string
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
  qrz_url?: string
  cached: boolean
  cached_at?: string
}

export interface Statistics {
  total_qso: number
  total_dxcc: number
  total_waz: number
  qsl_sent: number
  qsl_rcvd: number
  eqsl_sent: number
  eqsl_rcvd: number
  lotw_confirmed: number
  total_distance: number
  average_distance?: number
  last_qso_date?: string
}
