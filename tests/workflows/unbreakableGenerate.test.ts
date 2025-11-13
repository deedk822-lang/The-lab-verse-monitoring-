import { jest } from "@jest/globals";

test("unbreakableGenerate workflow works", async () => {
  const sleepMock = jest.fn().mockResolvedValue(undefined);
  const generateContentMock = jest.fn()
    .mockRejectedValueOnce(new Error("OpenAI failed"))
    .mockResolvedValue("Generated content");

  jest.unstable_mockModule('@workflow/core', () => ({
    __esModule: true,
    sleep: sleepMock,
  }));

  jest.unstable_mockModule('../kimi-computer/src/services/contentGenerator.js', () => ({
    __esModule: true,
    generateContent: generateContentMock,
  }));

  const { handleRequest } = await import("../../workflows/unbreakableGenerate");

  const result = await handleRequest("test prompt", "test-user");

  expect(result).toBe("Generated content");
  expect(generateContentMock).toHaveBeenCalledTimes(2);
  expect(sleepMock).toHaveBeenCalledWith("1 hour");
});
