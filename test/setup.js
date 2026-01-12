import { TextEncoder, TextDecoder } from 'util';
import fetchMock from 'jest-fetch-mock';

global.TextEncoder = TextEncoder;
global.TextDecoder = TextDecoder;

fetchMock.enableMocks();
