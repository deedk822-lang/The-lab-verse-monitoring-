# ⚡ Vaal AI Empire

**Digital Sovereignty for South African SMEs**

Complete autonomous AI platform with Stripe subscription billing.

---

## 🚀 Quick Start

```bash
# Clone repository
git clone https://github.com/deedk822-lang/vaal-ai-empire-site.git
cd vaal-ai-empire-site

# Run installer
chmod +x INSTALL.sh
./INSTALL.sh

# Configure Stripe
cd server
cp .env.example .env
# Edit .env with your keys

# Start server
npm start
```

**Open:** http://localhost:4242

---

## 📦 What's Included

### Complete Website:
- ✅ Professional homepage
- ✅ Pricing page with 2 tiers
- ✅ Success/cancel pages
- ✅ Responsive design
- ✅ Mobile-first approach

### Stripe Integration:
- ✅ Subscription checkout
- ✅ Webhook handling
- ✅ Customer portal
- ✅ ZAR currency
- ✅ 7-day free trials

### Backend:
- ✅ Node.js/Express server
- ✅ Complete API
- ✅ Environment config
- ✅ Production ready

---

## 💰 Pricing Plans

| Plan | Price | Features |
|------|-------|----------|
| **Vaal Starter** | R999/mo | Financial Sentinel, Guardian alerts, Email support |
| **Vaal Empire** | R2,999/mo | All features + Talent Accelerator + Priority support |

---

## 🛠 Tech Stack

- **Frontend:** HTML5, CSS3, Vanilla JS
- **Backend:** Node.js, Express
- **Payments:** Stripe
- **Hosting:** Alibaba Cloud Singapore
- **Currency:** ZAR (South African Rand)

---

## ⚙️ Configuration

### Required Environment Variables:

```env
STRIPE_PUBLISHABLE_KEY=pk_test_...
STRIPE_SECRET_KEY=sk_test_...
STARTER_PRICE_ID=price_...
EMPIRE_PRICE_ID=price_...
DOMAIN=http://localhost:4242
```

See `server/.env.example` for complete list.

---

## 🧪 Testing

### Stripe Test Cards:

```
Success: 4242 4242 4242 4242
3D Secure: 4000 0025 0000 3155
Declined: 4000 0000 0000 0002
```

### Test Flow:

1. Visit http://localhost:4242/pricing.html
2. Click "Start Free Trial"
3. Enter test card details
4. Verify redirect to success page

---

## 🚀 Deployment

### Production Checklist:

- [ ] Switch to live Stripe keys
- [ ] Update DOMAIN in .env
- [ ] Set up webhooks
- [ ] Configure SSL
- [ ] Test real payment
- [ ] Set up monitoring

### Deploy Commands:

```bash
cd server
npm install --production
npm start
```

---

## 📁 Project Structure

```
vaal-ai-empire-site/
├── index.html          # Homepage
├── pricing.html        # Pricing page
├── success.html        # Payment success
├── canceled.html       # Checkout canceled
├── css/
│   └── styles.css      # All styles
├── js/
│   └── main.js         # Frontend JS
├── server/
│   ├── server.js       # Express server
│   ├── package.json    # Dependencies
│   └── .env.example    # Config template
├── INSTALL.sh          # Auto-installer
└── README.md           # This file
```

---

## 📚 Documentation

- **Installation:** See INSTALL.sh output
- **Server API:** server/README.md
- **Stripe Setup:** server/.env.example

---

## 🐛 Troubleshooting

### "Node.js not found"
→ Install from https://nodejs.org/

### "Cannot find module"
→ Run `npm install` in server/

### "Missing API keys"
→ Check server/.env file

### "Port in use"
→ Change PORT in .env

---

## 📧 Support

- **Email:** founders@vaalai.co.za
- **GitHub:** [Issues](https://github.com/deedk822-lang/vaal-ai-empire-site/issues)
- **Stripe:** https://stripe.com/docs

---

## 🇿🇦 About

**Vaal AI Empire** provides digital sovereignty for South African SMEs through three autonomous AI engines:

1. **Financial Sentinel** - Tax recovery & compliance
2. **Guardian Engine** - Infrastructure monitoring
3. **Talent Accelerator** - Automated hiring

**Launch:** December 27, 2025

---

## 📝 License

Proprietary © 2025 Vaal AI Empire, Inc.

---

**⚡ Built in the Vaal. Built for Africa. Built to dominate.** 🇿🇦