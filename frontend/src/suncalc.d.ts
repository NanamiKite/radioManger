declare module 'suncalc' {
  interface SunPosition {
    altitude: number
    azimuth: number
  }
  export function getPosition(date: Date, lat: number, lng: number): SunPosition
}
