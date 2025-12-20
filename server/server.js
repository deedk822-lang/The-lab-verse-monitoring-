// Vaal AI Empire - Stripe Checkout Server
// Handles subscription checkout for SA SMEs

require('dotenv').config();
const express = require('express');
const bodyParser = require('body-parser');
const path = require('path');

// Initialize Stripe with your secret key
const stripe = require('stripe')(process.env.STRIPE_SECRET_KEY);

const app = express();
const port = process.env.PORT || 4242;

// Middleware
app.use(bodyParser.json());
app.use(bodyParser.urlencoded({ extended: true }));
app.use(express.static(process.env.STATIC_DIR || '../client'));

// CORS for development
app.use((req, res, next) => {
  res.header('Access-Control-Allow-Origin', '*');
  res.header('Access-Control-Allow-Headers', 'Content-Type');
  next();
});

// Routes
app.get('/', (req, res) => {
  const indexPath = path.resolve(process.env.STATIC_DIR || '../client', 'index.html');
  res.sendFile(indexPath);
});

// Get pricing configuration
app.get('/config', (req, res) => {
  res.send({
    publishableKey: process.env.STRIPE_PUBLISHABLE_KEY,
    prices: {
      starter: process.env.STARTER_PRICE_ID,
      empire: process.env.EMPIRE_PRICE_ID
    }
  });
});

// Create Checkout Session
app.post('/create-checkout-session', async (req, res) => {
  const { priceId } = req.body;
  
  try {
    const session = await stripe.checkout.sessions.create({
      mode: 'subscription',
      line_items: [
        {
          price: priceId,
          quantity: 1,
        },
      ],
      // Success and cancel URLs
      success_url: `${process.env.DOMAIN}/success?session_id={CHECKOUT_SESSION_ID}`,
      cancel_url: `${process.env.DOMAIN}/canceled`,
      // Automatically create customer
      customer_creation: 'always',
      // Collect billing address
      billing_address_collection: 'required',
      // Allow promotion codes
      allow_promotion_codes: true,
      // Payment method types
      payment_method_types: ['card'],
      // Metadata for tracking
      metadata: {
        product: priceId === process.env.STARTER_PRICE_ID ? 'Vaal Starter' : 'Vaal Empire',
        source: 'vaalai_website'
      },
      // Subscription data
      subscription_data: {
        metadata: {
          product: priceId === process.env.STARTER_PRICE_ID ? 'Vaal Starter' : 'Vaal Empire'
        },
      },
    });
    
    res.json({ sessionId: session.id });
  } catch (error) {
    console.error('Error creating checkout session:', error);
    res.status(500).json({ error: error.message });
  }
});

// Get session details for success page
app.get('/checkout-session', async (req, res) => {
  const { sessionId } = req.query;
  
  try {
    const session = await stripe.checkout.sessions.retrieve(sessionId);
    res.json(session);
  } catch (error) {
    console.error('Error retrieving session:', error);
    res.status(500).json({ error: error.message });
  }
});

// Webhook endpoint for Stripe events
app.post('/webhook', bodyParser.raw({type: 'application/json'}), async (req, res) => {
  const sig = req.headers['stripe-signature'];
  let event;
  
  try {
    event = stripe.webhooks.constructEvent(
      req.body,
      sig,
      process.env.STRIPE_WEBHOOK_SECRET
    );
  } catch (err) {
    console.error('Webhook signature verification failed:', err.message);
    return res.status(400).send(`Webhook Error: ${err.message}`);
  }
  
  // Handle the event
  switch (event.type) {
    case 'checkout.session.completed':
      const session = event.data.object;
      console.log('✅ Checkout completed:', session.id);
      console.log('Customer:', session.customer);
      console.log('Subscription:', session.subscription);
      break;
      
    case 'customer.subscription.created':
      const subscription = event.data.object;
      console.log('✅ Subscription created:', subscription.id);
      break;
      
    case 'customer.subscription.updated':
      const updatedSub = event.data.object;
      console.log('🔄 Subscription updated:', updatedSub.id);
      break;
      
    case 'customer.subscription.deleted':
      const deletedSub = event.data.object;
      console.log('❌ Subscription canceled:', deletedSub.id);
      break;
      
    case 'invoice.paid':
      const invoice = event.data.object;
      console.log('💰 Invoice paid:', invoice.id);
      break;
      
    case 'invoice.payment_failed':
      const failedInvoice = event.data.object;
      console.log('⚠️ Payment failed:', failedInvoice.id);
      break;
      
    default:
      console.log(`Unhandled event type: ${event.type}`);
  }
  
  res.json({ received: true });
});

// Customer Portal
app.post('/create-portal-session', async (req, res) => {
  const { customerId } = req.body;
  
  try {
    const portalSession = await stripe.billingPortal.sessions.create({
      customer: customerId,
      return_url: `${process.env.DOMAIN}/account`,
    });
    
    res.json({ url: portalSession.url });
  } catch (error) {
    console.error('Error creating portal session:', error);
    res.status(500).json({ error: error.message });
  }
});

const omniController = require('../services/omni_controller');

// This endpoint receives the "Signal" from your Frontend Dashboard
app.post('/api/empire/execute', async (req, res) => {
    const { signal, department } = req.body;

    // signal = "SABC reports Maths Literacy failure"
    // department = "Education"

    const result = await omniController.executeSovereignCycle(signal, department);
    res.json(result);
});

// Health check
app.get('/health', (req, res) => {
  res.json({ 
    status: 'ok',
    service: 'vaal-ai-empire-checkout',
    timestamp: new Date().toISOString()
  });
});

// Start server
app.listen(port, () => {
  console.log('⚡ Vaal AI Empire Checkout Server');
  console.log(`🚀 Running on http://localhost:${port}`);
  console.log(`📊 Environment: ${process.env.NODE_ENV || 'development'}`);
});

module.exports = app;