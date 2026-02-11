import { OpenApiValidator } from './OpenApiValidator';
import express from 'express';
import request from 'supertest';

test('rejects missing fields', async ()=>{
  const v = new OpenApiValidator();
  await v.loadSpec();
  const app = express();
  app.use(express.json());
  app.use('/api', v.validate.bind(v));
  app.post('/api/tasks', (_req,res)=>res.json({ ok: true }));
  const res = await request(app).post('/api/tasks').send({ type: 'X' });
  expect(res.status).toBe(400);
});
