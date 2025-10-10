import type { Request, Response, NextFunction } from 'express';

export class OpenApiValidator {
  private loaded = false;

  async loadSpec(){
    // In a real system, load and compile OpenAPI schema here
    this.loaded = true;
  }

  validate(req: Request, res: Response, next: NextFunction){
    if (!this.loaded) return next();

    // Minimal contract for POST /api/tasks
    if (req.method === 'POST' && (req.path === '/tasks' || req.url.endsWith('/tasks'))){
      const body = req.body ?? {};
      if (!body.type || !body.priority || !body.tenant){
        return res.status(400).json({ error: 'type, priority, tenant are required' });
      }
    }
    next();
  }
}
