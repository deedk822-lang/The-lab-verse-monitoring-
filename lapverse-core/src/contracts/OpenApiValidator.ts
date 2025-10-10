import type { Request, Response, NextFunction } from 'express';

export class OpenApiValidator {
  private loaded = false;
  private requireTenantHeader = false;

  async loadSpec(path?: string){
    // Future: compile OpenAPI 3.1; for now, toggle stricter checks when path provided
    if (path) this.requireTenantHeader = true;
    this.loaded = true;
  }

  validate(req: Request, res: Response, next: NextFunction){
    if (!this.loaded) return next();

    const isV2 = req.baseUrl?.includes('/api/v2') || req.originalUrl?.includes('/api/v2');
    const isTasks = req.method === 'POST' && (req.path.endsWith('/tasks') || req.url.endsWith('/tasks'));
    const isComp  = req.method === 'POST' && (req.path.endsWith('/self-compete') || req.url.endsWith('/self-compete'));

    if (this.requireTenantHeader && isV2 && (isTasks || isComp)){
      const idk = req.header('Idempotency-Key');
      const tenant = req.header('X-Tenant-ID');
      if (!idk) return res.status(400).json({ error: 'Idempotency-Key header required' });
      if (!tenant) return res.status(400).json({ error: 'X-Tenant-ID header required' });
    }

    if (isTasks){
      const body = req.body ?? {};
      if (!body.type || !body.priority || !body.description || !body.tenant){
        return res.status(400).json({ error: 'type, priority, description, tenant are required' });
      }
    }

    if (isComp){
      const body = req.body ?? {};
      if (!body.content || !Array.isArray(body.platforms) || !body.priority){
        return res.status(400).json({ error: 'content, platforms[], priority are required' });
      }
    }

    next();
  }
}
