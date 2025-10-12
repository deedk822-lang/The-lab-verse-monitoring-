import { StatsD } from 'hot-shots';

export class FinOpsTagger {
    private readonly client = new StatsD();

    emitUsage(usage: { artifactId?: string; forecastCost: number; tenant?: string; source: string; }) {
        this.client.increment('finops.usage.emit', 1, {
            source: usage.source,
            tenant: usage.tenant || 'default'
        });
    }

    getFinOpsTags(task: any) {
        return {
            'finops.cost_center': 'ai-inference',
            'finops.tenant': task.tenantId || 'default',
        };
    }

    getAllocation() {
        return {
            'project-default': {
                used: 100,
                limit: 1000,
            }
        }
    }

    async estimate(body: any) {
        return 0.001;
    }

    async estimateCompetition(body: any) {
        return 0.01;
    }

    async wouldBustMargin(tenant: string, forecast: number) {
        return false;
    }

    async calculate(task: any) {
        return 0.002
    }

    async calculateCompetition(results: any) {
        return 0.02
    }

    trackLlmUsage(tokens: number, dimensions: any) {
        this.client.histogram('finops.llm.tokens', tokens, dimensions);
    }
}