import { Request, Response, NextFunction } from 'express';

export class OpenApiValidator {
    async loadSpec(path: string): Promise<void> { /* Load OpenAPI spec logic */ }
    validate(req: Request, res: Response, next: NextFunction) { next(); }
}

