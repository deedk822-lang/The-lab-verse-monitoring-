import axios from 'axios';
import { Config } from '../config/Config';
import { trace } from '@opentelemetry/api';  // OTel for traces

Config.load();

class KaggleService {
  private tracer = trace.getTracer('lapverse-kaggle');

  async syncCompetitionData(compId: string) {
    const span = this.tracer.startSpan('kaggle.sync');
    try {
      const response = await axios.post('https://www.kaggle.com/api/v1/competitions/sync', {
        id: compId
      }, {
        headers: { Authorization: `Kaggle ${Config.env.KAGGLE_API_KEY}` },
        timeout: 30000  // 30s for data sync
      });
      span.setAttribute('sync.success', true);
      return { datasetId: response.data.id, status: 'synced' };
    } catch (error) {
      span.recordException(error as Error);
      span.setStatus({ code: 2, message: 'Kaggle Sync Failed' });
      throw error;
    } finally {
      span.end();
    }
  }

  async evaluateNotebook(nbId: string) {
    const span = this.tracer.startSpan('kaggle.eval');
    try {
      const response = await axios.post('https://www.kaggle.com/api/v1/notebooks/evaluate', {
        id: nbId
      }, {
        headers: { Authorization: `Kaggle ${Config.env.KAGGLE_API_KEY}` }
      });
      const score = response.data.score;
      span.setAttribute('eval.score', score);
      return { score, status: 'evaluated' };
    } catch (error) {
      span.recordException(error as Error);
      throw error;
    } finally {
      span.end();
    }
  }

  async promoteModel(modelId: string) {
    const span = this.tracer.startSpan('kaggle.promote');
    try {
      const response = await axios.post('https://www.kaggle.com/api/v1/models/promote', {
        id: modelId
      }, {
        headers: { Authorization: `Kaggle ${Config.env.KAGGLE_API_KEY}` }
      });
      span.setAttribute('promote.success', true);
      return { status: 'promoted' };
    } catch (error) {
      span.recordException(error as Error);
      throw error;
    } finally {
      span.end();
    }
  }
}

export { KaggleService };