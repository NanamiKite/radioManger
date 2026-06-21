/**
 * Maidenhead Grid Square utilities
 * Ported from backend GridUtils.to_lat_lon() — ARRL standard
 */

/** 4位网格中心点经纬度 */
export function gridToLatLon(grid: string): [number, number] | null {
  const g = grid.toUpperCase().trim()
  if (g.length < 4) return null
  if (!/^[A-R][A-R]\d\d/.test(g)) return null

  const lon = (g.charCodeAt(0) - 65) * 20 - 180 + parseInt(g[2]) * 2 + 1
  const lat = (g.charCodeAt(1) - 65) * 10 - 90 + parseInt(g[3]) + 0.5
  return [lat, lon]
}

/** 4位网格边界 [[south, west], [north, east]] */
export function gridBounds(grid: string): [[number, number], [number, number]] | null {
  const center = gridToLatLon(grid)
  if (!center) return null
  const [lat, lon] = center
  return [[lat - 0.5, lon - 1], [lat + 0.5, lon + 1]]
}
