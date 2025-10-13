import { IdempotencyManager } from './IdempotencyManager';

test('cache roundtrip', async ()=>{
  const i = new IdempotencyManager();
  await i.cacheResult('k','v');
  expect(await i.isDuplicate('k')).toBe(true);
  expect(await i.getCached('k')).toBe('v');
});
