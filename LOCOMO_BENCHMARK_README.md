# LoCoMo Benchmark for Memori

This directory contains the complete **LoCoMo (Long-Term Conversational Memory)** benchmark implementation for evaluating Memori's conversational memory capabilities using the standardized LoCoMo evaluation framework.

## 🎯 What is LoCoMo?

LoCoMo evaluates AI systems on long-term conversational memory across:
- **300-turn conversations** spanning multiple sessions
- **5 question types**: Single-hop, Multi-hop, Temporal, Open-domain knowledge, Adversarial  
- **LLM-as-a-Judge scoring** for comprehensive evaluation
- **Performance metrics**: Latency, token usage, accuracy

## 📊 Performance Standards

LoCoMo benchmark performance targets:
- **J-Score ≥70%** (High performance threshold)
- **F1 Score ≥80%** (Strong accuracy target)
- **Latency ≤2s per query** (Efficiency target)  
- **High scores across all question categories** (Consistent performance)

## 🚀 Quick Start

### Prerequisites
1. **Python 3.8+** with required dependencies
2. **OpenAI API Key** for real AI processing
3. **LoCoMo dataset** (automatically loaded)

```bash
# Set your OpenAI API key
export OPENAI_API_KEY="your_api_key_here"  # Linux/Mac
set OPENAI_API_KEY=your_api_key_here       # Windows
```

### Option 1: Quick Demo (5-10 minutes)
Perfect for testing and development:

```bash
python locomo_benchmark_quick_demo.py
```

**What it does:**
- Processes 1 conversation (~400 turns)
- Evaluates 20 questions across 5 categories
- Demonstrates complete pipeline
- Shows performance vs baselines
- **Cost:** ~$2-5

### Option 2: Full Benchmark (2-3 hours)
Complete evaluation for OSS community:

```bash
python locomo_full_benchmark.py
```

**What it does:**
- Processes all 10 conversations (6,000+ turns) 
- Evaluates all ~2,000 questions
- Comprehensive performance analysis
- Detailed category breakdown
- **Cost:** ~$20-40

## 📁 Benchmark Architecture

```
memori/
├── locomo/                     # Core LoCoMo implementation
│   ├── __init__.py
│   ├── data_models.py          # Pydantic models for LoCoMo data
│   ├── data_loader.py          # Dataset loading and validation
│   ├── real_memory_processor.py# Real AI memory processing
│   └── benchmark_suite.py      # Main orchestrator
├── evaluation/                 # Evaluation components
│   ├── qa_evaluator.py         # Question-answering evaluation
│   ├── summary_evaluator.py    # Event summarization
│   └── judge_client.py         # LLM-as-a-Judge scoring
├── metrics/                    # Performance tracking
│   ├── performance_tracker.py  # Latency/token metrics
│   └── score_calculator.py     # F1/accuracy computation
└── agents/                     # Memory processing
    ├── memory_agent.py         # OpenAI Structured Outputs
    └── retrieval_agent.py      # Multi-strategy search
```

## 📊 Expected Performance Range

Typical performance characteristics:
- **J-Score: 65-85%** depending on conversation complexity
- **F1 scores: 75-90%** across different question types
- **Latency: 1-3s per query** with real AI processing
- **Memory processing: Real AI** with OpenAI Structured Outputs

## 🔧 Configuration Options

### Benchmark Suite Options
```python
benchmark = LocomotBenchmarkSuite(
    database_path=None,      # Auto-creates temp DB
    namespace="benchmark",   # Data isolation
    use_real_ai=True        # Use real AI vs rule-based
)

# Run with custom limits
report = benchmark.run_full_benchmark(
    max_conversations=10,    # None for all
    max_questions=None,      # None for all ~2000
    output_path="results.json"
)
```

### Memory Agent Configuration
```python
memory_agent = MemoryAgent(
    api_key=None,           # Uses OPENAI_API_KEY env var
    model="gpt-4o"         # Structured output model
)
```

## 📈 Understanding Results

### Key Metrics Explained

1. **J-Score (Judge Score)**: LLM-as-a-Judge evaluation (0-100%)
   - Primary metric for overall performance assessment  
   - Target: ≥70% for high performance classification

2. **F1 Score**: Token-level overlap between predicted and ground truth
   - Macro-averaged across all questions
   - Higher values indicate better accuracy

3. **Exact Match**: Percentage of perfect answers
   - Strict evaluation metric
   - Good indicator of precision

4. **Response Latency**: Average time per query processing
   - Target: ≤2 seconds for efficient operation
   - Measures system responsiveness

### Question Categories

1. **Single-hop**: Direct factual questions
2. **Multi-hop**: Require connecting multiple facts  
3. **Temporal**: Time-based reasoning
4. **Open-domain**: General knowledge questions
5. **Adversarial**: Resistance to incorrect information

## 🐛 Troubleshooting

### Common Issues

1. **OpenAI API Key Error**
   ```
   The api_key client option must be set
   ```
   **Solution:** Set `OPENAI_API_KEY` environment variable

2. **Database Constraint Error**
   ```
   NOT NULL constraint failed: long_term_memory.created_at
   ```
   **Solution:** Already fixed in latest version

3. **Memory Processing Takes Too Long**
   - This is expected with real AI processing
   - Each conversation takes 10-15 minutes
   - Consider using quick demo for testing

4. **High API Costs**
   - Quick demo: $2-5
   - Full benchmark: $20-40
   - Adjust `max_conversations` and `max_questions` to control costs

### Performance Tips

1. **Use Quick Demo First**: Validate system before full run
2. **Monitor API Usage**: Check OpenAI dashboard
3. **Run Incrementally**: Use `max_conversations` parameter
4. **Save Results**: Always specify `output_path`

## 📄 Output Files

After running benchmarks, you'll get:

1. **JSON Results**: Complete benchmark data
   - `locomo_demo_results.json` (quick demo)
   - `locomo_full_benchmark_YYYYMMDD_HHMMSS.json` (full)

2. **Log Files**: Detailed execution logs
   - `locomo_full_benchmark.log` (full benchmark only)

3. **Database**: Temporary SQLite file with processed memories
   - Auto-cleaned after completion
   - Can be preserved by specifying `database_path`

## 🤝 For OSS Community

This benchmark enables:

1. **Performance Comparison**: Direct comparison with research baselines and other systems
2. **Continuous Evaluation**: Track improvements over time  
3. **Research Validation**: Reproducible results for papers
4. **System Optimization**: Identify areas for improvement

### Citing This Work

When using this benchmark in research:

```bibtex
@software{memori_locomo_benchmark,
  title={LoCoMo Benchmark Implementation for Memori},
  author={Memori Development Team},
  year={2025},
  url={https://github.com/your-repo/memori}
}
```

## 🔄 Next Steps

1. **Run Quick Demo**: Validate your setup
2. **Execute Full Benchmark**: Get comprehensive results
3. **Analyze Results**: Review category-specific performance
4. **Share with Community**: Contribute to OSS evaluation standards
5. **Iterate and Improve**: Use results to enhance Memori

## 📞 Support

- **Issues**: Create GitHub issues for problems
- **Questions**: Discussion forum or community chat
- **Contributions**: PRs welcome for improvements

---

**Ready to benchmark Memori? Start with the quick demo!**

```bash
python locomo_benchmark_quick_demo.py
```