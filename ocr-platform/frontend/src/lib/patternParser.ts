/**
 * Human Pattern Language helpers and API client.
 */

export interface PatternTokenHelp {
  token: string;
  label: string;
  example: string;
}

export const PATTERN_TOKENS: PatternTokenHelp[] = [
  { token: '{YYYY}', label: '4-digit Year', example: '2026' },
  { token: '{YY}', label: '2-digit Year', example: '26' },
  { token: '{MM}', label: '2-digit Month', example: '09' },
  { token: '{DD}', label: '2-digit Day', example: '15' },
  { token: '{NNNNNN}', label: '6 Numbers', example: '001234' },
  { token: '{NNNN}', label: '4 Numbers', example: '1234' },
  { token: '{NN}', label: '2 Numbers', example: '12' },
  { token: '{N}', label: '1 Number', example: '5' },
  { token: '{AAAA}', label: '4 Letters', example: 'WXYZ' },
  { token: '{AAA}', label: '3 Letters', example: 'ABC' },
  { token: '{AA}', label: '2 Letters', example: 'US' },
  { token: '{A}', label: '1 Letter', example: 'X' },
  { token: '{MONEY}', label: 'Currency', example: '$1,250.00' },
  { token: '{EMAIL}', label: 'Email', example: 'user@example.com' },
  { token: '{PHONE}', label: 'Phone', example: '+1-555-0199' },
  { token: '{TEXT}', label: 'Words', example: 'Sample Text' },
];

export const patternParserApi = {
  async compile(humanPattern: string, ocrTolerant: boolean = false) {
    const res = await fetch('/api/pattern-parser/compile', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ human_pattern: humanPattern, ocr_tolerant: ocrTolerant }),
    });
    if (!res.ok) throw new Error('Failed to compile pattern');
    return res.json();
  },

  async fromExamples(examples: string[]) {
    const res = await fetch('/api/pattern-parser/from-examples', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ examples }),
    });
    if (!res.ok) throw new Error('Failed to infer from examples');
    return res.json();
  },

  async fromDescription(description: string) {
    const res = await fetch('/api/pattern-parser/from-description', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ description }),
    });
    if (!res.ok) throw new Error('Failed to infer from description');
    return res.json();
  },
};
