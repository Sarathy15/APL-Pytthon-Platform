import { askAI } from "../lib/gemini";
import { MigrationJob, MigrationScore } from "../types";

export class MigrationService {
  static async understandAPL(aplCode: string) {
    return await askAI("/api/understand", { apl_code: aplCode });
  }

  static async convertToPython(aplCode: string, explanation: any) {
    return await askAI("/api/convert", { apl_code: aplCode, explanation });
  }

  static async generateTests(aplCode: string, pythonCode: string) {
    return await askAI("/api/tests", { apl_code: aplCode, python_code: pythonCode });
  }

  static calculateFinalScore(explanation: any, conversion: any, tests: any): MigrationScore {
    // Simulated enterprise scoring logic based on PDF formulas
    const confidence = conversion.confidence_score * 100 || 85;
    const complexity = explanation.complexity === 'low' ? 95 : explanation.complexity === 'medium' ? 80 : 60;
    
    return {
      syntax: 98,
      complexity,
      conversion: confidence,
      confidence: (confidence + complexity) / 2,
      semanticMatch: 95,
      overall: (confidence + complexity + 95) / 3
    };
  }
}
