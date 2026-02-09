import { FastifyInstance } from 'fastify';
import CircuitBreaker from 'opossum';
import fp from 'fastify-plugin';

// Define a type for the function that will be wrapped by the circuit breaker
type Action<T> = (...args: any[]) => Promise<T>;

// Augment the FastifyInstance to include the circuit breaker factory
declare module 'fastify' {
  interface FastifyInstance {
    circuitBreaker: {
      create: <T>(action: Action<T>, options?: CircuitBreaker.Options) => CircuitBreaker<any[], T>;
    };
  }
}

const circuitBreakerPlugin = async (fastify: FastifyInstance) => {
  const create = <T>(action: Action<T>, options?: CircuitBreaker.Options): CircuitBreaker<any[], T> => {
    const defaultOptions: CircuitBreaker.Options = {
      timeout: 3000, // If the action takes longer than 3 seconds, trigger a failure
      errorThresholdPercentage: 50, // If 50% of requests fail, trip the circuit
      resetTimeout: 30000, // After 30 seconds, try again.
      ...options,
    };

    const breaker = new CircuitBreaker(action, defaultOptions);

    // Log events for observability
    breaker.on('open', () => console.warn(`[CircuitBreaker] Circuit opened for ${action.name || 'anonymous action'}.`));
    breaker.on('close', () => console.log(`[CircuitBreaker] Circuit closed for ${action.name || 'anonymous action'}.`));
    breaker.on('halfOpen', () => console.log(`[CircuitBreaker] Circuit half-open for ${action.name || 'anonymous action'}.`));
    breaker.on('fallback', (result) => console.log(`[CircuitBreaker] Fallback executed for ${action.name || 'anonymous action'}. Result:`, result));

    return breaker;
  };

  fastify.decorate('circuitBreaker', { create });

  console.log('✅ Circuit Breaker service initialized.');
};

export default fp(circuitBreakerPlugin, { name: 'circuit-breaker' });