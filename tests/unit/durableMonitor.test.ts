import { jest } from "@jest/globals";

test("fallback chain still works", async () => {
  const sleepMock = jest.fn().mockResolvedValue(undefined);

  jest.unstable_mockModule('@workflow/core', () => ({
    __esModule: true,
    sleep: sleepMock,
  }));

  const { POST } = await import("../../api/workflows/durableMonitor");

  const req = {
    json: async () => ({
      prompt: "hello",
      userId: "u123",
      platforms: [],
    }),
    headers: {
      get: (header: string) => {
        if (header === "x-workflow-id") {
          return "test-id";
        }
        return null;
      },
    },
  };

  // @ts-ignore
  const res = await POST(req);
  expect(res.status).toBe(200);
  expect(sleepMock).toHaveBeenCalledWith("1 second");
});
