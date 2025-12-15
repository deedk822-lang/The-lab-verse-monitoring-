# Vaal AI Empire - Server

Node.js/Express server handling Stripe subscription checkout.

## Quick Start

```bash
cd server
npm install
cp .env.example .env
# Edit .env with your Stripe keys
npm start
```

## Requirements

- Node.js 18+
- npm 9+
- Stripe account

## Environment Variables

See `.env.example` for all required variables.

## Endpoints

- `GET /` - Homepage
- `GET /config` - Stripe configuration
- `POST /create-checkout-session` - Create checkout
- `GET /checkout-session` - Get session details
- `POST /webhook` - Stripe webhooks
- `POST /create-portal-session` - Customer portal
- `GET /health` - Health check

## Testing

Test card: `4242 4242 4242 4242`

## Production

See main INSTALL.md for deployment instructions.

## Support

founders@vaalai.co.za