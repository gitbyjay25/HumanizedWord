export default function robots() {
  return {
    rules: [
      {
        userAgent: "*",
        allow: "/",
      },
    ],
    sitemap: "https://humanizedtext.pro/sitemap.xml",
  };
}
