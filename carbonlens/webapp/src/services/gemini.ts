import { GoogleGenerativeAI, GenerativeModel } from '@google/generative-ai'
import { AgentMessage, AgentPlan } from '@/types'

export class GeminiService {
  private genAI: GoogleGenerativeAI | null = null
  private model: GenerativeModel | null = null

  constructor(apiKey?: string) {
    if (apiKey) {
      this.initialize(apiKey)
    }
  }

  initialize(apiKey: string): void {
    this.genAI = new GoogleGenerativeAI(apiKey)
    this.model = this.genAI.getGenerativeModel({ 
      model: 'gemini-2.0-flash-exp',
      generationConfig: {
        temperature: 0.7,
        topK: 40,
        topP: 0.95,
        maxOutputTokens: 8192,
      }
    })
  }

  async plan(history: AgentMessage[]): Promise<AgentPlan> {
    if (!this.model) {
      throw new Error('Gemini service not initialized')
    }

    const systemPrompt = this.buildSystemPrompt()
    const conversationHistory = this.formatHistory(history)
    
    const prompt = `${systemPrompt}\n\n${conversationHistory}\n\nProvide your response as a JSON object with the following structure:
{
  "type": "tool_call" | "final",
  "tool": "tool_name", // only if type is "tool_call"
  "args": {...}, // only if type is "tool_call"
  "response": "your response", // only if type is "final"
  "reasoning": "your reasoning for this step"
}`

    try {
      const result = await this.model.generateContent(prompt)
      const response = result.response
      const text = response.text()

      const plan = this.parseAgentPlan(text)
      if (!plan) {
        // If parsing failed, try to get JSON from model again
        const retryPrompt = `${text}\n\nPlease format your response as valid JSON with the required structure.`
        const retryResult = await this.model.generateContent(retryPrompt)
        const retryText = retryResult.response.text()
        const retryPlan = this.parseAgentPlan(retryText)
        
        if (!retryPlan) {
          throw new Error('Failed to parse agent plan from Gemini response')
        }
        return retryPlan
      }

      return plan
    } catch (error) {
      console.error('Gemini API error:', error)
      throw new Error(`Gemini service error: ${error instanceof Error ? error.message : 'Unknown error'}`)
    }
  }

  async *streamPlan(history: AgentMessage[]): AsyncGenerator<string, AgentPlan, unknown> {
    if (!this.model) {
      throw new Error('Gemini service not initialized')
    }

    const systemPrompt = this.buildSystemPrompt()
    const conversationHistory = this.formatHistory(history)
    
    const prompt = `${systemPrompt}\n\n${conversationHistory}\n\nProvide your response as a JSON object.`

    try {
      const result = await this.model.generateContentStream(prompt)
      let fullText = ''

      for await (const chunk of result.stream) {
        const chunkText = chunk.text()
        fullText += chunkText
        yield chunkText
      }

      const plan = this.parseAgentPlan(fullText)
      if (!plan) {
        throw new Error('Failed to parse streamed agent plan')
      }

      return plan
    } catch (error) {
      console.error('Gemini streaming error:', error)
      throw new Error(`Gemini streaming error: ${error instanceof Error ? error.message : 'Unknown error'}`)
    }
  }

