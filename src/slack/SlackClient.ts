interface BroadcastPayload {
    channel: string;
    blocks: any[];
}

export class SlackClient {
    static broadcast(payload: BroadcastPayload) {
        console.log(`Broadcasting to Slack channel ${payload.channel}:`);
        console.log(JSON.stringify(payload.blocks, null, 2));
    }
}