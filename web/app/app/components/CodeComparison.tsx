'use client';

import React, { useState } from 'react';
import {
  Code,
  ArrowRight,
  Copy,
  Download,
  Eye,
  EyeOff,
  GitBranch,
  FileText,
  CheckCircle,
  AlertTriangle,
  Info,
  Zap,
  Target,
  Layers,
  ChevronDown,
  ChevronRight,
  X,
  ExternalLink,
  Share2,
  Save,
  RefreshCw
} from 'lucide-react';

interface CodeComparisonProps {
  beforeCode: string;
  afterCode: string;
  title: string;
  description: string;
  changes: {
    added: number;
    removed: number;
    modified: number;
  };
  metrics: {
    complexityBefore: number;
    complexityAfter: number;
    maintainabilityBefore: number;
    maintainabilityAfter: number;
    testabilityBefore: number;
    testabilityAfter: number;
  };
  onApply?: () => void;
  onReject?: () => void;
}

export default function CodeComparison({
  beforeCode,
  afterCode,
  title,
  description,
  changes,
  metrics,
  onApply,
  onReject
}: CodeComparisonProps) {
  const [activeTab, setActiveTab] = useState<'side-by-side' | 'unified' | 'diff'>('side-by-side');
  const [showMetrics, setShowMetrics] = useState(true);
  const [copied, setCopied] = useState<string | null>(null);

  const copyToClipboard = async (text: string, type: string) => {
    try {
      await navigator.clipboard.writeText(text);
      setCopied(type);
      setTimeout(() => setCopied(null), 2000);
    } catch (err) {
      console.error('Failed to copy:', err);
    }
  };

  const getComplexityColor = (complexity: number) => {
    if (complexity <= 3) return 'text-green-400';
    if (complexity <= 7) return 'text-yellow-400';
    return 'text-red-400';
  };

  const getImprovementColor = (before: number, after: number) => {
    if (after > before) return 'text-green-400';
    if (after < before) return 'text-red-400';
    return 'text-slate-400';
  };

  const getImprovementIcon = (before: number, after: number) => {
    if (after > before) return <CheckCircle className="w-4 h-4 text-green-400" />;
    if (after < before) return <AlertTriangle className="w-4 h-4 text-red-400" />;
    return <Info className="w-4 h-4 text-slate-400" />;
  };

  return (
    <div className="bg-slate-800 rounded-lg border border-slate-700">
      {/* Header */}
      <div className="p-6 border-b border-slate-700">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h3 className="text-xl font-bold text-white flex items-center">
              <Code className="w-5 h-5 mr-2 text-blue-400" />
              {title}
            </h3>
            <p className="text-slate-400 mt-1">{description}</p>
          </div>
          <div className="flex space-x-2">
            <button
              onClick={() => setShowMetrics(!showMetrics)}
              className="px-3 py-1 bg-slate-700 hover:bg-slate-600 text-white rounded text-sm flex items-center"
            >
              {showMetrics ? <EyeOff className="w-4 h-4 mr-1" /> : <Eye className="w-4 h-4 mr-1" />}
              {showMetrics ? 'Hide' : 'Show'} Metrics
            </button>
          </div>
        </div>

        {/* Change Statistics */}
        <div className="grid grid-cols-3 gap-4">
          <div className="bg-slate-700 rounded-lg p-3">
            <div className="text-2xl font-bold text-green-400">+{changes.added}</div>
            <div className="text-sm text-slate-400">Lines Added</div>
          </div>
          <div className="bg-slate-700 rounded-lg p-3">
            <div className="text-2xl font-bold text-red-400">-{changes.removed}</div>
            <div className="text-sm text-slate-400">Lines Removed</div>
          </div>
          <div className="bg-slate-700 rounded-lg p-3">
            <div className="text-2xl font-bold text-blue-400">{changes.modified}</div>
            <div className="text-sm text-slate-400">Lines Modified</div>
          </div>
        </div>
      </div>

      {/* Metrics Panel */}
      {showMetrics && (
        <div className="p-6 border-b border-slate-700 bg-slate-900/50">
          <h4 className="text-white font-semibold mb-4 flex items-center">
            <Target className="w-4 h-4 mr-2 text-purple-400" />
            Quality Metrics Comparison
          </h4>
          
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div>
              <h5 className="text-white font-medium mb-3">Complexity</h5>
              <div className="space-y-2">
                <div className="flex items-center justify-between">
                  <span className="text-slate-400">Before:</span>
                  <span className={`${getComplexityColor(metrics.complexityBefore)}`}>
                    {metrics.complexityBefore}
                  </span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-slate-400">After:</span>
                  <span className={`${getComplexityColor(metrics.complexityAfter)}`}>
                    {metrics.complexityAfter}
                  </span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-slate-400">Change:</span>
                  <div className="flex items-center space-x-1">
                    {getImprovementIcon(metrics.complexityBefore, metrics.complexityAfter)}
                    <span className={`${getImprovementColor(metrics.complexityBefore, metrics.complexityAfter)}`}>
                      {metrics.complexityAfter > metrics.complexityBefore ? '+' : ''}
                      {metrics.complexityAfter - metrics.complexityBefore}
                    </span>
                  </div>
                </div>
              </div>
            </div>

            <div>
              <h5 className="text-white font-medium mb-3">Maintainability</h5>
              <div className="space-y-2">
                <div className="flex items-center justify-between">
                  <span className="text-slate-400">Before:</span>
                  <span className="text-slate-300">{metrics.maintainabilityBefore}/100</span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-slate-400">After:</span>
                  <span className="text-slate-300">{metrics.maintainabilityAfter}/100</span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-slate-400">Change:</span>
                  <div className="flex items-center space-x-1">
                    {getImprovementIcon(metrics.maintainabilityBefore, metrics.maintainabilityAfter)}
                    <span className={`${getImprovementColor(metrics.maintainabilityBefore, metrics.maintainabilityAfter)}`}>
                      {metrics.maintainabilityAfter > metrics.maintainabilityBefore ? '+' : ''}
                      {metrics.maintainabilityAfter - metrics.maintainabilityBefore}
                    </span>
                  </div>
                </div>
              </div>
            </div>

            <div>
              <h5 className="text-white font-medium mb-3">Testability</h5>
              <div className="space-y-2">
                <div className="flex items-center justify-between">
                  <span className="text-slate-400">Before:</span>
                  <span className="text-slate-300">{metrics.testabilityBefore}/100</span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-slate-400">After:</span>
                  <span className="text-slate-300">{metrics.testabilityAfter}/100</span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-slate-400">Change:</span>
                  <div className="flex items-center space-x-1">
                    {getImprovementIcon(metrics.testabilityBefore, metrics.testabilityAfter)}
                    <span className={`${getImprovementColor(metrics.testabilityBefore, metrics.testabilityAfter)}`}>
                      {metrics.testabilityAfter > metrics.testabilityBefore ? '+' : ''}
                      {metrics.testabilityAfter - metrics.testabilityBefore}
                    </span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Tab Navigation */}
      <div className="flex border-b border-slate-700">
        {[
          { id: 'side-by-side', label: 'Side by Side', icon: <Code className="w-4 h-4" /> },
          { id: 'unified', label: 'Unified View', icon: <Layers className="w-4 h-4" /> },
          { id: 'diff', label: 'Diff View', icon: <GitBranch className="w-4 h-4" /> }
        ].map(tab => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id as any)}
            className={`flex items-center px-4 py-3 text-sm font-medium transition-colors ${
              activeTab === tab.id
                ? 'text-blue-400 border-b-2 border-blue-400 bg-blue-500/10'
                : 'text-slate-400 hover:text-white hover:bg-slate-700'
            }`}
          >
            {tab.icon}
            <span className="ml-2">{tab.label}</span>
          </button>
        ))}
      </div>

      {/* Code Comparison Content */}
      <div className="p-6">
        {activeTab === 'side-by-side' && (
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <div>
              <div className="flex items-center justify-between mb-3">
                <h4 className="text-white font-semibold flex items-center">
                  <FileText className="w-4 h-4 mr-2 text-red-400" />
                  Before
                </h4>
                <button
                  onClick={() => copyToClipboard(beforeCode, 'before')}
                  className="p-2 text-slate-400 hover:text-white transition-colors"
                  title="Copy code"
                >
                  {copied === 'before' ? <CheckCircle className="w-4 h-4 text-green-400" /> : <Copy className="w-4 h-4" />}
                </button>
              </div>
              <div className="bg-slate-900 rounded-lg p-4 border border-red-500/50">
                <pre className="text-sm text-red-300 overflow-auto max-h-96">
                  {beforeCode}
                </pre>
              </div>
            </div>

            <div>
              <div className="flex items-center justify-between mb-3">
                <h4 className="text-white font-semibold flex items-center">
                  <FileText className="w-4 h-4 mr-2 text-green-400" />
                  After
                </h4>
                <button
                  onClick={() => copyToClipboard(afterCode, 'after')}
                  className="p-2 text-slate-400 hover:text-white transition-colors"
                  title="Copy code"
                >
                  {copied === 'after' ? <CheckCircle className="w-4 h-4 text-green-400" /> : <Copy className="w-4 h-4" />}
                </button>
              </div>
              <div className="bg-slate-900 rounded-lg p-4 border border-green-500/50">
                <pre className="text-sm text-green-300 overflow-auto max-h-96">
                  {afterCode}
                </pre>
              </div>
            </div>
          </div>
        )}

        {activeTab === 'unified' && (
          <div className="space-y-4">
            <div className="bg-slate-900 rounded-lg p-4 border border-slate-600">
              <div className="flex items-center justify-between mb-3">
                <h4 className="text-white font-semibold">Unified View</h4>
                <button
                  onClick={() => copyToClipboard(`${beforeCode}\n\n---\n\n${afterCode}`, 'unified')}
                  className="p-2 text-slate-400 hover:text-white transition-colors"
                  title="Copy code"
                >
                  {copied === 'unified' ? <CheckCircle className="w-4 h-4 text-green-400" /> : <Copy className="w-4 h-4" />}
                </button>
              </div>
              <div className="space-y-4">
                <div>
                  <div className="text-sm text-red-400 font-medium mb-2">Before:</div>
                  <pre className="text-sm text-red-300 bg-slate-800 rounded p-3 overflow-auto max-h-48">
                    {beforeCode}
                  </pre>
                </div>
                <div className="flex items-center justify-center">
                  <ArrowRight className="w-5 h-5 text-slate-400" />
                </div>
                <div>
                  <div className="text-sm text-green-400 font-medium mb-2">After:</div>
                  <pre className="text-sm text-green-300 bg-slate-800 rounded p-3 overflow-auto max-h-48">
                    {afterCode}
                  </pre>
                </div>
              </div>
            </div>
          </div>
        )}

        {activeTab === 'diff' && (
          <div className="bg-slate-900 rounded-lg p-4 border border-slate-600">
            <div className="flex items-center justify-between mb-3">
              <h4 className="text-white font-semibold">Diff View</h4>
              <button
                onClick={() => copyToClipboard(`--- Before\n${beforeCode}\n\n+++ After\n${afterCode}`, 'diff')}
                className="p-2 text-slate-400 hover:text-white transition-colors"
                title="Copy diff"
              >
                {copied === 'diff' ? <CheckCircle className="w-4 h-4 text-green-400" /> : <Copy className="w-4 h-4" />}
              </button>
            </div>
            <div className="text-sm">
              <div className="text-red-400 mb-2">--- Before</div>
              <pre className="text-red-300 bg-slate-800 rounded p-3 overflow-auto max-h-48 mb-4">
                {beforeCode}
              </pre>
              <div className="text-green-400 mb-2">+++ After</div>
              <pre className="text-green-300 bg-slate-800 rounded p-3 overflow-auto max-h-48">
                {afterCode}
              </pre>
            </div>
          </div>
        )}
      </div>

      {/* Action Buttons */}
      <div className="p-6 border-t border-slate-700 bg-slate-900/50">
        <div className="flex items-center justify-between">
          <div className="flex space-x-3">
            <button
              onClick={() => copyToClipboard(afterCode, 'final')}
              className="px-4 py-2 bg-slate-700 hover:bg-slate-600 text-white rounded-lg transition-colors flex items-center"
            >
              <Copy className="w-4 h-4 mr-2" />
              Copy Refactored Code
            </button>
            <button className="px-4 py-2 bg-slate-700 hover:bg-slate-600 text-white rounded-lg transition-colors flex items-center">
              <Download className="w-4 h-4 mr-2" />
              Download
            </button>
            <button className="px-4 py-2 bg-slate-700 hover:bg-slate-600 text-white rounded-lg transition-colors flex items-center">
              <Share2 className="w-4 h-4 mr-2" />
              Share
            </button>
          </div>
          
          <div className="flex space-x-3">
            {onReject && (
              <button
                onClick={onReject}
                className="px-4 py-2 bg-red-600 hover:bg-red-700 text-white rounded-lg transition-colors flex items-center"
              >
                <X className="w-4 h-4 mr-2" />
                Reject Changes
              </button>
            )}
            {onApply && (
              <button
                onClick={onApply}
                className="px-4 py-2 bg-green-600 hover:bg-green-700 text-white rounded-lg transition-colors flex items-center"
              >
                <CheckCircle className="w-4 h-4 mr-2" />
                Apply Changes
              </button>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}