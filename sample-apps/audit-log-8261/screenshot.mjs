// Log in to the local dashboard as the demo admin and screenshot the
// organisation audit log (served by the #8261 frontend + API).
import { chromium } from 'playwright'
import fs from 'fs'
const cfg = JSON.parse(fs.readFileSync(new URL('./setup.json', import.meta.url)))
const out = new URL('./screenshots/', import.meta.url).pathname
const browser = await chromium.launch()
const page = await browser.newPage({ viewport: { width: 1400, height: 900 } })
await page.goto('http://localhost:8080/login')
await page.fill('[name="email"]', cfg.login[0])
await page.fill('[name="password"]', cfg.login[1])
await page.click('#login-btn')
await page.waitForURL(u => u.pathname.includes('/organisation/') || u.pathname.includes('/create'), { timeout: 60000 })
await page.goto(`http://localhost:8080/project/${cfg.project_id}/audit-log`)
await page.waitForSelector('text=terraform_flag', { timeout: 60000 })
await page.waitForTimeout(1500)
await page.screenshot({ path: out + 'audit-log-fixed.png', fullPage: false })
console.log('saved', out + 'audit-log-fixed.png')
await browser.close()
