import { test, expect, json, TOKEN } from '../fixtures'

test('business 401 clears local auth without issuing recursive logout', async ({ page, boundary }) => {
  await boundary.login(page)
  let logoutCalls = 0
  await page.route('**/api/v1/auth/logout', async route => { logoutCalls++; await json(route, { detail: 'Expired' }, 401) })
  await page.route('**/api/v1/stations', route => json(route, { detail: 'Expired' }, 401))
  await page.goto('/stations')
  await expect(page).toHaveURL(/\/login/)
  expect(await page.evaluate(() => [localStorage.getItem('token'), localStorage.getItem('user')])).toEqual([null, null])
  expect(logoutCalls).toBe(0)
})

test('explicit logout transport failure is visible and preserves local session', async ({ page, boundary }) => {
  await boundary.login(page)
  let logoutCalls = 0
  await page.route('**/api/v1/auth/logout', async route => { logoutCalls++; await route.abort('connectionfailed') })
  await page.locator('.user-btn').hover()
  await page.getByRole('menuitem', { name: 'Logout', exact: true }).click()
  await expect(page.locator('.el-message--error')).toBeVisible()
  await expect(page.locator('.user-btn')).toContainText('contract-user')
  expect(await page.evaluate(() => localStorage.getItem('token'))).toBe(TOKEN)
  await expect(page).toHaveURL(/\/logs$/)
  expect(logoutCalls).toBe(1)
})

for (const mode of ['unknown', 'mysql'] as const) {
  test(`${mode} regular user has no host controls but receives shared DX spots`, async ({ page, boundary }) => {
    boundary.mode = mode
    await boundary.login(page, '/settings')
    await expect(page.getByRole('tab', { name: 'UDP Settings', exact: true })).toHaveCount(0)
    await page.getByRole('menuitem', { name: 'QSO Logs', exact: true }).click()
    await expect(page.getByRole('button', { name: /UDP/ })).toHaveCount(0)
    await page.getByRole('menuitem', { name: 'DX Spots', exact: true }).click()
    await expect(page.getByRole('button', { name: 'Connect', exact: true })).toHaveCount(0)
    await expect(page.getByRole('button', { name: 'Disconnect', exact: true })).toHaveCount(0)
    await expect(page.getByPlaceholder('Select Node')).toHaveCount(0)
    if (mode === 'mysql') await expect(page.getByText('Read only', { exact: true })).toBeVisible()
    await expect.poll(() => boundary.socketMessages.length).toBe(1)
    const first = boundary.socketMessages[0]
    expect(new URL(first.url).search).toBe('')
    expect(first.url).not.toContain(TOKEN)
    expect(JSON.parse(first.message)).toEqual({ token: TOKEN })
    boundary.sockets[0].send(JSON.stringify({ type: 'spot', data: { spotter: 'W1AW', freq: 14074, dx_callsign: 'JA1CONTRACT', mode: 'FT8', comment: 'Shared spot', time_utc: '03:04', band: '20m', received_at: '2026-01-02T03:04:05Z' } }))
    await expect(page.getByText('JA1CONTRACT', { exact: true })).toBeVisible()
    expect(boundary.requests.filter(r => ['/dxcluster/connect', '/dxcluster/disconnect', '/udp/start', '/udp/stop'].includes(r.path))).toEqual([])
  })
}

test('MySQL admin can operate DX and access UDP settings', async ({ page, boundary }) => {
  boundary.mode = 'mysql'; boundary.role = 'admin'
  await boundary.login(page, '/settings')
  await expect(page.getByRole('tab', { name: 'UDP Settings', exact: true })).toBeVisible()
  await page.getByRole('menuitem', { name: 'DX Spots', exact: true }).click()
  await page.getByRole('button', { name: 'Connect', exact: true }).click()
  await expect.poll(() => boundary.requests.filter(r => r.path === '/dxcluster/connect')).toHaveLength(1)
  expect(boundary.requests.find(r => r.path === '/dxcluster/connect')?.body).toEqual({ node_host: 'loopback.invalid', node_port: 7300 })
  await expect(page.getByRole('button', { name: 'Disconnect', exact: true })).toBeVisible()
})

for (const channel of ['dxcluster', 'udp'] as const) {
  test(`${channel} websocket authenticates in first message and 4401 clears auth`, async ({ page, boundary }) => {
    await boundary.login(page, channel === 'dxcluster' ? '/dxclusters' : '/logs')
    if (channel === 'udp') await page.getByRole('button', { name: /UDP/ }).click()
    await expect.poll(() => boundary.socketMessages.length).toBe(1)
    expect(boundary.socketMessages[0].url).toMatch(new RegExp(`/api/v1/${channel}/ws$`))
    expect(new URL(boundary.socketMessages[0].url).search).toBe('')
    expect(JSON.parse(boundary.socketMessages[0].message)).toEqual({ token: TOKEN })
    boundary.sockets[0].close({ code: 4401, reason: 'Session revoked' })
    await expect(page).toHaveURL(/\/login/)
    expect(await page.evaluate(() => [localStorage.getItem('token'), localStorage.getItem('user')])).toEqual([null, null])
    expect(boundary.requests.filter(r => r.path === '/auth/logout')).toEqual([])
  })
}
