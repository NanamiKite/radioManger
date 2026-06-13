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
  grid_square: string
  radio_model?: string
  antenna_model?: string
  qth?: string
  is_primary: boolean
  created_at: string
  updated_at: string
}

export interface QSOLog {
  id: number
  user_id: number
  station_id: number
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
  qsl_sent: string
  qsl_rcvd: string
  comment?: string
  created_at: string
  updated_at: string
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
}
