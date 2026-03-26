const Stripe = require("stripe");
const { findVariantById, readCatalog } = require("./lib/catalog");

function json(statusCode, payload) {
  return {
    statusCode,
    headers: {
      "Content-Type": "application/json"
    },
    body: JSON.stringify(payload)
  };
}

function getBaseUrl(event) {
  const headers = event.headers || {};
  const host = headers["x-forwarded-host"] || headers.host;
  const proto = headers["x-forwarded-proto"] || "https";
  if (host) {
    return `${proto}://${host}`;
  }
  return process.env.URL || process.env.DEPLOY_PRIME_URL || "http://localhost:8888";
}

function buildShippingOptions() {
  const shippingOptions = [];

  if (process.env.STRIPE_SHIPPING_RATE_STANDARD) {
    shippingOptions.push({ shipping_rate: process.env.STRIPE_SHIPPING_RATE_STANDARD });
  } else {
    shippingOptions.push({
      shipping_rate_data: {
        type: "fixed_amount",
        fixed_amount: {
          amount: Number(process.env.DEFAULT_STANDARD_SHIPPING_CENTS || 700),
          currency: (process.env.STORE_CURRENCY || "usd").toLowerCase()
        },
        display_name: process.env.DEFAULT_STANDARD_SHIPPING_LABEL || "Standard Shipping",
        delivery_estimate: {
          minimum: { unit: "business_day", value: 5 },
          maximum: { unit: "business_day", value: 8 }
        }
      }
    });
  }

  if (process.env.STRIPE_SHIPPING_RATE_EXPEDITED) {
    shippingOptions.push({ shipping_rate: process.env.STRIPE_SHIPPING_RATE_EXPEDITED });
  }

  return shippingOptions;
}

exports.handler = async function handler(event) {
  if (event.httpMethod !== "POST") {
    return json(405, { error: "Method not allowed." });
  }

  if (!process.env.STRIPE_SECRET_KEY) {
    return json(500, { error: "Missing STRIPE_SECRET_KEY." });
  }

  let payload;
  try {
    payload = JSON.parse(event.body || "{}");
  } catch (error) {
    return json(400, { error: "Invalid JSON body." });
  }

  const cartItems = Array.isArray(payload.cartItems) ? payload.cartItems : [];
  if (!cartItems.length) {
    return json(400, { error: "Cart is empty." });
  }

  const catalog = readCatalog();
  const lineItems = [];
  const orderSummary = [];

  for (const item of cartItems) {
    const quantity = Number(item.quantity);
    if (!item.variantId || !Number.isInteger(quantity) || quantity < 1) {
      return json(400, { error: "Invalid cart payload." });
    }

    const match = findVariantById(catalog, item.variantId);
    if (!match || !match.product.active || !match.variant.available) {
      return json(400, { error: `Item is unavailable: ${item.variantId}` });
    }

    const currency = (match.variant.currency || catalog.collection?.currency || "USD").toLowerCase();
    const variantLabel = match.variant.label || Object.values(match.variant.options || {}).join(" / ");

    if (match.variant.stripePriceId) {
      lineItems.push({
        price: match.variant.stripePriceId,
        quantity
      });
    } else {
      lineItems.push({
        quantity,
        price_data: {
          currency,
          unit_amount: match.variant.priceCents,
          product_data: {
            name: match.product.title,
            description: variantLabel && variantLabel !== "Default Title" ? variantLabel : undefined,
            metadata: {
              productId: match.product.id,
              variantId: match.variant.id
            }
          }
        }
      });
    }

    orderSummary.push({
      productId: match.product.id,
      productTitle: match.product.title,
      variantId: match.variant.id,
      variantLabel,
      quantity,
      unitAmount: match.variant.priceCents,
      currency
    });
  }

  const stripe = new Stripe(process.env.STRIPE_SECRET_KEY);
  const baseUrl = getBaseUrl(event);

  try {
    const session = await stripe.checkout.sessions.create({
      mode: "payment",
      billing_address_collection: "auto",
      shipping_address_collection: {
        allowed_countries: (process.env.ALLOWED_SHIPPING_COUNTRIES || "US,CA").split(",").map((country) => country.trim()).filter(Boolean)
      },
      shipping_options: buildShippingOptions(),
      phone_number_collection: {
        enabled: true
      },
      automatic_tax: {
        enabled: true
      },
      allow_promotion_codes: true,
      success_url: `${baseUrl}/shop-success.html?session_id={CHECKOUT_SESSION_ID}`,
      cancel_url: `${baseUrl}/shop-cancel.html`,
      line_items: lineItems,
      metadata: {
        source: "projectile-store",
        orderSummary: JSON.stringify(orderSummary).slice(0, 500)
      }
    });

    return json(200, { url: session.url, id: session.id });
  } catch (error) {
    console.error("Stripe checkout session creation failed", {
      message: error.message,
      type: error.type,
      code: error.code,
      param: error.param
    });
    return json(500, { error: "Unable to create checkout session.", details: error.message });
  }
};
