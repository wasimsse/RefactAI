# RefactAI - Comprehensive Hierarchical Code Smell Detection System

RefactAI is an advanced intelligent code refactoring assistant that helps developers detect and fix code smells in Java projects using state-of-the-art Large Language Models (LLMs) and comprehensive hierarchical detection algorithms.

## 🚀 Enhanced Features

### 🔍 **Comprehensive Code Smell Detection**
- **40+ Different Types** of code smells detected
- **Hierarchical Classification**: Class-Level, Method-Level, Design-Level, Code-Level, Architectural & Evolutionary
- **Advanced Detection Algorithms**: AST-based analysis, metrics-based detection, pattern-based detection
- **Developer-Friendly**: Clear descriptions and actionable suggestions for each smell

### 🤖 **AI-Powered Refactoring**
- **Multiple LLM Support**: Local models (Ollama) and cloud-based providers
- **Intelligent Suggestions**: Get smart recommendations for code improvements
- **Controlled Refactoring**: Step-by-step refactoring with approval workflows
- **Before/After Comparison**: Visual code comparison with impact analysis

### 📊 **Advanced Analytics**
- **Quality Metrics**: Track code quality improvements over time
- **Dependency Analysis**: Visualize and analyze code dependencies
- **Ripple Impact Analysis**: Understand the impact of changes across the codebase
- **Performance Monitoring**: Track refactoring performance and success rates

### 🧪 **Testing & Validation**
- **Testing Integration**: Ensure refactoring changes maintain code quality
- **Safety Validation**: Comprehensive safety checks before applying changes
- **Rollback Support**: Easy rollback of unsuccessful refactorings

## 🏗️ System Architecture

### **Backend (Spring Boot)**
- **Comprehensive Analysis Engine**: Multi-level code smell detection
- **Hierarchical Detectors**: Specialized detectors for different smell categories
- **LLM Integration**: Seamless integration with multiple LLM providers
- **RESTful APIs**: Complete API for frontend integration

### **Frontend (Next.js/React)**
- **Interactive Dashboard**: Modern, responsive web interface
- **Real-time Analysis**: Live code analysis and visualization
- **Enhanced Refactoring UI**: Intuitive refactoring workflow
- **Dependency Graphs**: Interactive dependency visualization

## 📋 Code Smell Categories

### **Class-Level Smells**
- ✅ **God Class / Large Class** - Classes doing too much (SRP violation)
- ✅ **Feature Envy** - Methods using more features of other classes
- ✅ **Data Class** - Classes with only data and no behavior
- ✅ **Lazy Class** - Classes that don't do enough to justify their existence

### **Method-Level Smells**
- ✅ **Long Method** - Methods that are too long and complex
- ✅ **Long Parameter List** - Methods with too many parameters
- ✅ **Message Chains** - Excessive chaining of method calls

### **Design-Level Smells**
- ✅ **Cyclic Dependencies** - Circular dependencies between modules
- ✅ **Tight Coupling** - High coupling between classes
- ✅ **Shotgun Surgery** - Changes require modifications in many places

### **Code-Level Smells**
- ✅ **Primitive Obsession** - Overuse of primitive types
- ✅ **Magic Numbers** - Hard-coded numeric literals
- ✅ **Duplicate Code** - Repeated code blocks
- ✅ **Dead Code** - Unused code that should be removed

## 🚀 Getting Started

### **Prerequisites**
- Java 17+
- Node.js 18+
- Maven 3.8+
- Python 3.8+ (for legacy Streamlit components)

### **Quick Start**

1. **Clone the repository:**
   ```bash
   git clone https://github.com/wasimsse/RefactAI.git
   cd RefactAI
   ```

2. **Start the Backend:**
   ```bash
   cd backend
   mvn spring-boot:run
   ```

3. **Start the Frontend:**
   ```bash
   cd web/app
   npm install
   npm run dev
   ```

4. **Access the Application:**
   - Frontend: http://localhost:4000
   - Backend API: http://localhost:8081

### **Legacy Streamlit Dashboard (Optional)**
```bash
# For the original Streamlit interface
pip install -r requirements.txt
streamlit run dashboard.py
```

## 🔧 Configuration

### **Environment Variables**
```bash
# LLM Configuration
OPENROUTER_API_KEY=your-openrouter-api-key
GPTLAB_BASE_URL=http://localhost:11434
GPTLAB_API_KEY=your-api-key

# Application Configuration
DEBUG=false
LOG_LEVEL=INFO
```

### **LLM Integration**
- **OpenRouter**: Cloud-based LLM access
- **Ollama**: Local model support
- **GPTlab**: Private cloud integration

## 📊 System Status

### **✅ Implemented Features**
- **Phase 1**: Foundation & Hierarchical Classification ✅
- **Phase 2**: Method-Level & Design-Level Detectors ✅
- **Backend API**: Complete RESTful API ✅
- **Frontend Dashboard**: Modern React interface ✅
- **LLM Integration**: Multiple provider support ✅
- **Cache Management**: Optimized performance ✅

### **🎯 Current Capabilities**
- **1016+ Code Smells** detected for complex Java files
- **18 Active Smell Types** with hierarchical classification
- **Real-time Analysis** with cache-busting
- **Developer-Friendly** descriptions and suggestions

## 🧪 Testing

### **Backend Testing**
```bash
cd backend
mvn test
```

### **Frontend Testing**
```bash
cd web/app
npm test
```

### **Integration Testing**
- Visit http://localhost:4000/test-enhanced-refactoring
- Test all API endpoints and functionality

## 📈 Performance

- **Analysis Speed**: Sub-second analysis for most files
- **Memory Usage**: Optimized for large codebases
- **Cache Efficiency**: Intelligent caching for repeated analyses
- **Scalability**: Handles projects with 1000+ files

## 🤝 Contributing

We welcome contributions! Please see our [Contributing Guidelines](CONTRIBUTING.md) for details.

### **Development Setup**
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **Ollama Project**: For local model support
- **GPTlab Team**: For cloud model integration
- **Spring Boot Community**: For excellent framework support
- **Next.js Team**: For modern React framework

## 📞 Support

- **Issues**: [GitHub Issues](https://github.com/wasimsse/RefactAI/issues)
- **Discussions**: [GitHub Discussions](https://github.com/wasimsse/RefactAI/discussions)
- **Documentation**: [Wiki](https://github.com/wasimsse/RefactAI/wiki)

---

**RefactAI** - Making code refactoring intelligent, comprehensive, and developer-friendly! 🚀