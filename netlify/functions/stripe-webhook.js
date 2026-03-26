const Stripe = require("stripe");

function response(statusCode, body) {
  return {
    statusCode,
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body)
  };
}

async function sendOrderEmail(order) {
  if (!process.env.RESEND_API_KEY || !process.env.ORDER_ALERT_EMAIL || !process.env.ORDER_FROM_EMAIL) {
    return { skipped: true, reason: "Email environment variables not fully configured." };
  }
  const shipping = order.shipping || {};
  const addressLines = [
    shipping.name,
    shipping.address?.line1,
    shipping.address?.line2,
    [shipping.address?.city, shipping.address?.state, shipping.address?.postal_code].filter(Boolean).join(", "),
    shipping.address?.country
  ].filter(Boolean);

  const itemsHtml = (order.items || [])
    .map((item) => `<li>${item.name}${item.description ? ` (${item.description})` : ""} x ${item.quantity}</li>`)
    .join("");

  const html = `
    <h1>New Projectile order</h1>
    <p><strong>Stripe session:</strong> ${order.sessionId}</p>
    <p><strong>Customer email:</strong> ${order.customerEmail || "Unavailable"}</p>
    <p><strong>Total:</strong> ${order.total}</p>
    <p><strong>Shipping:</strong><br>${addressLines.join("<br>") || "Unavailable"}</p>
    <p><strong>Items:</strong></p>
    <ul>${itemsHtml}</ul>
  `;

  const result = await fetch("https://api.resend.com/emails", {
    method: "POST",
    headers: {
      "Authorization": `Bearer ${process.env.RESEND_API_KEY}`,
      "Content-Type": "application/json"
    },
    body: JSON.stringify({
      from: process.env.ORDER_FROM_EMAIL,
      to: [process.env.ORDER_ALERT_EMAIL],
      subject: `New Projectile order ${order.sessionId}`,
      html
    })
  });

  if (!result.ok) {
    const details = await result.text();
    throw new Error(`Resend email failed with status ${result.status}: ${details}`);
  }

  return { skipped: false };
}

async function recordOrder(order) {
  const baseUrl = process.env.URL || process.env.DEPLOY_PRIME_URL || process.env.SITE_URL;
  if (!baseUrl) {
    return { skipped: true, reason: "Missing deploy URL for Netlify form submission." };
  }

  const params = new URLSearchParams({
    "form-name": "order-record",
    sessionId: order.sessionId,
    customerEmail: order.customerEmail || "",
    amountTotal: order.total,
    shippingName: order.shipping?.name || "",
    shippingAddress: order.shippingText || "",
    items: order.itemsText
  });

  const result = await fetch(baseUrl, {
    method: "POST",
    headers: {
      "Content-Type": "application/x-www-form-urlencoded"
    },
    body: params.toString()
  });

  if (!result.ok) {
    throw new Error(`Netlify form submission failed with status ${result.status}.`);
  }

  return { skipped: false };
}

exports.handler = async function handler(event) {
  if (event.httpMethod !== "POST") {
    return response(405, { error: "Method not allowed." });
  }

  if (!process.env.STRIPE_SECRET_KEY || !process.env.STRIPE_WEBHOOK_SECRET) {
    return response(500, { error: "Missing Stripe webhook configuration." });
  }

  const stripe = new Stripe(process.env.STRIPE_SECRET_KEY);
  const signature = event.headers["stripe-signature"] || event.headers["Stripe-Signature"];
  if (!signature) {
    return response(400, { error: "Missing stripe-signature header." });
  }

  let stripeEvent;
  try {
    stripeEvent = stripe.webhooks.constructEvent(event.body, signature, process.env.STRIPE_WEBHOOK_SECRET);
  } catch (error) {
    return response(400, { error: `Webhook signature verification failed: ${error.message}` });
  }

  if (stripeEvent.type !== "checkout.session.completed") {
    return response(200, { received: true, ignored: true });
  }

  try {
    const session = stripeEvent.data.object;
    const lineItems = await stripe.checkout.sessions.listLineItems(session.id, { limit: 100 });
    const shipping = session.customer_details || {};
    const items = (lineItems.data || []).map((item) => ({
      name: item.description,
      description: item.price?.product?.description || "",
      quantity: item.quantity || 0
    }));
    const shippingText = [
      shipping.name,
      shipping.address?.line1,
      shipping.address?.line2,
      [shipping.address?.city, shipping.address?.state, shipping.address?.postal_code].filter(Boolean).join(", "),
      shipping.address?.country
    ].filter(Boolean).join(", ");
    const itemsText = items.map((item) => `${item.name} x ${item.quantity}`).join(" | ");

    const order = {
      sessionId: session.id,
      customerEmail: session.customer_details?.email || session.customer_email || "",
      total: `${((session.amount_total || 0) / 100).toFixed(2)} ${(session.currency || "usd").toUpperCase()}`,
      shipping,
      shippingText,
      items,
      itemsText
    };

    await sendOrderEmail(order);
    await recordOrder(order);

    return response(200, { received: true });
  } catch (error) {
    return response(500, { error: "Webhook processing failed.", details: error.message });
  }
};
