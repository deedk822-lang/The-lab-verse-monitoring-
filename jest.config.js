// jest.config.js
const config = {
    verbose: true,
    testEnvironment: "jsdom",
    modulePaths: ["<rootDir>/src"],
    moduleNameMapper: {
        "^@workflow/(.*)$": "<rootDir>/src/workflows/$1.js",
        "^../../src/(.*)$": "<rootDir>/src/$1",
        "^workflow$": "<rootDir>/src/workflows/workflow.js"
    },
    transform: {
        "^.+\\.(js|jsx|ts|tsx)$": "babel-jest"
    },
    transformIgnorePatterns: [
        "/node_modules/(?!node-fetch|data-uri-to-buffer|fetch-blob|formdata-polyfill|@vercel/analytics)"
    ]
};

module.exports = config;
