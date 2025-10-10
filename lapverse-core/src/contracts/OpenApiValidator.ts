import type { Request, Response, NextFunction } from 'express';

type HeaderSpec = { name: string; required?: boolean };

export class OpenApiValidator {
  private loaded = false;
  private taskHeaders: HeaderSpec[] = [
    { name: 'idempotency-key', required: true },
    { name: 'x-tenant-id', required: true }
  ];

  async loadSpec(_path?: string){
    // Stubbed: accept a path, mark as loaded to avoid drift
    this.loaded = true;
  }

  validate(req: Request, res: Response, next: NextFunction){
    if (!this.loaded) return next();

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
      }
    }
    next();
  }
}
