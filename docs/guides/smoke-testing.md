curl -s -X POST http://localhost:8080/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer localai-key" \
  -d '{"model":"hermes-2-pro-mistral","messages":[{"role":"user","content":"Say hello in three languages"}],"max_tokens":64}' \
  | jq .choices[0].message.content
