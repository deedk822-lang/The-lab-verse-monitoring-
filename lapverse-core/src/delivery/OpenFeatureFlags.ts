export class OpenFeatureFlags {
  private flags = new Map<string, Set<string>>();

  async isEnabled(flag: string, tenant: string){
    const set = this.flags.get(flag);
    return set ? set.has(tenant) : true; // default enabled
  }

  setRollout(flag: string, percent: number){
    // stub: no-op; in real impl, bucket by tenant hash
  }
}
