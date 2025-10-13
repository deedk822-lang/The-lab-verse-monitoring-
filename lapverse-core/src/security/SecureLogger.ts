import pino from 'pino';
import { randomUUID } from 'crypto';

const logger = pino({
  redact: ['*.password', '*.token', '*.email', '*.ip', '*.ssn'],
  mixin: () => ({ traceId: randomUUID() })
});

export class SecureLogger {
  info(obj: any, msg?: string){ logger.info(obj, msg); }
  error(obj: any, msg?: string){ logger.error(obj, msg); }
}
