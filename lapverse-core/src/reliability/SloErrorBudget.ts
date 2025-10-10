export class SloErrorBudget {
  private burnRate = 0.1; // start safe
  async loadBudget(){ /* load from prometheus */ }
  wouldExceedBudget(){ return this.burnRate > 1; }
  getBurnRate(){ return this.burnRate; }
  recordApiCall(source: string, count: number){ /* inc prometheus */ }
}
