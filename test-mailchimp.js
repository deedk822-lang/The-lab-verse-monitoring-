import dotenv from 'dotenv';

// Load environment variables from .env file FIRST
dotenv.config();

const runTest = async () => {
  // Dynamically import services AFTER dotenv has run
  const { default: mailchimpService } = await import('./src/services/mailchimpService.js');
  const { logger } = await import('./src/utils/logger.js');

  logger.info('Testing Mailchimp connection...');

  // Log the configuration being used, but mask the API key
  logger.info(`Mailchimp Server Prefix: ${process.env.MAILCHIMP_SERVER_PREFIX}`);
  logger.info(`Mailchimp List ID: ${process.env.MAILCHIMP_LIST_ID}`);
  logger.info(`Mailchimp API Key: ${process.env.MAILCHIMP_API_KEY ? 'Loaded' : 'Not Loaded'}`);


  if (!mailchimpService.apiKey || !mailchimpService.serverPrefix || !mailchimpService.listId) {
    logger.error('Mailchimp environment variables are not fully configured. Please check your .env file.');
    logger.error('Required variables: MAILCHIMP_API_KEY, MAILCHIMP_SERVER_PREFIX, MAILCHIMP_LIST_ID');
    process.exit(1);
  }

  const isConnected = await mailchimpService.testConnection();

  if (isConnected) {
    logger.info('✅ Mailchimp connection successful!');
    const listInfo = await mailchimpService.getListInfo();
    if (listInfo.success) {
        logger.info(`Successfully fetched list info for: ${listInfo.data.name}`);
    } else {
        logger.warn('Could not fetch list details, but connection test passed.');
    }
  } else {
    logger.error('❌ Mailchimp connection failed. Please check your API key and server prefix.');
    const listInfo = await mailchimpService.getListInfo();
    logger.error('Error details:', listInfo.error);
    process.exit(1);
  }
};

runTest();
