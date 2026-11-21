import { test, expect, json, TOKEN } from '../fixtures'

for (const [status, detail] of [[422, 'Only ADI/ADIF files are accepted'], [404, 'Station not found']] as const) {
  test(`import ${status} shows reason without fabricated zero-success statistics`, async ({ page, boundary }) => {
    await boundary.login(page)
    await page.route('**/api/v1/logs/import*', route => json(route, { detail }, status))
    await page.getByRole('button', { name: 'Import', exact: true }).click()
    const dialog = page.getByRole('dialog', { name: 'Import Logs' })
    await dialog.locator('input[type=file]').setInputFiles({ name: 'contract.adi', mimeType: 'text/plain', buffer: Buffer.from('<EOH><CALL:5>W1AWX<EOR>') })
    await dialog.getByRole('button', { name: 'Import', exact: true }).click()
    await expect(page.locator('.el-message--error').filter({ hasText: detail }).first()).toBeVisible()
    await expect(dialog).not.toContainText('Imported:')
    await expect(dialog).not.toContainText('Duplicates:')
    await expect(dialog.locator('.el-alert--success')).toHaveCount(0)
    await expect(page.locator('.el-message--success').filter({ hasText: /Imported.*records/ })).toHaveCount(0)
  })
}

test('503 partial import displays committed counts, original record error and rollback explanation', async ({ page, boundary }) => {
  await boundary.login(page)
  await page.route('**/api/v1/logs/import*', route => json(route, {
    status: 'partial', database_failed: true, imported: 7, duplicates: 2, updated: 3, skipped: 1,
    errors: [{ line: 14, error: 'Database unavailable; current batch rolled back' }],
  }, 503))
  await page.getByRole('button', { name: 'Import', exact: true }).click()
  const dialog = page.getByRole('dialog', { name: 'Import Logs' })
  await dialog.locator('input[type=file]').setInputFiles({ name: 'partial.adi', mimeType: 'text/plain', buffer: Buffer.from('<EOH><CALL:5>W1AWX<EOR>') })
  await dialog.getByRole('button', { name: 'Import', exact: true }).click()
  await expect(dialog).toContainText('Imported: 7 | Duplicates: 2 | QSL Updated: 3 | Errors: 1')
  await expect(dialog.locator('.el-alert--error')).toContainText('Saved records remain')
  await expect(dialog.getByRole('row').filter({ hasText: 'current batch rolled back' })).toContainText('14')
  await expect(dialog.getByRole('button', { name: 'Import', exact: true })).toBeDisabled()
})

for (const outcome of ['failure', 'success'] as const) {
  test(`export stays loading until response and ${outcome === 'failure' ? 'retains dialog on failure' : 'downloads before closing'}`, async ({ page, boundary }) => {
    await boundary.login(page)
    const { promise: pending, resolve: release } = Promise.withResolvers<void>()
    let requested = false
    await page.route('**/api/v1/logs/export*', async route => {
      requested = true
      expect(route.request().headers().authorization).toBe(`Bearer ${TOKEN}`)
      await pending
      if (outcome === 'failure') await json(route, { detail: 'Export database unavailable' }, 503)
      else await route.fulfill({ status: 200, contentType: 'application/octet-stream', headers: { 'Content-Disposition': 'attachment; filename="contract.adi"' }, body: '<EOH><CALL:4>W1AW<EOR>' })
    })
    await page.getByRole('button', { name: 'Export', exact: true }).click()
    const dialog = page.getByRole('dialog', { name: 'Export Logs' })
    const button = dialog.getByRole('button', { name: 'Export', exact: true })
    const downloaded = outcome === 'success' ? page.waitForEvent('download') : null
    await button.click()
    try {
      await expect.poll(() => requested).toBe(true)
      await expect(dialog).toBeVisible()
      await expect(button).toHaveClass(/is-loading/)
    } finally { release() }
    if (outcome === 'failure') {
      await expect(page.locator('.el-message--error')).toContainText('Export database unavailable')
      await expect(dialog).toBeVisible()
      await expect(button).not.toHaveClass(/is-loading/)
    } else {
      const download = await downloaded!
      expect(download.suggestedFilename()).toBe('contract.adi')
      expect(await download.failure()).toBeNull()
      await expect(dialog).not.toBeVisible()
    }
  })
}

