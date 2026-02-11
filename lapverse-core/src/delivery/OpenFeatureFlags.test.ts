import { OpenFeatureFlags } from './OpenFeatureFlags';

test('global flag enabled', async ()=>{
  const flags = new OpenFeatureFlags();
  expect(await flags.isEnabled('task-v2', 'acme')).toBe(true);
});
