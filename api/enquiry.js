/**
 * Advertisement board enquiry endpoint.
 *
 * Runs as a Vercel Edge Function and posts the enquiry to the Resend API,
 * so a brand's submission is delivered without leaving the page and without
 * routing the message through a third-party form relay.
 *
 * Required environment variable:
 *   RESEND_API_KEY   API key from https://resend.com/api-keys
 *
 * Optional environment variables:
 *   ENQUIRY_TO       Inbox that receives enquiries (defaults to the owner address)
 *   ENQUIRY_FROM     Verified sender, e.g. "Ad Board <ads@yourdomain.com>"
 */

export const config = { runtime: 'edge' };

const OWNER_EMAIL = 'chetansharmap7@gmail.com';
const RESEND_ENDPOINT = 'https://api.resend.com/emails';
const EMAIL_PATTERN = /^[^\s@]+@[^\s@]+\.[a-z]{2,}$/i;

const LIMITS = {
    brand: 60,
    email: 80,
    message: 400,
    currency: 8,
    cycle: 40,
    slotName: 80,
    slotSize: 60,
    placement: 160
};

const json = (status, body) => new Response(JSON.stringify(body), {
    status,
    headers: {
        'Content-Type': 'application/json; charset=utf-8',
        'Cache-Control': 'no-store'
    }
});

const clean = (value, max) => String(value === undefined || value === null ? '' : value)
    .split('')
    .filter((ch) => ch.charCodeAt(0) > 31 && ch.charCodeAt(0) !== 127)
    .join('')
    .trim()
    .slice(0, max);

const escapeHtml = (value) => String(value).replace(/[&<>"']/g, (c) => ({
    '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;'
}[c]));

function validate(raw) {
    const data = {
        brand: clean(raw.brand, LIMITS.brand),
        email: clean(raw.email, LIMITS.email),
        budget: clean(raw.budget, 20),
        currency: clean(raw.currency, LIMITS.currency) || 'INR',
        cycle: clean(raw.cycle, LIMITS.cycle) || 'Per month',
        message: clean(raw.message, LIMITS.message),
        slotName: clean(raw.slotName, LIMITS.slotName) || 'Portfolio Board',
        slotSize: clean(raw.slotSize, LIMITS.slotSize) || 'Not specified',
        placement: clean(raw.placement, LIMITS.placement) || 'Not specified'
    };

    if (!data.brand) return { error: 'Brand or company name is required.' };
    if (!EMAIL_PATTERN.test(data.email)) return { error: 'A valid contact email is required.' };
    if (!data.message) return { error: 'A short message is required.' };

    const budgetAmount = Number(String(data.budget).replace(/[,\s]/g, ''));
    if (!Number.isFinite(budgetAmount) || budgetAmount <= 0) {
        return { error: 'A budget offer greater than zero is required.' };
    }
    data.budget = String(Math.round(budgetAmount));

    // Honeypot: real visitors never fill a hidden field.
    if (clean(raw.company_website, 100)) return { error: 'Submission rejected.' };

    return { data };
}

function buildEmail(data) {
    const rows = [
        ['Brand / Company', data.brand],
        ['Contact Email', data.email],
        ['Budget Offer', data.budget + ' ' + data.currency + ' (' + data.cycle + ')'],
        ['Slot Requested', data.slotName],
        ['Slot Size', data.slotSize],
        ['Placement', data.placement],
        ['Message', data.message]
    ];

    const text = rows.map(([k, v]) => k + ': ' + v).join('\n') +
        '\n\nSent from the advertisement board on the portfolio site.';

    const html = `<!doctype html><html><body style="margin:0;background:#f5f7fa;padding:24px;font-family:'Segoe UI',Arial,sans-serif;color:#0f172a">
<table role="presentation" cellpadding="0" cellspacing="0" style="max-width:620px;margin:0 auto;background:#ffffff;border:1px solid #e2e8f0;border-radius:10px;overflow:hidden">
<tr><td style="padding:20px 24px;background:#0f172a;color:#ffffff">
<div style="font-size:16px;font-weight:600">New advertisement slot enquiry</div>
<div style="font-size:13px;opacity:.75;margin-top:4px">${escapeHtml(data.slotName)} &middot; ${escapeHtml(data.budget)} ${escapeHtml(data.currency)} ${escapeHtml(data.cycle.toLowerCase())}</div>
</td></tr>
<tr><td style="padding:8px 24px 20px">
<table role="presentation" cellpadding="0" cellspacing="0" width="100%" style="font-size:14px;line-height:1.6">
${rows.map(([k, v]) => `<tr>
<td style="padding:10px 0;border-bottom:1px solid #eef2f6;color:#64748b;width:150px;vertical-align:top">${escapeHtml(k)}</td>
<td style="padding:10px 0;border-bottom:1px solid #eef2f6;font-weight:500">${escapeHtml(v)}</td>
</tr>`).join('')}
</table>
<p style="margin:18px 0 0;font-size:13px;color:#64748b">Reply directly to this email to reach ${escapeHtml(data.brand)}.</p>
</td></tr></table></body></html>`;

    return { text, html };
}

export default async function handler(request) {
    if (request.method === 'OPTIONS') {
        return new Response(null, {
            status: 204,
            headers: { 'Allow': 'POST, OPTIONS' }
        });
    }

    if (request.method !== 'POST') {
        return json(405, { ok: false, error: 'Method not allowed.' });
    }

    let raw;
    try {
        raw = await request.json();
    } catch {
        return json(400, { ok: false, error: 'Expected a JSON body.' });
    }

    const { data, error } = validate(raw || {});
    if (error) return json(400, { ok: false, error });

    const apiKey = process.env.RESEND_API_KEY;
    if (!apiKey) {
        return json(503, { ok: false, error: 'Mail service is not configured yet.' });
    }

    const { text, html } = buildEmail(data);
    const subject = 'Ad enquiry: ' + data.slotName + ' — ' + data.brand +
        ' (' + data.budget + ' ' + data.currency + ' ' + data.cycle.toLowerCase() + ')';

    let upstream;
    try {
        upstream = await fetch(RESEND_ENDPOINT, {
            method: 'POST',
            headers: {
                'Authorization': 'Bearer ' + apiKey,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                from: process.env.ENQUIRY_FROM || 'Portfolio Ad Board <onboarding@resend.dev>',
                to: [process.env.ENQUIRY_TO || OWNER_EMAIL],
                reply_to: data.email,
                subject,
                text,
                html
            })
        });
    } catch {
        return json(502, { ok: false, error: 'Mail service unreachable.' });
    }

    const result = await upstream.json().catch(() => ({}));

    if (!upstream.ok) {
        return json(502, {
            ok: false,
            error: result.message || 'Mail service rejected the request.'
        });
    }

    return json(200, { ok: true, id: result.id || null });
}
