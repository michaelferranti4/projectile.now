const { readCatalog, sanitizeCatalog } = require("./lib/catalog");

exports.handler = async function handler() {
  try {
    const catalog = readCatalog();
    return {
      statusCode: 200,
      headers: {
        "Content-Type": "application/json",
        "Cache-Control": "no-store"
      },
      body: JSON.stringify(sanitizeCatalog(catalog))
    };
  } catch (error) {
    return {
      statusCode: 500,
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ error: "Failed to load catalog.", details: error.message })
    };
  }
};
