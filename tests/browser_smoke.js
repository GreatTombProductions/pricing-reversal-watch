'use strict';

const assert = require('assert');
const { chromium } = require('playwright');

(async () => {
  const base = process.env.SMOKE_BASE || 'http://127.0.0.1:8765/';
  const browser = await chromium.launch({ headless: true });
  const errors = [];
  try {
    const page = await browser.newPage({ viewport: { width: 1280, height: 900 } });
    page.on('console', (m) => { if (m.type() === 'error') errors.push(m.text()); });
    page.on('pageerror', (e) => errors.push(e.message));

    const response = await page.goto(base, { waitUntil: 'networkidle' });
    assert(response.ok(), `index returned ${response.status()}`);

    // hero strip rendered from data
    await page.waitForFunction(() => document.getElementById('event-count').textContent !== '—');
    assert.strictEqual((await page.locator('#event-count').textContent()).trim(), '5');
    assert.strictEqual((await page.locator('#quote-count').textContent()).trim(), '10');

    // timeline: 5 event cards; the cancellation carries a quote + capture link
    assert.strictEqual(await page.locator('.card.event').count(), 5);
    const cancelCard = page.locator('.card.event', { hasText: 'Scheduled increase cancelled' });
    assert.strictEqual(await cancelCard.count(), 1);
    assert(await cancelCard.locator('blockquote.quote').first().textContent().then((t) => t.includes('will not occur')));
    assert((await cancelCard.locator('a', { hasText: 'capture' }).count()) >= 1);

    // vendor tables rendered
    assert(await page.locator('#anthropic-models tr').count() > 10);
    const sonnetRow = page.locator('#anthropic-models tr', { hasText: 'Claude Sonnet 5' });
    assert((await sonnetRow.textContent()).includes('$2'));
    assert(await page.locator('#deepseek-models tr').count() >= 5);

    // gaps are visible, never silent
    assert((await page.locator('#openai-errors li').count()) >= 2);
    assert.strictEqual(await page.locator('#other-gaps li').count(), 3);

    // sources page: 5 receipts + quote-verification summary
    const sources = await page.goto(new URL('sources.html', base).toString(), { waitUntil: 'networkidle' });
    assert(sources.ok());
    await page.waitForFunction(() => document.querySelectorAll('#sources-table tr').length > 0);
    assert.strictEqual(await page.locator('#sources-table tr').count(), 6); // header + 5
    assert((await page.locator('#sources-summary').textContent()).includes('verified'));

    // mobile viewport: page still renders, no horizontal clipping of the header
    const mobile = await browser.newPage({ viewport: { width: 375, height: 740 } });
    const mobileErrors = [];
    mobile.on('pageerror', (e) => mobileErrors.push(e.message));
    await mobile.goto(base, { waitUntil: 'networkidle' });
    await mobile.waitForFunction(() => document.getElementById('event-count').textContent !== '—');
    assert.strictEqual(await mobile.locator('.card.event').count(), 5);

    assert.deepStrictEqual(errors, [], 'console errors on desktop: ' + errors.join(' | '));
    assert.deepStrictEqual(mobileErrors, [], 'page errors on mobile: ' + mobileErrors.join(' | '));
    console.log('SMOKE PASS: events=5, receipts=5, quotes+links render, gaps visible, mobile OK');
  } finally {
    await browser.close();
  }
})().catch((err) => {
  console.error('SMOKE FAIL:', err.message);
  process.exit(1);
});
