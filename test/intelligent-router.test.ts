import {
  generateContentWithFallback,
  factCheckClaim,
  extractClaims,
  generateFactCheckedContent,
} from '../src/ai-connections/intelligent-router';
import { MISTRAL_MODELS, AI_CONNECTIONS } from '../src/ai-connections/mistral-config';

let nock;

beforeAll(async () => {
  const nockModule = await import('nock');
  nock = nockModule.default;
});

// Set dummy API keys for testing
process.env.MISTRAL_API_KEY = 'test-mistral-key';
process.env.GLM_API_KEY = 'test-glm-key';
process.env.GEMINI_API_KEY = 'test-gemini-key';
process.env.GROQ_API_KEY = 'test-groq-key';


const MISTRAL_API_ENDPOINT = MISTRAL_MODELS.MIXTRAL.apiEndpoint;
const GLM_API_ENDPOINT = 'https://open.bigmodel.cn/api/paas/v4';
const OPENAI_COMPATIBLE_ENDPOINT = 'https://api.openai.com/v1';


describe('Intelligent Router', () => {
  beforeEach(() => {
    if(nock) {
      nock.disableNetConnect();
      if (!nock.isActive()) nock.activate();
    }
  });

  afterEach(() => {
    if(nock) {
      nock.cleanAll();
      nock.restore();
    }
  });

  describe('generateContentWithFallback', () => {
    it('should return content from the primary model when it succeeds', async () => {
      const prompt = 'Hello, world!';
      const primaryModel = AI_CONNECTIONS.PRIMARY.model;
      const expectedContent = 'This is a response from the primary model.';

      nock(MISTRAL_API_ENDPOINT)
        .post('/chat/completions')
        .reply(200, {
          choices: [{ message: { content: expectedContent } }],
        });

      const result = await generateContentWithFallback(prompt);

      expect(result.success).toBe(true);
      expect(result.content).toBe(expectedContent);
      expect(result.modelUsed).toBe(primaryModel);
    });

    it('should return content from the fallback model when the primary model fails', async () => {
      const prompt = 'Hello, world!';
      const fallbackModel = AI_CONNECTIONS.PRIMARY.fallbackModel;
      const expectedContent = 'This is a response from the fallback model.';

      nock(MISTRAL_API_ENDPOINT)
        .post('/chat/completions')
        .reply(500, { error: 'Internal Server Error' });

      nock(GLM_API_ENDPOINT)
        .post('/chat/completions')
        .reply(200, {
          choices: [{ message: { content: expectedContent } }],
        });

      const result = await generateContentWithFallback(prompt);

      expect(result.success).toBe(true);
      expect(result.content).toBe(expectedContent);
      expect(result.modelUsed).toBe(fallbackModel);
    });

    it('should return an error when both primary and fallback models fail', async () => {
      const prompt = 'Hello, world!';

      nock(MISTRAL_API_ENDPOINT)
        .post('/chat/completions')
        .reply(500, { error: 'Internal Server Error' });

      nock(GLM_API_ENDPOINT)
        .post('/chat/completions')
        .reply(500, { error: 'Internal Server Error' });

      const result = await generateContentWithFallback(prompt);

      expect(result.success).toBe(false);
      expect(result.content).toContain('Error: Unable to generate content.');
      expect(result.modelUsed).toBe('none');
    });
  });

  describe('factCheckClaim', () => {
    const claim = 'The sky is blue.';

    const mockJudgeResponse = (verdict, confidence, judgeName) => ({
      verdict,
      confidence,
      reasoning: `The verdict is ${verdict} with ${confidence}% confidence.`,
      judge: judgeName,
    });

    it('should return "Fact-Checked: True" when at least two judges agree', async () => {
      nock(OPENAI_COMPATIBLE_ENDPOINT)
        .post('/chat/completions')
        .twice()
        .reply(200, {
          choices: [{ message: { content: JSON.stringify(mockJudgeResponse('True', 95, 'Judge Gemini/Grok')) } }],
        });

      nock(MISTRAL_API_ENDPOINT)
        .post('/chat/completions')
        .reply(200, {
          choices: [{ message: { content: JSON.stringify(mockJudgeResponse('False', 80, 'Judge Mistral')) } }],
        });

      const result = await factCheckClaim(claim);
      expect(result.finalVerdict).toBe('Fact-Checked: True');
      expect(result.consensus).toBe('Consensus: 2/3 judges agree');
    });

    it('should return "Fact-Checked: False" when at least two judges agree', async () => {
        nock(OPENAI_COMPATIBLE_ENDPOINT)
            .post('/chat/completions')
            .twice()
            .reply(200, {
                choices: [{ message: { content: JSON.stringify(mockJudgeResponse('False', 90, 'Judge Gemini/Grok')) } }],
            });

        nock(MISTRAL_API_ENDPOINT)
            .post('/chat/completions')
            .reply(200, {
                choices: [{ message: { content: JSON.stringify(mockJudgeResponse('True', 85, 'Judge Mistral')) } }],
            });

        const result = await factCheckClaim(claim);
        expect(result.finalVerdict).toBe('Fact-Checked: False');
        expect(result.consensus).toBe('Consensus: 2/3 judges agree');
    });

    it('should return "Inconclusive" when no consensus is reached', async () => {
        nock(OPENAI_COMPATIBLE_ENDPOINT)
            .post('/chat/completions')
            .reply(200, {
                choices: [{ message: { content: JSON.stringify(mockJudgeResponse('True', 90, 'Judge Gemini')) } }],
            });
        nock(OPENAI_COMPATIBLE_ENDPOINT)
            .post('/chat/completions')
            .reply(200, {
                choices: [{ message: { content: JSON.stringify(mockJudgeResponse('False', 88, 'Judge Grok')) } }],
            });
        nock(MISTRAL_API_ENDPOINT)
            .post('/chat/completions')
            .reply(200, {
                choices: [{ message: { content: JSON.stringify(mockJudgeResponse('Inconclusive', 50, 'Judge Mistral')) } }],
            });

        const result = await factCheckClaim(claim);
        expect(result.finalVerdict).toBe('Fact-Checked: Inconclusive');
        expect(result.consensus).toBe('No consensus reached (judges disagree)');
    });
  });

  describe('extractClaims', () => {
    const content = 'The Earth is round. The sun is a star.';

    it('should extract claims from content successfully', async () => {
      const expectedClaims = ['The Earth is round.', 'The sun is a star.'];
      nock(MISTRAL_API_ENDPOINT)
        .post('/chat/completions')
        .reply(200, {
          choices: [{ message: { content: JSON.stringify(expectedClaims) } }],
        });

      const claims = await extractClaims(content);
      expect(claims).toEqual(expectedClaims);
    });
  });

  describe('generateFactCheckedContent', () => {
    const prompt = 'Tell me about the Earth.';
    const generatedContent = 'The Earth is flat.';
    const claims = ['The Earth is flat.'];

    it('should generate content and append fact-check evidence', async () => {
      // Mock content generation
      nock(MISTRAL_API_ENDPOINT)
        .post('/chat/completions')
        .reply(200, {
          choices: [{ message: { content: generatedContent } }],
        });

      // Mock claim extraction
      nock(MISTRAL_API_ENDPOINT)
        .post('/chat/completions')
        .reply(200, {
          choices: [{ message: { content: JSON.stringify(claims) } }],
        });

      // Mock fact-checking judges
      nock(OPENAI_COMPATIBLE_ENDPOINT)
        .post('/chat/completions')
        .twice()
        .reply(200, {
          choices: [{ message: { content: JSON.stringify({ verdict: 'False', confidence: 99, reasoning: 'Scientific consensus.' }) } }],
        });
      nock(MISTRAL_API_ENDPOINT)
        .post('/chat/completions')
        .reply(200, {
          choices: [{ message: { content: JSON.stringify({ verdict: 'False', confidence: 98, reasoning: 'Overwhelming evidence.' }) } }],
        });

      const result = await generateFactCheckedContent(prompt);

      expect(result.success).toBe(true);
      expect(result.content).toContain(generatedContent);
      expect(result.content).toContain('Fact-Check Evidence');
      expect(result.factChecks).toHaveLength(1);
      expect(result.factChecks[0].finalVerdict).toBe('Fact-Checked: False');
    });
  });
});
