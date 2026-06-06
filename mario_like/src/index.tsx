#!/usr/bin/env node
import React from 'react';
import { render } from 'ink';
import App from './App.js';

const app = render(<App />);

await app.waitUntilExit();
