export interface MigrationJob {
  id: string;
  name: string;
  aplCode: string;
  pythonCode?: string;
  explanation?: string;
  status: 'pending' | 'processing' | 'completed' | 'failed';
  score?: MigrationScore;
  createdAt: string;
}

export interface MigrationScore {
  syntax: number;
  complexity: number;
  conversion: number;
  confidence: number;
  semanticMatch: number;
  overall: number;
}

export interface TestCase {
  id: string;
  input: string;
  expectedOutput: string;
  metadata: {
    operatorType: string;
    isEdgeCase: boolean;
  };
}
