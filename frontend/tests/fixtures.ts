import { test as base, expect, type Page, type Route, type WebSocketRoute } from '@playwright/test'

export const TOKEN = 'contract.jwt.never-in-url'
const timestamp = '2026-01-02T03:04:05Z'
export const station = { id: 11, user_id: 7, callsign: 'BA1TEST', created_at: timestamp, updated_at: timestamp }
export const location = { id: 21, user_id: 7, station_id: 11, station_callsign: 'BA1TEST', name: 'Home', grid_square: 'OM89AA', is_active: true, created_at: timestamp, updated_at: timestamp }
export const udpStatus = { running: false, receiving: false, wsjtx_port: 2237, n1mm_port: 12060, qso_count: 0, last_qso: null, ws_clients: 0 }
export const node = { host: 'loopback.invalid', port: 7300, name: 'Contract node', country: 'Test', remark: 'Network mocked' }
export const clusterStatus = { connected: false, connecting: false, current_node: null, callsign: 'BA1TEST', spot_count: 0, uptime_seconds: null }
export const emptyLogs = { items: [], total: 0, page: 1, page_size: 20, pages: 0 }
export const json = (route: Route, body: unknown, status = 200) => route.fulfill({ status, contentType: 'application/json', body: JSON.stringify(body) })

export class Boundary {
  mode: 'sqlite' | 'mysql' | 'unknown' = 'sqlite'
  role = 'user'
  requests: { path: string; method: string; body: unknown; authorization: string | undefined }[] = []
  sockets: WebSocketRoute[] = []
  socketMessages: { url: string; message: string }[] = []
  user() { return { id: 7, username: 'contract-user', email: 'contract@example.invalid', language: 'en-US', timezone: 'UTC', role: this.role, is_active: true, created_at: timestamp } }
  async install(page: Page) {
    await page.routeWebSocket(/\/api\/v1\/.*\/ws(?:\?.*)?$/, ws => {
      this.sockets.push(ws)
      ws.onMessage(message => this.socketMessages.push({ url: ws.url(), message: String(message) }))
    })
    await page.route('**/health', route => this.mode === 'unknown' ? json(route, { status: 'degraded', detail: 'Database unavailable' }, 503) : json(route, { status: 'ok', database: this.mode, version: 'contract' }))
    await page.route('**/api/v1/**', async route => {
      const request = route.request()
      const path = new URL(request.url()).pathname.replace('/api/v1', '')
      this.requests.push({ path, method: request.method(), body: request.headers()['content-type']?.includes('application/json') ? request.postDataJSON() : request.postData(), authorization: request.headers().authorization })
      const responses: Record<string, unknown> = {
        '/auth/login': { access_token: TOKEN, token_type: 'bearer', expires_in: 3600, user: this.user() },
        '/auth/me': this.user(), '/auth/logout': { message: 'Logged out' },
        '/stations': [station], '/locations': [location], '/locations/active/current': location,
        '/logs': emptyLogs,
        '/stats/overview': { data: { total_qso: 0, total_dxcc: 0, confirmed_dxcc: 0, total_waz: 0, qsl_sent: 0, qsl_rcvd: 0, eqsl_sent: 0, eqsl_rcvd: 0, lotw_confirmed: 0, total_distance: 0, average_distance: 0, monthly_qso: 0, yearly_qso: 0, confirmed_qso: 0, station_count: 1 } },
        '/stats/band-mode': { data: { bands: [], modes: [] } },
        '/stats/dxcc': { data: { total_dxcc: 0, dxcc_list: [] } },
        '/stats/dxcc-chart': { data: { bands: [], entities: [], band_confirmed: {}, band_worked: {}, total_entities: 0 } },
        '/stats/band-mode-matrix': { data: [] },
        '/udp/status': { data: udpStatus }, '/udp/start': { data: { ...udpStatus, running: true, receiving: true } },
        '/dxcluster/nodes': [node], '/dxcluster/status': clusterStatus, '/dxcluster/spots': [],
        '/dxcluster/connect': { success: true, message: 'Connected', status: { ...clusterStatus, connected: true, current_node: node } },
      }
      if (Object.hasOwn(responses, path)) await json(route, responses[path])
      else await json(route, { detail: `Unconfigured test API: ${request.method()} ${path}` }, 501)
    })
  }
  async login(page: Page, destination = '/logs') {
    await page.goto(`/login?redirect=${encodeURIComponent(destination)}`)
    await page.getByPlaceholder('Username', { exact: true }).fill('contract-user')
    await page.getByPlaceholder('Password', { exact: true }).fill('correct-password')
    await page.getByRole('button', { name: 'Login', exact: true }).click()
    await expect(page).toHaveURL(new RegExp(destination.split('?')[0] + '(?:\\?.*)?$'))
    await expect(page.locator('.user-btn')).toContainText('contract-user')
  }
}

export const test = base.extend<{ boundary: Boundary }>({
  boundary: async ({ page }, use) => {
    const boundary = new Boundary()
    await boundary.install(page)
    await use(boundary)
  },
})
export { expect }
