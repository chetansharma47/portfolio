/**
 * Endpoint tests for api/enquiry.js.
 * Runs the handler with a stubbed fetch, so no mail is sent.
 *   node api/enquiry.test.js
 */

import assert from 'node:assert/strict';
import handler from './enquiry.js';

const post = (body) => new Request('https://example.com/api/enquiry', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: typeof body === 'string' ? body : JSON.stringify(body)
});

const valid = {
    brand: 'Acme Cloud',
    email: 'ads@acme.com',
    budget: '25000',
    currency: 'INR',
    cycle: 'Per month',
    message: 'Q1 campaign, static banner, link to acme.com',
    slotName: 'Panel B',
    slotSize: '468 x 200',
    placement: 'Right board panel, upper row'
};

let sent = null;
const stubFetch = (url, options) => {
    sent = { url, options, body: JSON.parse(options.body) };
    return Promise.resolve(new Response(JSON.stringify({ id: 'msg_test_123' }), {
        status: 200, headers: { 'Content-Type': 'application/json' }
    }));
};

async function run() {
    process.env.RESEND_API_KEY = 'test-key';
    process.env.ENQUIRY_TO = 'owner@example.com';
    globalThis.fetch = stubFetch;

    // Rejects anything but POST
    let res = await handler(new Request('https://example.com/api/enquiry'));
    assert.equal(res.status, 405);

    // Rejects malformed JSON
    res = await handler(post('not json'));
    assert.equal(res.status, 400);

    // Validation
    const cases = [
        [{ ...valid, brand: '' }, 'brand'],
        [{ ...valid, email: 'nope' }, 'email'],
        [{ ...valid, budget: '0' }, 'zero budget'],
        [{ ...valid, budget: 'free' }, 'non-numeric budget'],
        [{ ...valid, message: '' }, 'message'],
        [{ ...valid, company_website: 'bot.example' }, 'honeypot']
    ];
    for (const [body, label] of cases) {
        res = await handler(post(body));
        assert.equal(res.status, 400, 'expected 400 for ' + label);
        assert.equal((await res.json()).ok, false);
    }

    // Happy path
    sent = null;
    res = await handler(post(valid));
    const json = await res.json();
    assert.equal(res.status, 200);
    assert.deepEqual(json, { ok: true, id: 'msg_test_123' });
    assert.equal(sent.url, 'https://api.resend.com/emails');
    assert.equal(sent.options.headers.Authorization, 'Bearer test-key');
    assert.deepEqual(sent.body.to, ['owner@example.com']);
    assert.equal(sent.body.reply_to, 'ads@acme.com');
    assert.match(sent.body.subject, /Panel B/);
    assert.match(sent.body.subject, /25000 INR per month/);
    assert.match(sent.body.text, /Budget Offer: 25000 INR \(Per month\)/);
    assert.match(sent.body.html, /Acme Cloud/);

    // Escapes HTML in the creative fields
    sent = null;
    await handler(post({ ...valid, brand: '<script>alert(1)</script>' }));
    assert.ok(!sent.body.html.includes('<script>'));
    assert.match(sent.body.html, /&lt;script&gt;/);

    // Surfaces upstream failure
    globalThis.fetch = () => Promise.resolve(new Response(
        JSON.stringify({ message: 'API key is invalid' }),
        { status: 401, headers: { 'Content-Type': 'application/json' } }
    ));
    res = await handler(post(valid));
    assert.equal(res.status, 502);
    assert.match((await res.json()).error, /API key is invalid/);

    // Reports missing configuration
    globalThis.fetch = stubFetch;
    delete process.env.RESEND_API_KEY;
    res = await handler(post(valid));
    assert.equal(res.status, 503);
    assert.match((await res.json()).error, /not configured/);

    console.log('api/enquiry.js — all checks passed');
}

run().catch((err) => {
    console.error(err);
    process.exit(1);
});
