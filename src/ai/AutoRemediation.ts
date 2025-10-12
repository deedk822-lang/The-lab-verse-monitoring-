import { EventEmitter } from 'events';

class AutoRemediationEmitter extends EventEmitter {}

// A placeholder for the real AutoRemediation class.
// It emits a 'success' event to be used by the FinOpsEngine.
export const AutoRemediation = new AutoRemediationEmitter();