import type { Request, Response, NextFunction } from 'express';

export class IdempotencyManager {
  private cache = new Map<string, any>();

  async isDuplicate(key: string){ return this.cache.has(key); }
  async getCached(key: string){ return this.cache.get(key); }
  async setCached(key: string, value: any){ this.cache.set(key, value); }
  async cacheResult(key: string, value: any){ this.cache.set(key, value); }

  middleware(req: Request, _res: Response, next: NextFunction){
    const key = req.header('Idempotency-Key');
    if (key) (req as any).idempotencyKey = key;
    next();
  }
}
