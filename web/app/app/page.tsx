'use client';

import { useRouter } from 'next/navigation';
import { 
  Search,
  Zap, 
  Shield, 
  Code, 
  BarChart3, 
  Play,
  ArrowRight,
  GitBranch
} from 'lucide-react';

export default function HomePage() {
  const router = useRouter();

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900">
      {/* Header */}
      <header className="border-b border-slate-700/50 bg-slate-900/80 backdrop-blur-xl sticky top-0 z-50">
        <div className="container mx-auto px-8 py-6">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-4">
              <div className="text-3xl font-bold text-blue-400">R⚙️</div>
              <h1 className="text-2xl font-bold text-white tracking-tight">RefactAI</h1>
            </div>
            <nav className="hidden lg:flex items-center space-x-8">
              <a href="/dashboard" className="text-slate-300 hover:text-white transition-colors duration-200 font-medium">Dashboard</a>
              <a href="#features" className="text-slate-300 hover:text-white transition-colors duration-200 font-medium">Features</a>
              <a href="#docs" className="text-slate-300 hover:text-white transition-colors duration-200 font-medium">Documentation</a>
              <button 
                onClick={() => router.push('/dashboard')}
                className="bg-blue-600 hover:bg-blue-700 text-white px-6 py-3 rounded-lg transition-all duration-200 font-semibold shadow-lg hover:shadow-xl transform hover:scale-105"
              >
                Open Dashboard
              </button>
            </nav>
          </div>
        </div>
      </header>

      {/* Hero Section */}
      <section className="container mx-auto px-8 py-24">
        <div className="text-center max-w-6xl mx-auto">
          <div className="flex items-center justify-center mb-12">
            <div className="text-8xl mr-6 text-blue-400 font-bold">R⚙️</div>
            <div className="text-left">
              <h1 className="text-6xl lg:text-8xl font-black text-white mb-4 tracking-tight leading-tight">
                RefactAI
              </h1>
              <p className="text-3xl lg:text-4xl text-blue-400 font-bold tracking-wide">Professional Java Refactoring Suite</p>
            </div>
          </div>
          
          <p className="text-2xl text-slate-300 mb-16 leading-relaxed max-w-4xl mx-auto font-light">
            Transform your Java codebase with AI-powered analysis. Identify code smells, 
            plan refactoring strategies, and safely apply transformations with our 
            assessment-first workflow.
          </p>

          {/* Dashboard Access Message */}
          <div className="bg-gradient-to-r from-blue-500/20 to-purple-500/20 border border-blue-500/30 rounded-2xl p-6 mb-16 max-w-4xl mx-auto text-center">
            <div className="flex items-center justify-center mb-3">
              <BarChart3 className="w-8 h-8 text-blue-400 mr-3" />
              <h3 className="text-xl font-bold text-blue-400">Enhanced Dashboard Available!</h3>
            </div>
            <p className="text-slate-300 text-lg mb-4">
              Our professional Code Analysis Dashboard is ready with individual file analysis, code smells detection, and security scanning.
            </p>
            <button 
              onClick={() => router.push('/dashboard')}
              className="bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-700 hover:to-purple-700 text-white px-8 py-3 rounded-xl font-semibold transition-all duration-200 transform hover:scale-105 border border-blue-400/50"
            >
              Access Dashboard Now
            </button>
          </div>
          
          <div className="flex items-center justify-center space-x-6 mb-20">
            <button 
              onClick={() => router.push('/dashboard')}
              className="bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-700 hover:to-purple-700 text-white px-12 py-6 rounded-2xl text-2xl font-bold transition-all duration-300 transform hover:scale-105 shadow-2xl hover:shadow-blue-500/25 flex items-center group border-2 border-blue-400/50"
            >
              <BarChart3 size={32} className="mr-4" />
              Go to Dashboard
              <ArrowRight size={28} className="ml-4 group-hover:translate-x-1 transition-transform duration-200" />
            </button>
            <button className="bg-slate-700 hover:bg-slate-600 text-white px-10 py-5 rounded-2xl text-xl font-bold transition-all duration-300 transform hover:scale-105 shadow-xl flex items-center">
              <Play size={28} className="mr-4" />
              Quick Demo
            </button>
          </div>

          {/* Auto-redirect Message */}
          {/* Removed auto-redirect message as per edit hint */}
          
        </div>
      </section>

      {/* Features Section */}
      <section id="features" className="container mx-auto px-8 py-24">
        <div className="text-center mb-20">
          <h2 className="text-5xl font-black text-white mb-8 tracking-tight">Why Choose RefactAI?</h2>
          <p className="text-2xl text-slate-300 max-w-4xl mx-auto font-light leading-relaxed">
            Professional-grade tools designed for enterprise Java development teams
          </p>
        </div>

        <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-10">
          <div className="bg-slate-800/50 backdrop-blur-sm rounded-2xl p-10 border border-slate-700/50 hover:border-blue-500/50 transition-all duration-300 transform hover:scale-105 group">
            <div className="w-20 h-20 bg-blue-500/10 rounded-2xl flex items-center justify-center mb-8 group-hover:bg-blue-500/20 transition-all duration-300">
              <Search className="text-blue-400" size={40} />
            </div>
            <h3 className="text-2xl font-bold text-white mb-6">Assessment-First</h3>
            <p className="text-slate-300 leading-relaxed text-lg font-light">
              Analyze code quality before making changes with comprehensive smell detection and metrics analysis.
            </p>
          </div>

          <div className="bg-slate-800/50 backdrop-blur-sm rounded-2xl p-10 border border-slate-700/50 hover:border-emerald-500/50 transition-all duration-300 transform hover:scale-105 group">
            <div className="w-20 h-20 bg-emerald-500/10 rounded-2xl flex items-center justify-center mb-8 group-hover:bg-emerald-500/20 transition-all duration-300">
              <Code className="text-emerald-400" size={40} />
            </div>
            <h3 className="text-2xl font-bold text-white mb-6">Plugin Architecture</h3>
            <p className="text-slate-300 leading-relaxed text-lg font-light">
              Extensible detectors and transforms via SPI for custom refactoring rules and enterprise needs.
            </p>
          </div>

          <div className="bg-slate-800/50 backdrop-blur-sm rounded-2xl p-10 border border-slate-700/50 hover:border-amber-500/50 transition-all duration-300 transform hover:scale-105 group">
            <div className="w-20 h-20 bg-amber-500/10 rounded-2xl flex items-center justify-center mb-8 group-hover:bg-amber-500/20 transition-all duration-300">
              <Shield className="text-amber-400" size={40} />
            </div>
            <h3 className="text-2xl font-bold text-white mb-6">Enterprise Security</h3>
            <p className="text-slate-300 leading-relaxed text-lg font-light">
              All processing happens locally by default with no code sent externally. Perfect for sensitive codebases.
            </p>
          </div>

          <div className="bg-slate-800/50 backdrop-blur-sm rounded-2xl p-10 border border-slate-700/50 hover:border-purple-500/50 transition-all duration-300 transform hover:scale-105 group">
            <div className="w-20 h-20 bg-purple-500/10 rounded-2xl flex items-center justify-center mb-8 group-hover:bg-purple-500/20 transition-all duration-300">
              <Zap className="text-purple-400" size={40} />
            </div>
            <h3 className="text-2xl font-bold text-white mb-6">Deterministic Results</h3>
            <p className="text-slate-300 leading-relaxed text-lg font-light">
              Same input produces same output with version-pinned formatters and consistent analysis.
            </p>
          </div>

          <div className="bg-slate-800/50 backdrop-blur-sm rounded-2xl p-10 border border-slate-700/50 hover:border-red-500/50 transition-all duration-300 transform hover:scale-105 group">
            <div className="w-20 h-20 bg-red-500/10 rounded-2xl flex items-center justify-center mb-8 group-hover:bg-red-500/20 transition-all duration-300">
              <BarChart3 className="text-red-400" size={40} />
            </div>
            <h3 className="text-2xl font-bold text-white mb-6">Multiple Interfaces</h3>
            <p className="text-slate-300 leading-relaxed text-lg font-light">
              CLI, Web UI, and VS Code extension for different workflow preferences and team needs.
            </p>
          </div>

          <div className="bg-slate-800/50 backdrop-blur-sm rounded-2xl p-10 border border-slate-700/50 hover:border-blue-500/50 transition-all duration-300 transform hover:scale-105 group">
            <div className="w-20 h-20 bg-blue-500/10 rounded-2xl flex items-center justify-center mb-8 group-hover:bg-blue-500/20 transition-all duration-300">
              <GitBranch className="text-blue-400" size={40} />
            </div>
            <h3 className="text-2xl font-bold text-white mb-6">Git Integration</h3>
            <p className="text-slate-300 leading-relaxed text-lg font-light">
              Direct analysis of Git repositories with branch and commit support for modern workflows.
            </p>
          </div>
        </div>
      </section>

      {/* Stats Section */}
      <section className="container mx-auto px-8 py-24">
        <div className="bg-slate-800/50 backdrop-blur-sm rounded-3xl p-16 text-center border border-slate-700/50 shadow-2xl">
          <h2 className="text-4xl font-black text-white mb-16 tracking-tight">Trusted by Development Teams</h2>
          <div className="grid md:grid-cols-4 gap-12">
            <div>
              <div className="text-6xl font-black text-blue-400 mb-4">500+</div>
              <div className="text-xl text-slate-300 font-medium">Projects Analyzed</div>
            </div>
            <div>
              <div className="text-6xl font-black text-emerald-400 mb-4">10M+</div>
              <div className="text-xl text-slate-300 font-medium">Lines of Code</div>
            </div>
            <div>
              <div className="text-6xl font-black text-amber-400 mb-4">99.9%</div>
              <div className="text-xl text-slate-300 font-medium">Uptime</div>
            </div>
            <div>
              <div className="text-6xl font-black text-purple-400 mb-4">24/7</div>
              <div className="text-xl text-slate-300 font-medium">Support</div>
            </div>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="border-t border-slate-700/50 bg-slate-900/80 backdrop-blur-sm">
        <div className="container mx-auto px-8 py-16">
          <div className="grid md:grid-cols-4 gap-12">
            <div>
              <div className="flex items-center space-x-4 mb-6">
                <div className="text-3xl font-bold text-blue-400">R⚙️</div>
                <span className="text-2xl font-bold text-white">RefactAI</span>
              </div>
              <p className="text-slate-400 text-lg font-light leading-relaxed">
                Professional Java refactoring suite for enterprise development teams.
              </p>
            </div>
            <div>
              <h3 className="text-white font-bold text-lg mb-6">Product</h3>
              <ul className="space-y-3 text-slate-400">
                <li><a href="/dashboard" className="hover:text-white transition-colors duration-200 font-medium">Dashboard</a></li>
                <li><a href="#features" className="hover:text-white transition-colors duration-200 font-medium">Features</a></li>
                <li><a href="#docs" className="hover:text-white transition-colors duration-200 font-medium">Documentation</a></li>
              </ul>
            </div>
            <div>
              <h3 className="text-white font-bold text-lg mb-6">Support</h3>
              <ul className="space-y-3 text-slate-400">
                <li><a href="#" className="hover:text-white transition-colors duration-200 font-medium">Help Center</a></li>
                <li><a href="#" className="hover:text-white transition-colors duration-200 font-medium">Contact Us</a></li>
                <li><a href="#" className="hover:text-white transition-colors duration-200 font-medium">Status</a></li>
              </ul>
            </div>
            <div>
              <h3 className="text-white font-bold text-lg mb-6">Company</h3>
              <ul className="space-y-3 text-slate-400">
                <li><a href="#" className="hover:text-white transition-colors duration-200 font-medium">About</a></li>
                <li><a href="#" className="hover:text-white transition-colors duration-200 font-medium">Blog</a></li>
                <li><a href="#" className="hover:text-white transition-colors duration-200 font-medium">Careers</a></li>
              </ul>
            </div>
          </div>
          <div className="border-t border-slate-700/50 mt-12 pt-12 text-center text-slate-500">
            <p className="text-lg">© 2024 RefactAI. All rights reserved.</p>
          </div>
        </div>
      </footer>
    </div>
  );
}
