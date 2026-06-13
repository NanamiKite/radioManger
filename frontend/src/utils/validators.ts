export const validators = {
  validateCallsign(callsign: string): boolean {
    const pattern = /^[A-Z0-9]{1,3}\/[A-Z0-9]{3,10}$|^[A-Z0-9]{2,6}$|^[A-Z0-9]{1,3}\/[A-Z0-9]{1,3}\/[A-Z0-9]{1,6}$/
    return pattern.test(callsign.toUpperCase())
  },

  validateGridSquare(grid: string): boolean {
    const pattern = /^[A-R]{2}[0-9]{2}([a-x]{2})?$/
    return pattern.test(grid.toLowerCase())
  },

  validateEmail(email: string): boolean {
    const pattern = /^[^\s@]+@[^\s@]+\.[^\s@]+$/
    return pattern.test(email)
  },

  validateFrequency(freq: number, band: string): boolean {
    const bandRanges: { [key: string]: [number, number] } = {
      '160m': [1.8, 2.0],
      '80m': [3.5, 4.0],
      '40m': [7.0, 7.3],
      '20m': [14.0, 14.35],
      '15m': [21.0, 21.45],
      '10m': [28.0, 29.7],
      '6m': [50.0, 54.0],
      '2m': [144.0, 148.0],
      '70cm': [420.0, 450.0]
    }

    if (!bandRanges[band]) return false
    const [min, max] = bandRanges[band]
    return freq >= min && freq <= max
  }
}
