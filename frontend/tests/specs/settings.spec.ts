import { test, expect, json, udpStatus, TOKEN } from '../fixtures'

test('preference save failure uses error status and retains persisted user', async ({ page, boundary }) => {
  await boundary.login(page, '/settings')
  const savedUser = await page.evaluate(() => localStorage.getItem('user'))
  await page.route('**/api/v1/auth/me', route => route.request().method() === 'PATCH'
    ? json(route, { detail: 'Preference storage unavailable' }, 503) : route.fallback())
  await page.getByRole('tab', { name: 'Preferences', exact: true }).click()
  await page.getByRole('button', { name: 'Save Settings', exact: true }).click()
  const panel = page.getByRole('tabpanel', { name: 'Preferences', exact: true })
  await expect(panel.locator('.el-alert--error')).toContainText('Preference storage unavailable')
  await expect(panel.locator('.el-alert--success')).toHaveCount(0)
  expect(await page.evaluate(() => localStorage.getItem('user'))).toBe(savedUser)
})

test('UDP settings sends the selected non-default ports with bearer authentication', async ({ page, boundary }) => {
  await boundary.login(page, '/settings')
  let received: unknown
  await page.route('**/api/v1/udp/start', async route => {
    received = route.request().postDataJSON()
    expect(route.request().headers().authorization).toBe(`Bearer ${TOKEN}`)
    await json(route, { data: { ...udpStatus, receiving: true, running: true, wsjtx_port: 32001, n1mm_port: 32002 } })
  })
  await page.getByRole('tab', { name: 'UDP Settings', exact: true }).click()
  const panel = page.getByRole('tabpanel', { name: 'UDP Settings', exact: true })
  await panel.getByRole('spinbutton').nth(0).fill('32001')
  await panel.getByRole('spinbutton').nth(1).fill('32002')
  await panel.getByRole('button', { name: 'Apply and Start', exact: true }).click()
  await expect.poll(() => received).toEqual({ wsjtx_port: 32001, n1mm_port: 32002 })
  await expect(page.locator('.el-message--success').filter({ hasText: 'Settings saved' })).toBeVisible()
})

test('UDP equal ports are visibly rejected without starting a listener', async ({ page, boundary }) => {
  await boundary.login(page, '/settings')
  await page.getByRole('tab', { name: 'UDP Settings', exact: true }).click()
  const panel = page.getByRole('tabpanel', { name: 'UDP Settings', exact: true })
  await panel.getByRole('spinbutton').nth(0).fill('33001')
  await panel.getByRole('spinbutton').nth(1).fill('33001')
  await panel.getByRole('spinbutton').nth(1).press('Tab')
  await panel.getByRole('button', { name: 'Apply and Start', exact: true }).press('Enter')
  await expect(panel.locator('.el-form-item__error')).toContainText(/port/i)
  expect(boundary.requests.filter(r => r.path === '/udp/start')).toEqual([])
})

for (const value of ['1023', '65536']) {
  test(`UDP rejects out-of-range input ${value} rather than starting with defaults`, async ({ page, boundary }) => {
    await boundary.login(page, '/settings')
    await page.getByRole('tab', { name: 'UDP Settings', exact: true }).click()
    const panel = page.getByRole('tabpanel', { name: 'UDP Settings', exact: true })
    const port = panel.getByRole('spinbutton').first()
    await port.fill(value)
    await port.press('Tab')
    await panel.getByRole('button', { name: 'Apply and Start', exact: true }).press('Enter')
    await expect(page.locator('.el-form-item__error:visible, .el-message--error:visible').first()).toContainText(/port|1024|65535|range/i)
    expect(boundary.requests.filter(r => r.path === '/udp/start')).toEqual([])
    await expect(page.locator('.el-message--success').filter({ hasText: 'Settings saved' })).toHaveCount(0)
  })
}
