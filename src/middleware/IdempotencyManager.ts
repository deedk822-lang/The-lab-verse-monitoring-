export class IdempotencyManager {
  async isDuplicate(key: string): Promise<boolean> { return false; }
  async getCached(key: string): Promise<any> { return {}; }
  middleware() { return (req: any, res: any, next: any) => next(); }
}
