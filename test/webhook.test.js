import test from 'node:test';
import assert from 'node:assert';
import { mock } from 'node:test';
import handler, { _setOctokitForTest } from '../api/webhook.js';
import utils from '../api/util.js';

// --- Test Setup ---
const getMockReq = () => ({
  method: 'POST',
  headers: { 'x-webhook-signature': 'sha256=valid_signature' },
  body: {
    event: 'post.published',
    article: { id: '123', title: 'Test Article', content: '<p>Test</p>', author: { name: 'Test' }, tags: [], published_at: new Date().toISOString() }
  }
});

const getMockRes = () => ({
  statusCode: 200,
  body: {},
  status: function(code) { this.statusCode = code; return this; },
  json: function(data) { this.body = data; return this; }
});

const setupEnv = () => {
  process.env.NODE_ENV = 'test';
  process.env.GITHUB_TOKEN = 'test_token';
  process.env.GITHUB_OWNER = 'test_owner';
  process.env.GITHUB_REPO = 'test_repo';
  process.env.WEBHOOK_SECRET = 'test_secret';
  process.env.CREATE_PR = 'false';
  process.env.SLACK_WEBHOOK_URL = 'https://hooks.slack.com/services/test';
};

// --- Test Suite ---
test('RankYak Webhook Handler', async (t) => {
  let octokitMocks;
  let fetchMock;

  t.beforeEach(() => {
    setupEnv();

    fetchMock = mock.method(global, 'fetch', async () => ({ ok: true }));

    octokitMocks = {
      repos: {
        getContent: mock.fn(() => { throw new Error('File not found'); }),
        createOrUpdateFileContents: mock.fn(() => ({ data: { content: { html_url: 'https://github.com/content/url' } } }))
      },
      git: {
        getRef: mock.fn(() => ({ data: { object: { sha: 'base_sha' } } })),
        createRef: mock.fn()
      },
      pulls: {
        create: mock.fn(() => ({ data: { number: 1, html_url: 'https://github.com/pr/url' } }))
      },
      issues: {
        addLabels: mock.fn()
      }
    };
    _setOctokitForTest(octokitMocks);
  });

  t.afterEach(() => mock.reset());

  await t.test('should return 405 for non-POST requests', async () => {
    mock.method(utils, 'verifySignature', () => true);
    const mockReq = getMockReq();
    mockReq.method = 'GET';
    const mockRes = getMockRes();
    await handler(mockReq, mockRes);
    assert.strictEqual(mockRes.statusCode, 405);
    assert.deepStrictEqual(mockRes.body, { error: 'Method not allowed' });
  });

  await t.test('should return 401 for invalid signature', async () => {
    mock.method(utils, 'verifySignature', () => false);
    const mockReq = getMockReq();
    const mockRes = getMockRes();
    await handler(mockReq, mockRes);
    assert.strictEqual(mockRes.statusCode, 401);
    assert.deepStrictEqual(mockRes.body, { error: 'Invalid signature' });
  });

  await t.test('should ignore non-publish events', async () => {
    mock.method(utils, 'verifySignature', () => true);
    const mockReq = getMockReq();
    mockReq.body.event = 'post.updated';
    const mockRes = getMockRes();
    await handler(mockReq, mockRes);
    assert.strictEqual(mockRes.statusCode, 200);
    assert.deepStrictEqual(mockRes.body.message, 'Event ignored');
  });

  await t.test('should return 400 for invalid article data', async () => {
    mock.method(utils, 'verifySignature', () => true);
    const mockReq = getMockReq();
    mockReq.body.article.title = '';
    const mockRes = getMockRes();
    await handler(mockReq, mockRes);
    assert.strictEqual(mockRes.statusCode, 400);
    assert.deepStrictEqual(mockRes.body, { error: 'Invalid article data' });
  });

  await t.test('Direct Commit: should commit file and notify Slack', async () => {
    mock.method(utils, 'verifySignature', () => true);
    const mockReq = getMockReq();
    const mockRes = getMockRes();
    await handler(mockReq, mockRes);
    assert.strictEqual(octokitMocks.repos.createOrUpdateFileContents.mock.calls.length, 1);
    assert.strictEqual(fetchMock.mock.calls.length, 1);
    assert.strictEqual(mockRes.statusCode, 200);
    assert.strictEqual(mockRes.body.success, true);
    assert.strictEqual(mockRes.body.message, 'Content committed');
  });

  await t.test('PR Mode: should create PR and notify Slack', async () => {
    mock.method(utils, 'verifySignature', () => true);
    process.env.CREATE_PR = 'true';
    const mockReq = getMockReq();
    const mockRes = getMockRes();
    await handler(mockReq, mockRes);
    assert.strictEqual(octokitMocks.git.createRef.mock.calls.length, 1);
    assert.strictEqual(octokitMocks.pulls.create.mock.calls.length, 1);
    assert.strictEqual(fetchMock.mock.calls.length, 1);
    assert.strictEqual(mockRes.statusCode, 200);
    assert.strictEqual(mockRes.body.success, true);
    assert.strictEqual(mockRes.body.message, 'Pull request created');
  });

  await t.test('should handle GitHub API errors gracefully', async () => {
    mock.method(utils, 'verifySignature', () => true);
    octokitMocks.repos.createOrUpdateFileContents.mock.mockImplementation(() => { throw new Error('GitHub API Error'); });
    const mockReq = getMockReq();
    const mockRes = getMockRes();
    await handler(mockReq, mockRes);
    assert.strictEqual(mockRes.statusCode, 500);
    assert.deepStrictEqual(mockRes.body.error, 'Processing failed');
  });
});
