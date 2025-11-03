import { OpenFeature, InMemoryProvider, Client } from '@openfeature/server-sdk';
import { FastifyInstance } from 'fastify';
import fp from 'fastify-plugin';

// Augment the FastifyInstance to include the OpenFeature client
declare module 'fastify' {
  interface FastifyInstance {
    openfeature: Client;
  }
}

const featureFlagsPlugin = async (fastify: FastifyInstance) => {
  // For demonstration, we'll use an in-memory provider.
  // In a real production environment, this would be a service like Flagsmith, LaunchDarkly, etc.
  const provider = new InMemoryProvider({
    'pricingV2': {
      disabled: false,
      variants: {
        on: true,
        off: false,
      },
      defaultVariant: 'off',
    },
  });

  await OpenFeature.setProviderAndWait(provider);
  const client = OpenFeature.getClient('scout-monetization');

  fastify.decorate('openfeature', client);

  console.log('✅ OpenFeature service initialized with in-memory provider.');
};

export default fp(featureFlagsPlugin, { name: 'feature-flags' });