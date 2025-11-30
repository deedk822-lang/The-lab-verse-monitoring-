#!/usr/bin/env node

/**
 * Test script for Mistral & LocalAI integration
 * Validates that LocalAI, Mistral, and MCP servers are working correctly
 */

import { config } from "dotenv";
import { createOpenAI } from "@ai-sdk/openai";

// Load environment variables
config();

console.log("🔍 Testing Mistral & LocalAI Integration\n");

async function testLocalAI() {
  console.log("1️⃣ Testing LocalAI connection...");
  
  try {
    const localai = createOpenAI({
      baseURL: process.env.LOCALAI_API_URL || "http://localhost:8080/v1",
      apiKey: process.env.LOCALAI_API_KEY || "localai-key",
    });

    const modelsResponse = await fetch(`${process.env.LOCALAI_API_URL || "http://localhost:8080/v1"}/models`, {
      headers: {
        "Authorization": `Bearer ${process.env.LOCALAI_API_KEY || "localai-key"}`
      }
    });

    if (!modelsResponse.ok) {
      throw new Error(`Failed to fetch models: ${modelsResponse.status}`);
    }

    const models = await modelsResponse.json();
    console.log("   ✅ LocalAI models loaded:", models.data.map(m => m.id).join(", "));

    // Test completion
    const completion = await localai.chat.completions.create({
      model: "hermes-2-pro-mistral",
      messages: [{ role: "user", content: "Say hello in exactly 3 words." }],
      max_tokens: 10,
    });

    console.log("   ✅ LocalAI response:", completion.choices[0].message.content.trim());
    return true;

  } catch (error) {
    console.log("   ❌ LocalAI test failed:", error.message);
    return false;
  }
}

async function testMistral() {
  console.log("\n2️⃣ Testing Mistral provider...");
  
  try {
    const mistral = createOpenAI({
      baseURL: process.env.MISTRAL_API_URL || "http://localhost:8080/v1",
      apiKey: process.env.MISTRAL_API_KEY || "localai-key",
    });

    const completion = await mistral.chat.completions.create({
      model: "hermes-2-pro-mistral",
      messages: [{ role: "user", content: "What is 2 + 2? Answer with just the number." }],
      max_tokens: 5,
    });

    console.log("   ✅ Mistral response:", completion.choices[0].message.content.trim());
    return true;

  } catch (error) {
    console.log("   ❌ Mistral test failed:", error.message);
    return false;
  }
}

async function testMCPServer() {
  console.log("\n3️⃣ Testing MCP Server...");
  
  try {
    const response = await fetch(`${process.env.MCP_SERVER_URL || "http://localhost:8000"}/health`, {
      method: "GET",
      headers: {
        "Content-Type": "application/json",
        ...(process.env.MCP_API_KEY && { "Authorization": `Bearer ${process.env.MCP_API_KEY}` })
      }
    });

    if (!response.ok) {
      throw new Error(`MCP server health check failed: ${response.status}`);
    }

    const health = await response.json();
    console.log("   ✅ MCP Server health:", health);
    return true;

  } catch (error) {
    console.log("   ❌ MCP Server test failed:", error.message);
    return false;
  }
}

async function testProviderConfig() {
  console.log("\n4️⃣ Testing Provider Configuration...");
  
  try {
    // Import and test the provider configuration
    const { providers, getActiveProvider } = await import("./src/config/providers.js");
    
    console.log("   🔧 Available providers:");
    Object.entries(providers).forEach(([key, config]) => {
      console.log(`      ${key}: ${config.enabled ? '✅' : '❌'} (${config.name})`);
    });

    // Test getting an active provider
    const activeProvider = getActiveProvider();
    if (activeProvider) {
      console.log("   ✅ Active provider found:", activeProvider.name || "Unknown");
      return true;
    } else {
      console.log("   ❌ No active providers available");
      return false;
    }

  } catch (error) {
    console.log("   ❌ Provider config test failed:", error.message);
    return false;
  }
}

async function main() {
  console.log("🎯 Running integration tests...\n");

  const results = {
    localai: await testLocalAI(),
    mistral: await testMistral(),
    mcpServer: await testMCPServer(),
    providerConfig: await testProviderConfig(),
  };

  console.log("\n📊 Test Results Summary:");
  console.log("   LocalAI:", results.localai ? "✅ PASS" : "❌ FAIL");
  console.log("   Mistral:", results.mistral ? "✅ PASS" : "❌ FAIL");
  console.log("   MCP Server:", results.mcpServer ? "✅ PASS" : "❌ FAIL");
  console.log("   Provider Config:", results.providerConfig ? "✅ PASS" : "❌ FAIL");

  const passed = Object.values(results).filter(Boolean).length;
  const total = Object.keys(results).length;

  console.log(`\n🏆 Overall: ${passed}/${total} tests passed`);

  if (passed === total) {
    console.log("🎉 All tests passed! Your Mistral & LocalAI setup is working correctly.");
    process.exit(0);
  } else {
    console.log("⚠️  Some tests failed. Check the configuration and try again.");
    process.exit(1);
  }
}

main().catch(console.error);