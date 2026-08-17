# Portfolio — Chetan Sharma

Static portfolio site (no build step) with one serverless endpoint for
advertisement board enquiries.

```
index.html              markup for every section
assets/css/style.css    styles, dark + light themes
assets/js/main.js       interactions, bucket module, ad board, enquiry form
api/enquiry.js          Vercel Edge Function: sends enquiries through Resend
api/enquiry.test.js     endpoint tests (stubbed mail, sends nothing)
```

## Advertisement board enquiries

The booking form posts JSON to `/api/enquiry`. The function validates the
submission and sends the mail with the [Resend](https://resend.com) API, so the
API key stays on the server and never reaches the browser. If the request fails
for any reason, the browser falls back to opening a prefilled mail draft, so an
enquiry is never lost.

### Environment variables

| Variable | Required | Purpose |
| --- | --- | --- |
| `RESEND_API_KEY` | yes | API key from https://resend.com/api-keys |
| `ENQUIRY_TO` | no | Inbox receiving enquiries (defaults to the owner address) |
| `ENQUIRY_FROM` | no | Verified sender, e.g. `Ad Board <ads@yourdomain.com>` |

Set the same values in the Vercel dashboard under
**Project → Settings → Environment Variables**, or with the CLI:

```bash
npm i -g vercel
vercel link
vercel env add RESEND_API_KEY production
```

`onboarding@resend.dev` is usable as the sender without owning a domain, but it
can only deliver to the Resend account owner's address. After verifying a domain
in Resend, set `ENQUIRY_FROM` to an address on that domain.

Local secrets live in `.env.local` (git-ignored). See `.env.example`.

## Running locally

```bash
npm i -g vercel   # once
vercel dev        # serves the site and /api/enquiry together
```

A plain static server (`python -m http.server`) works for everything except the
enquiry endpoint, which needs the Vercel runtime.

## Analytics

Vercel Web Analytics runs through `@vercel/analytics`. The site has no bundler,
so the package's browser build is vendored at
`assets/js/vendor/vercel-analytics.js` and imported as a module from
`index.html`. Refresh the copy after upgrading the package:

```bash
npm i @vercel/analytics
npm run analytics:sync
```

Enable **Project → Analytics → Web Analytics** in Vercel, otherwise
`/_vercel/insights/script.js` returns 404 and no data is collected. Custom
events (`ad_booking_opened`, `ad_enquiry_sent`) are sent through `track()` and
require a plan that includes custom events; page views work on any plan.

## Tests

```bash
node api/enquiry.test.js
```

## Managing content

- **Bucket items** — edit `DEFAULT_BUCKET` in `assets/js/main.js`. Additions made
  through the UI are stored per browser in `localStorage`; use **Export JSON** on
  the section and paste the result into `DEFAULT_BUCKET` to publish them.
- **Ad slots** — edit `AD_SLOTS` in `assets/js/main.js`. Set a slot's `status` to
  `'booked'` and add `brand`, `tagline`, `link` and `logo` to run a campaign.
