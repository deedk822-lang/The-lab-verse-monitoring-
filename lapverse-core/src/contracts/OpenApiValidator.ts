import type { Request, Response, NextFunction } from 'express';

type HeaderSpec = { name: string; required?: boolean };

export class OpenApiValidator {
  private loaded = false;
 cursor/the-lap-verse-core-service-polish-ae35
  private taskHeaders: HeaderSpec[] = [
    { name: 'idempotency-key', required: true },
    { name: 'x-tenant-id', required: true }
  ];

  async loadSpec(_path?: string){
    // Stubbed: accept a path, mark as loaded to avoid drift

  private requireTenantHeader = false;

  async loadSpec(path?: string){
    // Future: compile OpenAPI 3.1; for now, toggle stricter checks when path provided
    if (path) this.requireTenantHeader = true;
 main
    this.loaded = true;
  }

  validate(req: Request, res: Response, next: NextFunction){
    if (!this.loaded) return next();

 cursor/the-lap-verse-core-service-polish-ae35
    const isV2 = req.baseUrl?.endsWith('/api/v2') || req.originalUrl?.includes('/api/v2');
    if (!isV2) return next();

    // Headers (case-insensitive)
    const getHeader = (name: string) => req.headers[name] || req.headers[name.toLowerCase()];
    for (const h of this.taskHeaders){
      if (h.required && !getHeader(h.name)){
        return res.status(400).json({ error: `missing required header: ${h.name}` });
      }
    }

    // Body validation for POST routes
    if (req.method === 'POST'){
      const body = req.body ?? {};
      if (req.path.endsWith('/tasks')){
        const required = ['type','priority','description','tenant'];
        const missing = required.filter(k => body[k] === undefined);
        if (missing.length) return res.status(400).json({ error: `missing fields: ${missing.join(', ')}` });
      }
      if (req.path.endsWith('/self-compete')){
        const required = ['content','platforms','priority'];
        const missing = required.filter(k => body[k] === undefined);
        if (missing.length) return res.status(400).json({ error: `missing fields: ${missing.join(', ')}` });

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
 main
      }
    }

    next();
  }
}
