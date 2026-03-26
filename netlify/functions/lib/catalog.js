const fs = require("fs");
const path = require("path");

function resolveCatalogPath() {
  const candidates = [
    path.resolve(process.cwd(), "data/products.json"),
    path.resolve(__dirname, "../../../data/products.json"),
    path.resolve(__dirname, "../../data/products.json"),
    path.resolve("/var/task/data/products.json")
  ];

  for (const candidate of candidates) {
    if (fs.existsSync(candidate)) {
      return candidate;
    }
  }

  throw new Error(`Catalog file not found. Checked: ${candidates.join(", ")}`);
}

function readCatalog() {
  const catalogPath = resolveCatalogPath();
  const raw = fs.readFileSync(catalogPath, "utf8");
  return JSON.parse(raw);
}

function sanitizeCatalog(catalog) {
  return {
    collection: catalog.collection,
    products: (catalog.products || [])
      .filter((product) => product.active)
      .map((product) => ({
        id: product.id,
        slug: product.slug,
        title: product.title,
        description: product.description,
        active: Boolean(product.active),
        featuredImage: product.featuredImage,
        images: product.images || [],
        options: product.options || [],
        variants: (product.variants || []).map((variant) => ({
          id: variant.id,
          label: variant.label,
          priceCents: variant.priceCents,
          currency: variant.currency || catalog.collection?.currency || "USD",
          available: Boolean(variant.available),
          image: variant.image || product.featuredImage,
          options: variant.options || {},
          stripePriceId: variant.stripePriceId || null
        }))
      }))
  };
}

function findVariantById(catalog, variantId) {
  for (const product of catalog.products || []) {
    for (const variant of product.variants || []) {
      if (variant.id === variantId) {
        return { product, variant };
      }
    }
  }
  return null;
}

module.exports = {
  findVariantById,
  readCatalog,
  sanitizeCatalog
};
