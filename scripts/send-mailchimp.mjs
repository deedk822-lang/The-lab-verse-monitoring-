import fs from 'fs/promises';
import fetch from 'node-fetch';

export async function sendMailChimp() {
  try {
    const content = JSON.parse(await fs.readFile('./tmp/content-bundle.json', 'utf8'));

    console.log('📧 Sending MailChimp campaign...');

    const response = await fetch(`https://${process.env.MAILCHIMP_DC}.api.mailchimp.com/3.0/campaigns`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${process.env.MAILCHIMP_API_KEY}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        type: 'regular',
        recipients: { list_id: process.env.MAILCHIMP_LIST_ID },
        settings: {
          subject_line: `🚨 Crisis Alert: ${content.crisis_id}`,
          from_name: 'Crisis Monitor SA',
          reply_to: 'noreply@deedk822.wordpress.com',
          title: `Crisis-${content.crisis_id}`
        }
      })
    });

    if (!response.ok) {
      throw new Error(`MailChimp API error: ${response.statusText}`);
    }

    const campaign = await response.json();

    // Set content
    const setContentResponse = await fetch(`https://${process.env.MAILCHIMP_DC}.api.mailchimp.com/3.0/campaigns/${campaign.id}/content`, {
      method: 'PUT',
      headers: {
        'Authorization': `Bearer ${process.env.MAILCHIMP_API_KEY}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        html: content.newsletter.replace(
          '[SPONSOR]',
          `<p>Sponsored by <strong>Emergency Response Corp</strong> - <a href="https://emergency-response.link">Learn More</a></p>`
        )
      })
    });

    if (!setContentResponse.ok) {
      throw new Error(`MailChimp API error (setting content): ${setContentResponse.statusText}`);
    }

    // Send
    const sendResponse = await fetch(`https://${process.env.MAILCHIMP_DC}.api.mailchimp.com/3.0/campaigns/${campaign.id}/actions/send`, {
      method: 'POST',
      headers: { 'Authorization': `Bearer ${process.env.MAILCHIMP_API_KEY}` }
    });

    if (!sendResponse.ok) {
      throw new Error(`MailChimp API error (sending): ${sendResponse.statusText}`);
    }

    console.log('✅ MailChimp sent');

  } catch (error) {
    console.error('❌ Error sending MailChimp campaign:', error);
    process.exit(1);
  }
}

sendMailChimp();
