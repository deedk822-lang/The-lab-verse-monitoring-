export class CircuitBreaker {
    constructor(func: Function, options: any) {}
    async execute(func: Function): Promise<any> { return func(); }
}
