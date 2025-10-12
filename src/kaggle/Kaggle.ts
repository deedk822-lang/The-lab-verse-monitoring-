import { EventEmitter } from 'events';

class KaggleEmitter extends EventEmitter {}

// A placeholder for the real Kaggle class.
// It emits a 'competition:completed' event to be used by the FinOpsEngine.
export const Kaggle = new KaggleEmitter();