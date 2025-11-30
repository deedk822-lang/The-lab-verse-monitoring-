#!/usr/bin/env node

import fs from 'fs';
import path from 'path';
import { execSync } from 'child_process';

console.log('🚀 Setting up AI Content Creation Suite...\n');

// Check Node.js version
const nodeVersion = process.version;
const requiredVersion = '18.0.0';
if (nodeVersion < `v${requiredVersion}`) {
    console.error(`❌ Node.js ${requiredVersion} or higher is required. Current version: ${nodeVersion}`);
    process.exit(1);
}
console.log(`✅ Node.js version: ${nodeVersion}`);

// Check if .env file exists
const envPath = '.env';
if (!fs.existsSync(envPath)) {
    console.log('📝 Creating .env file from template...');
    fs.copyFileSync('.env.example', '.env');
    console.log('✅ .env file created. Please configure your API keys.');
} else {
    console.log('✅ .env file already exists');
}

// Create necessary directories
const directories = ['logs', 'uploads', 'public/js'];
directories.forEach(dir => {
    if (!fs.existsSync(dir)) {
        fs.mkdirSync(dir, { recursive: true });
        console.log(`✅ Created directory: ${dir}`);
    }
});

// Install dependencies
console.log('\n📦 Installing dependencies...');
try {
    execSync('npm install', { stdio: 'inherit' });
    console.log('✅ Dependencies installed successfully');
} catch (error) {
    console.error('❌ Failed to install dependencies:', error.message);
    process.exit(1);
}

// Test Redis connection
console.log('\n🔍 Testing Redis connection...');
try {
    const { connectRedis } = await import('../src/utils/redis.js');
    const redis = await connectRedis();
    await redis.ping();
    console.log('✅ Redis connection successful');
} catch (error) {
    console.log('⚠️  Redis connection failed. Make sure Redis is running.');
    console.log('   You can start Redis with: redis-server');
}

// Test providers
console.log('\n🤖 Testing AI providers...');
try {
    const { ProviderFactory } = await import('../src/services/ProviderFactory.js');
    const results = await ProviderFactory.testAllProviders();
    
    Object.entries(results).forEach(([provider, result]) => {
        if (result.success) {
            console.log(`✅ ${provider}: OK`);
        } else {
            console.log(`⚠️  ${provider}: ${result.error}`);
        }
    });
} catch (error) {
    console.log('⚠️  Provider testing failed:', error.message);
}

console.log('\n🎉 Setup completed!');
console.log('\nNext steps:');
console.log('1. Configure your API keys in the .env file');
console.log('2. Start the application: npm start');
console.log('3. Open http://localhost:3000 in your browser');
console.log('\nFor Docker deployment:');
console.log('1. docker-compose up -d');
console.log('2. Open http://localhost in your browser');