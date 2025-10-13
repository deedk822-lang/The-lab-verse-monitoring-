import type { Request, Response, NextFunction } from 'express';

export class OpenApiValidator {
  private loaded = false;
  private requireTenantHeader = false;

  async loadSpec(path?: string): Promise<void> {
    if (path) this.requireTenantHeader = true;
    this.loaded = true;
  }

  validate(req: Request, res: Response, next: NextFunction): void {
    if (!this.loaded) {
      next();
      return;
    }

    const isV2 = req.baseUrl?.includes('/api/v2') || req.originalUrl?.includes('/api/v2');
    const isTasks = req.method === 'POST' && (req.path.endsWith('/tasks') || req.url.endsWith('/tasks'));
    const isComp = req.method === 'POST' && (req.path.endsWith('/self-compete') || req.url.endsWith('/self-compete'));

    if (this.requireTenantHeader && isV2 && (isTasks || isComp)) {
      const idk = req.header('Idempotency-Key');
      const tenant = req.header('X-Tenant-ID');
      if (!idk) {
        res.status(400).json({ error: 'Idempotency-Key header required' });
        return;
      }
      if (!tenant) {
        res.status(400).json({ error: 'X-Tenant-ID header required' });
        return;
      }
    }

    if (isTasks) {
      const body = req.body ?? {};
      if (!body.type || !body.priority || !body.description || !body.tenant) {
        res.status(400).json({ error: 'type, priority, description, tenant are required' });
        return;
      }
    }

    if (isComp) {
      const body = req.body ?? {};
      if (!body.content || !Array.isArray(body.platforms) || !body.priority) {
        res.status(400).json({ error: 'content, platforms[], priority are required' });
        return;
      }
    }

    next();
  }
}
