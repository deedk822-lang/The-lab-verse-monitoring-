import { render, screen } from '@testing-library/react';
import React from 'react';
import App from './App';

describe('App', () => {
  it('renders headline', () => {
    render(<App />);
    const headline = screen.getByText(/Welcome to the LapVerse AI Brain Trust!/i);
    expect(headline).toBeInTheDocument();
  });
});
