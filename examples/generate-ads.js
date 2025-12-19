const axios = require("axios");

async function generateAds() {
  const apiToken = process.env.BRIA_API_TOKEN;

  const payload = {
    content_moderation: true,
    template_id: "1062",
    brand_id: "167",
    smart_image: {
      input_image_url: "https://example.com/product.png",
      scene: {
        operation: "lifestyle_shot_by_text",
        input: "Modern living room with soft natural light"
      }
    },
    elements: [
      {
        layer_type: "text",
        content_type: "Heading #1",
        content: "Summer Sale - Up to 50% Off",
        id: "headline_1"
      },
      {
        layer_type: "text",
        content_type: "Body #1",
        content: "Limited time offer on all living room furniture.",
        id: "body_1"
      },
      {
        layer_type: "image",
        content_type: "Image #1",
        content: "https://example.com/logo.png",
        id: "brand_logo"
      }
    ]
  };

  const res = await axios.post("https://api.bria.ai/ads/generate", payload, {
    headers: { api_token: apiToken }
  });

  console.log(res.data);
}

generateAds().catch(console.error);
