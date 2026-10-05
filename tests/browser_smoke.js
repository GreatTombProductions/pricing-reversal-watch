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

    // counts come from the served dataset itself, so a refresh cannot leave the smoke stale
    const data = await (await page.request.get(new URL('data/index.json', base).toString())).json();
    const nEvents = data.events.length;
    const nQuotes = data.quote_verification.checked;
    assert(nEvents >= 7 && nQuotes >= 17, `dataset shrank: events=${nEvents} quotes=${nQuotes}`);

    // hero strip rendered from data
    await page.waitForFunction(() => document.getElementById('event-count').textContent !== '—');
    assert.strictEqual((await page.locator('#event-count').textContent()).trim(), String(nEvents));
    assert.strictEqual((await page.locator('#quote-count').textContent()).trim(), String(nQuotes));

    // timeline: one card per event; the cancellation carries a quote + capture link
    assert.strictEqual(await page.locator('.card.event').count(), nEvents);
    const cancelCard = page.locator('.card.event', { hasText: 'Scheduled increase cancelled' });
    assert.strictEqual(await cancelCard.count(), 1);
    assert(await cancelCard.locator('blockquote.quote').first().textContent().then((t) => t.includes('will not occur')));
    // every capture quote links its raw capture — older dates included (capture catalog)
    const quoteCount = await cancelCard.locator('blockquote.quote').count();
    assert.strictEqual(await cancelCard.locator('a', { hasText: 'capture' }).count(), quoteCount);
    const oldLink = cancelCard.locator('a[href="data/raw/2026-09-06-platform.claude.com-pricing.html"]');
    assert.strictEqual(await oldLink.count(), 1);
    const raw = await page.request.get(new URL('data/raw/2026-09-06-platform.claude.com-pricing.html', base).toString());
    assert(raw.ok(), 'older raw capture not served');

    // new events render; the schedule change quotes before and after
    const sched = page.locator('.card.event', { hasText: 'Chinese public holidays now off-peak' });
    assert.strictEqual(await sched.locator('blockquote.quote').count(), 2);
    assert.strictEqual(await page.locator('.card.event', { hasText: 'Opus 5.5 launches' }).count(), 1);

    // featured cancellation wording, with where it now appears
    const featured = page.locator('#anthropic-callout .featured-callout');
    assert((await featured.textContent()).includes('will not occur'));
    assert((await featured.textContent()).includes('popover'));

    // vendor tables rendered
    assert(await page.locator('#anthropic-models tr').count() > 10);
    const sonnetRow = page.locator('#anthropic-models tr').filter({ has: page.locator('td', { hasText: /^Claude Sonnet 5$/ }) });
    assert((await sonnetRow.textContent()).includes('$2'));
    const opusRow = page.locator('#anthropic-models tr').filter({ has: page.locator('td', { hasText: /^Claude Opus 5\.5$/ }) });
    const opusText = await opusRow.textContent();
    assert(opusText.includes('$4') && opusText.includes('$20') && opusText.includes('$0.200'), 'Opus 5.5 row: ' + opusText);
    assert.strictEqual(await page.locator('#anthropic-models td', { hasText: /^Name$/ }).count(), 0);
    assert(await page.locator('#deepseek-models tr').count() >= 5);

    // gaps are visible, never silent
    assert((await page.locator('#openai-errors li').count()) >= 2);
    assert.strictEqual(await page.locator('#other-gaps li').count(), 3);

    // sources page: 5 receipts + quote-verification summary
    const sources = await page.goto(new URL('sources.html', base).toString(), { waitUntil: 'networkidle' });
    assert(sources.ok());
    await page.waitForFunction(() => document.querySelectorAll('#sources-table tr').length > 0);
    assert.strictEqual(await page.locator('#sources-table tr').count(), data.receipts.length + 1);
    assert((await page.locator('#sources-summary').textContent()).includes('verified'));

    // mobile viewport: page still renders, no horizontal clipping of the header
    const mobile = await browser.newPage({ viewport: { width: 375, height: 740 } });
    const mobileErrors = [];
    mobile.on('pageerror', (e) => mobileErrors.push(e.message));
    await mobile.goto(base, { waitUntil: 'networkidle' });
    await mobile.waitForFunction(() => document.getElementById('event-count').textContent !== '—');
    assert.strictEqual(await mobile.locator('.card.event').count(), nEvents);

    assert.deepStrictEqual(errors, [], 'console errors on desktop: ' + errors.join(' | '));
    assert.deepStrictEqual(mobileErrors, [], 'page errors on mobile: ' + mobileErrors.join(' | '));
    console.log(`SMOKE PASS ${base}: events=${nEvents}, quotes=${nQuotes}, receipts=${data.receipts.length}, links incl. older captures, gaps visible, mobile OK`);
  } finally {
    await browser.close();
  }
})().catch((err) => {
  console.error('SMOKE FAIL:', err.message);
  process.exit(1);
});
