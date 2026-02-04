export const costTracker = {
  trackAPICall(provider, model, { inputTokens, outputTokens, duration, status }) {
    console.log(
      `[cost] ${provider}/${model} – in:${inputTokens} out:${outputTokens} dur:${duration}ms status:${status}`
    );
  }
};