  private buildSystemPrompt(): string {
    return `You are CarbonLens, an expert AI agent specializing in carbon emissions analysis and sustainability research.

Your role is to help users analyze, compare, and optimize carbon footprints across different scenarios using REAL DATA from configured APIs.

🔑 CONFIGURED REAL APIs AVAILABLE:
1. **CarbonApiTool** - REAL Carbon Interface API - Get actual emission factors
2. **LCADatabaseTool** - REAL Climatiq API - Life cycle assessment data  
3. **ElectricityIntensityTool** - REAL ElectricityMap API - Live grid carbon intensity
4. **NewsSearchTool** - REAL News API - Current sustainability news
5. **EmissionEstimatorTool** - Monte Carlo simulation with real data inputs
6. **PageExtractorTool** - Extract specs from current web page
7. **NotifierTool** - Send notifications

⚠️ CRITICAL: You MUST use the real APIs above. Do NOT use sample/mock data.

🚫 IMPORTANT: If an API returns empty results (0 results), do NOT repeat the same query. Instead:
1. Try a broader, more generic search term (e.g., "TV manufacturing" instead of "Sony 55-inch OLED TV manufacturing")
2. If still no results, move on to the next tool in the sequence
3. NEVER make the same API call more than 2 times
4. Use realistic estimates based on similar products when APIs return empty data

SMART ANALYSIS PROCESS - Call the most relevant APIs for efficient analysis:

1. **For product comparisons, prioritize these tools (call 3-4 maximum):**
   - LCADatabaseTool OR CarbonApiTool (for emission data)
   - ElectricityIntensityTool (if regional usage is relevant)
   - EmissionEstimatorTool (for final comparison)
   - NewsSearchTool (optional, for recent news)

2. **IMPORTANT: After 3-4 tool calls, provide final analysis. Do NOT call more tools unnecessarily.**

3. **Example efficient sequences:**
   
   **For TV Analysis (OLED vs QLED vs LED):**
   - Tool 1: {"type": "tool_call", "tool": "CarbonApiTool", "args": {"action": "get_factors", "category": "electronics"}, "reasoning": "Getting TV manufacturing emission factors"}
   - Tool 2: {"type": "tool_call", "tool": "ElectricityIntensityTool", "args": {"action": "current", "region": "ap-south-1"}, "reasoning": "Getting Southern India electricity data for usage emissions"}
   - Tool 3: {"type": "tool_call", "tool": "EmissionEstimatorTool", "args": {"action": "compare", "scenarios": {"OLED": {...}, "QLED": {...}, "LED": {...}}, "samples": 1000}, "reasoning": "Comparing TV technologies"}
   - Tool 4: {"type": "final", "response": "Based on the analysis...", "reasoning": "Providing final comparison with recommendations"}

   **For Regional Analysis:**
   - Tool 1: {"type": "tool_call", "tool": "ElectricityIntensityTool", "args": {"action": "current", "region": "us-east-1"}, "reasoning": "Getting US East carbon intensity"}
   - Tool 2: {"type": "tool_call", "tool": "ElectricityIntensityTool", "args": {"action": "current", "region": "eu-west-1"}, "reasoning": "Getting EU West carbon intensity"}
   - Tool 3: {"type": "tool_call", "tool": "EmissionEstimatorTool", "args": {"action": "compare", "scenarios": {...}}, "reasoning": "Regional comparison"}
   - Tool 4: {"type": "final", "response": "Regional analysis shows...", "reasoning": "Final comparison results"}

4. **WHEN TO CONCLUDE - Provide final analysis when you have:**
   - At least 2-3 data points from APIs (even if some return empty results)
   - Enough information to make a meaningful comparison
   - After maximum 4-5 tool calls

5. **FINAL RESPONSE FORMAT:**
   {
     "type": "final",
     "response": "Based on the analysis of [products/regions], here are the key findings: [Carbon Footprint Comparison] Product A: X kg CO2e, Product B: Y kg CO2e [Usage Impact] Electricity intensity: Z gCO2/kWh [Recommendation] Clear recommendation with reasoning [Key Insights] 2-3 actionable insights",
     "reasoning": "Analysis complete with data from [list APIs used] providing comprehensive comparison"
   }

⚠️ CRITICAL RULES:
1. **Call 3-4 relevant tools maximum** - Don't over-analyze
2. **Provide final analysis after sufficient data** - Don't keep calling tools indefinitely
3. **Use realistic estimates** - If APIs return empty data, use reasonable assumptions
4. **Always conclude with actionable recommendations** - Give users clear guidance

**Decision Framework:**
- Got emission data? ✅ Move to regional analysis
- Got regional data? ✅ Move to comparison/estimation  
- Got comparison results? ✅ Provide final analysis
- Missing critical data? Use realistic estimates and note limitations

Response Format (MUST be valid JSON):
- Tool call: {"type": "tool_call", "tool": "ToolName", "args": {...}, "reasoning": "..."}
- Final answer: {"type": "final", "response": "...", "reasoning": "..."}

🚨 JSON FORMATTING RULES:
- NEVER include mathematical expressions (like 434 * 0.2) in JSON values
- ALWAYS calculate numbers before putting them in JSON
- ONLY return "tool_call" or "final" types, never "tool_result"
- Ensure all JSON is properly formatted and parseable`
  }

  private formatHistory(history: AgentMessage[]): string {
    return history
      .map(msg => `${msg.role.toUpperCase()}: ${msg.content}`)
      .join('\n\n')
  }

  private parseAgentPlan(text: string): AgentPlan | null {
    try {
      console.log('Raw Gemini response:', text)
      
      // Extract JSON from the response
      const jsonMatch = text.match(/\{[\s\S]*\}/)
      if (!jsonMatch) {
        console.log('No JSON found in response')
        return null
      }

      let jsonText = jsonMatch[0]
      
      // Fix mathematical expressions in JSON by evaluating them
      jsonText = jsonText.replace(/(\d+(?:\.\d+)?)\s*\*\s*(\d+(?:\.\d+)?)\s*\*\s*(\d+(?:\.\d+)?)\s*\/\s*(\d+(?:\.\d+)?)/g, (_, a, b, c, d) => {
        const result = (parseFloat(a) * parseFloat(b) * parseFloat(c)) / parseFloat(d)
        return result.toString()
      })
      
      // Fix other mathematical expressions
      jsonText = jsonText.replace(/(\d+(?:\.\d+)?)\s*\*\s*(\d+(?:\.\d+)?)/g, (_, a, b) => {
        const result = parseFloat(a) * parseFloat(b)
        return result.toString()
      })

      const parsed = JSON.parse(jsonText) as AgentPlan
      console.log('Parsed plan:', parsed)
      
      // Handle tool_result type by converting it to final type
      if ((parsed as any).type === 'tool_result') {
        console.log('Converting tool_result to final type')
        return {
          type: 'final',
          response: 'Analysis completed with tool results.',
          reasoning: 'Tool execution completed successfully'
        }
      }
      
      // Validate the structure
      if (!parsed.type || (parsed.type !== 'tool_call' && parsed.type !== 'final')) {
        console.log('Invalid plan type:', parsed.type)
        return null
      }

      if (parsed.type === 'tool_call' && (!parsed.tool || !parsed.args)) {
        console.log('Missing tool or args for tool_call:', parsed)
        return null
      }

      if (parsed.type === 'final' && !parsed.response) {
        console.log('Missing response for final:', parsed)
        return null
      }

      return parsed
    } catch (error) {
      console.error('Failed to parse agent plan:', error)
      console.error('Raw text was:', text)
      return null
    }
  }
}
