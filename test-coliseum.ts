import { AutoRemediation } from './src/ai/AutoRemediation';
import { SystemAnomaly } from './src/ai/AutoRemediation';

async function testColiseum() {
    console.log('=== Testing Lap-Verse Coliseum ===\n');
    
    // Create a high-stakes anomaly (error rate > 0.2)
    const highStakesAnomaly: SystemAnomaly = {
        tenantId: 'acme',
        signature: 'auth-service-cpu-spike',
        service: 'auth-service',
        errorRate: 0.35 // 35% error rate - triggers Coliseum
    };
    
    console.log('Testing HIGH-STAKES anomaly (error rate > 0.2):');
    console.log(JSON.stringify(highStakesAnomaly, null, 2));
    console.log('\nInitiating Coliseum competition...\n');
    
    try {
        const result = await AutoRemediation.execute(highStakesAnomaly);
        console.log('\n=== Coliseum Competition Complete ===');
        console.log('Champion:', JSON.stringify(result, null, 2));
    } catch (error) {
        console.error('Error during Coliseum competition:', error);
    }
    
    console.log('\n\n=== Testing LOW-STAKES anomaly (error rate < 0.2) ===\n');
    
    // Create a low-stakes anomaly (error rate < 0.2)
    const lowStakesAnomaly: SystemAnomaly = {
        tenantId: 'acme',
        signature: 'cache-service-latency',
        service: 'cache-service',
        errorRate: 0.15 // 15% error rate - simple remediation
    };
    
    console.log('Testing LOW-STAKES anomaly (error rate < 0.2):');
    console.log(JSON.stringify(lowStakesAnomaly, null, 2));
    console.log('\nPerforming simple remediation...\n');
    
    try {
        await AutoRemediation.execute(lowStakesAnomaly);
    } catch (error) {
        console.error('Error during simple remediation:', error);
    }
    
    console.log('\n=== Test Complete ===');
}

testColiseum();

