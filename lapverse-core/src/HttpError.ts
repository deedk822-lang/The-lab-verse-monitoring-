export class HttpError extends Error {
  constructor(
    public readonly status: number,
    message: string,
    public readonly code?: string,
    public readonly retryable: boolean = false
  ) {
    super(message);
    this.name = 'HttpError';
    Error.captureStackTrace(this, this.constructor);
  }
}

export class RateLimitError extends HttpError {
  constructor(message: string = 'Rate limit exceeded') {
    super(429, message, 'RATE_LIMIT_EXCEEDED', true);
    this.name = 'RateLimitError';
  }
}

export class CapacityError extends HttpError {
  constructor(message: string = 'Service capacity exceeded') {
    super(503, message, 'CAPACITY_EXCEEDED', true);
    this.name = 'CapacityError';
  }
}

export class FeatureDisabledError extends HttpError {
  constructor(feature: string) {
    super(403, `Feature ${feature} not available`, 'FEATURE_DISABLED', false);
    this.name = 'FeatureDisabledError';
  }
}