test('server validation errors are readable and repeated messages are merged', async ({ page, boundary }) => {
  await boundary.login(page)
  await page.route('**/api/v1/logs', route => route.request().method() === 'POST'
    ? json(route, { detail: [
      { type: 'value_error', loc: ['body', 'call_sign'], msg: 'Call sign is invalid', input: '?' },
      { type: 'value_error', loc: ['body', 'call_sign'], msg: 'Call sign is invalid', input: '?' },
      { type: 'value_error', loc: ['body', 'band'], msg: 'Band is unsupported', input: '20m' },
    ] }, 422) : route.fallback())
  await page.getByRole('button', { name: 'New Log', exact: true }).click()
  const dialog = page.getByRole('dialog', { name: 'New Log' })
  await dialog.getByPlaceholder('Call Sign', { exact: true }).fill('INVALID')
  await dialog.getByRole('button', { name: 'Submit', exact: true }).click()
  const errors = page.locator('.el-message--error')
  await expect(errors.first()).toBeVisible()
  await expect.poll(async () => (await errors.allTextContents()).join('\n')).toContain('Call sign is invalid')
  const text = (await errors.allTextContents()).join('\n')
  expect(text).toContain('Band is unsupported')
  expect(text.match(/Call sign is invalid/g)).toHaveLength(1)
  expect(text).not.toMatch(/\[object Object\]|"loc"|"input"/)
  await expect(dialog).toBeVisible()
})

test('URL grid, DXCC and band filters reach the log API', async ({ page, boundary }) => {
  await boundary.login(page, '/logs?grid=om89&dxcc=Japan&band=20m')
  await expect.poll(() => boundary.requests.filter(r => r.path === '/logs').length).toBeGreaterThan(0)
  // Observe the actual external request, not store internals.
  const request = page.waitForRequest(req => {
    const url = new URL(req.url())
    return url.pathname === '/api/v1/logs' && url.searchParams.get('grid_square') === 'OM89'
  })
  await page.getByRole('button', { name: 'Search', exact: true }).click()
  const url = new URL((await request).url())
  expect(url.searchParams.get('grid_square')).toBe('OM89')
  expect(url.searchParams.get('dxcc')).toBe('Japan')
  expect(url.searchParams.get('band')).toBe('20m')
  expect(url.searchParams.get('station_id')).toBe('11')
})

test('older log filter response cannot overwrite the newer search result', async ({ page, boundary }) => {
  await boundary.login(page)
  await expect(page.locator('.table-card .el-loading-mask')).toHaveCount(0)
  const { promise: olderGate, resolve: releaseOlder } = Promise.withResolvers<void>()
  let olderRequested = false
  let olderFulfilled = false
  const row = (call_sign: string, id: number) => ({
    id, station_id: 11, location_id: 21, user_id: 7, call_sign,
    qso_date: '2026-01-02', time_on: '03:04:05', band: '20m', mode: 'FT8',
    freq: 14.074, qsl_sent: 'N', qsl_rcvd: 'N', lotw_qsl_rcvd: 'N',
    created_at: '2026-01-02T03:04:05Z', updated_at: '2026-01-02T03:04:05Z',
  })
  await page.route('**/api/v1/logs?**', async route => {
    const filter = new URL(route.request().url()).searchParams.get('call_sign')
    if (filter === 'OLDER') {
      olderRequested = true
      await olderGate
      await json(route, { items: [row('OLDER', 101)], total: 1, page: 1, page_size: 20, pages: 1 })
      olderFulfilled = true
    } else if (filter === 'NEWER') {
      await json(route, { items: [row('NEWER', 102)], total: 1, page: 1, page_size: 20, pages: 1 })
    } else await route.fallback()
  })
  const search = page.getByRole('button', { name: 'Search', exact: true })
  await page.getByPlaceholder('Call Sign', { exact: true }).fill('OLDER')
  await search.click()
  try {
    await expect.poll(() => olderRequested).toBe(true)
    await page.getByPlaceholder('Call Sign', { exact: true }).fill('NEWER')
    await search.click()
    await expect(page.locator('.table-card').getByText('NEWER', { exact: true })).toBeVisible()
  } finally { releaseOlder() }
  await expect.poll(() => olderFulfilled).toBe(true)
  // A fresh UI action is a browser event-loop barrier after both network responses.
  await page.getByPlaceholder('Call Sign', { exact: true }).focus()
  await page.getByPlaceholder('Call Sign', { exact: true }).press('Tab')
  await expect(page.locator('.table-card').getByText('NEWER', { exact: true })).toBeVisible()
  await expect(page.locator('.table-card').getByText('OLDER', { exact: true })).toHaveCount(0)
})
