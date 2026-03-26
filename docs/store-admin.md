# Store Admin Notes

## Catalog editing
- Update [`data/products.json`](/Users/michaelferranti/Documents/code%20/projectile.now/data/products.json) to add or edit products.
- Each product controls title, description, images, options, and variants.
- Each variant controls its own `priceCents`, `available` flag, option combination, and optional `stripePriceId`.
- Set `active` to `false` to hide a product without deleting it.

## Images
- Prefer storing images in [`assets/`](/Users/michaelferranti/Documents/code%20/projectile.now/assets).
- Use relative paths like `assets/example.jpg` in the catalog.
- If you later move to a CDN, replace the image values with full `https://...` URLs.

## Netlify and Stripe environment variables
- `STRIPE_SECRET_KEY`
- `STRIPE_WEBHOOK_SECRET`
- `ALLOWED_SHIPPING_COUNTRIES=US,CA`
- `DEFAULT_STANDARD_SHIPPING_CENTS=700`
- `DEFAULT_STANDARD_SHIPPING_LABEL=Standard Shipping`
- `STRIPE_SHIPPING_RATE_STANDARD`
- `STRIPE_SHIPPING_RATE_EXPEDITED`

## Order alerts
- The webhook can send an email alert after `checkout.session.completed`.
- The same webhook posts an order record to the Netlify form named `order-record`.
- For now, email alerts are optional and safely skipped if Resend is not configured.
- To re-enable them later, add:
  - `RESEND_API_KEY`
  - `ORDER_FROM_EMAIL`
  - `ORDER_ALERT_EMAIL`
- Current intended order alert destination: `projectile.now@gmail.com`.

## Current content assumptions
- Production site URL should be `https://projectile.now`.
- Shipping is currently configured for `US,CA`.
- Default checkout shipping is currently `$7` with no expedited option.

## Local development
- Run `npm install`
- Run `netlify dev`
- Open `http://localhost:8888/shop.html`
