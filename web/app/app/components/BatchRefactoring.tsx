'use client';

import React, { useState } from 'react';
import { 
  Play, 
  Pause, 
  Square, 
  CheckCircle, 
  AlertTriangle, 
  Clock,
  FileText,
  Zap,
  Settings,
  Download,
  Upload,
  Trash2,
  Edit3,
  Eye
} from 'lucide-react';

interface BatchOperation {
  id: string;
  type: string;
  filePath: string;
  status: 'PENDING' | 'RUNNING' | 'COMPLETED' | 'FAILED' | 'SKIPPED';
  progress: number;
  priority: 'LOW' | 'MEDIUM' | 'HIGH';
  estimatedTime: number;
  riskLevel: 'LOW' | 'MEDIUM' | 'HIGH';
}

interface BatchRefactoringProps {
  workspaceId: string;
  selectedFiles: string[];
  onBatchComplete: () => void;
}

export default function BatchRefactoring({ 
  workspaceId, 
  selectedFiles, 
  onBatchComplete 
}: BatchRefactoringProps) {
  const [operations, setOperations] = useState<BatchOperation[]>([]);
  const [isRunning, setIsRunning] = useState(false);
  const [currentOperation, setCurrentOperation] = useState<string | null>(null);
  const [batchSettings, setBatchSettings] = useState({
    maxConcurrent: 3,
    autoApprove: false,
    stopOnError: true,
    priorityOrder: 'RISK_LEVEL' as 'RISK_LEVEL' | 'FILE_SIZE' | 'ALPHABETICAL'
  });

  // Generate batch operations from selected files
  const generateBatchOperations = () => {
    const batchOps: BatchOperation[] = selectedFiles.map((filePath, index) => ({
      id: `batch-${index}`,
      type: 'EXTRACT_METHOD', // Default operation
      filePath,
      status: 'PENDING' as const,
      progress: 0,
      priority: 'MEDIUM' as const,
      estimatedTime: Math.floor(Math.random() * 300) + 60, // 1-6 minutes
      riskLevel: Math.random() > 0.7 ? 'HIGH' : Math.random() > 0.4 ? 'MEDIUM' : 'LOW' as 'LOW' | 'MEDIUM' | 'HIGH'
    }));

    setOperations(batchOps);
  };

  const startBatchProcessing = async () => {
    setIsRunning(true);
    setCurrentOperation(operations[0]?.id || null);

    for (const operation of operations) {
      if (!isRunning) break; // Allow stopping

      setCurrentOperation(operation.id);
      
      // Update operation status to running
      setOperations(prev => prev.map(op => 
        op.id === operation.id 
          ? { ...op, status: 'RUNNING' as const, progress: 0 }
          : op
      ));

      try {
        // Simulate operation progress
        for (let progress = 0; progress <= 100; progress += 10) {
          if (!isRunning) break;
          
          setOperations(prev => prev.map(op => 
            op.id === operation.id 
              ? { ...op, progress }
              : op
          ));

          await new Promise(resolve => setTimeout(resolve, 200));
        }

        // Mark as completed
        setOperations(prev => prev.map(op => 
          op.id === operation.id 
            ? { ...op, status: 'COMPLETED' as const, progress: 100 }
            : op
        ));

      } catch (error) {
        // Mark as failed
        setOperations(prev => prev.map(op => 
          op.id === operation.id 
            ? { ...op, status: 'FAILED' as const }
            : op
        ));

        if (batchSettings.stopOnError) {
          break;
        }
      }
    }

    setIsRunning(false);
    setCurrentOperation(null);
    onBatchComplete();
  };

  const stopBatchProcessing = () => {
    setIsRunning(false);
    setCurrentOperation(null);
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'COMPLETED': return 'text-green-400 bg-green-500/20 border-green-500/50';
      case 'RUNNING': return 'text-blue-400 bg-blue-500/20 border-blue-500/50';
      case 'FAILED': return 'text-red-400 bg-red-500/20 border-red-500/50';
      case 'PENDING': return 'text-yellow-400 bg-yellow-500/20 border-yellow-500/50';
      case 'SKIPPED': return 'text-gray-400 bg-gray-500/20 border-gray-500/50';
      default: return 'text-gray-400 bg-gray-500/20 border-gray-500/50';
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'COMPLETED': return <CheckCircle className="w-4 h-4" />;
      case 'RUNNING': return <Play className="w-4 h-4 animate-pulse" />;
      case 'FAILED': return <AlertTriangle className="w-4 h-4" />;
      case 'PENDING': return <Clock className="w-4 h-4" />;
      case 'SKIPPED': return <Pause className="w-4 h-4" />;
      default: return <Clock className="w-4 h-4" />;
    }
  };

  const getRiskColor = (risk: string) => {
    switch (risk) {
      case 'LOW': return 'text-green-400';
      case 'MEDIUM': return 'text-yellow-400';
      case 'HIGH': return 'text-red-400';
      default: return 'text-gray-400';
    }
  };

  const completedCount = operations.filter(op => op.status === 'COMPLETED').length;
  const failedCount = operations.filter(op => op.status === 'FAILED').length;
  const totalTime = operations.reduce((sum, op) => sum + op.estimatedTime, 0);

  return (
    <div className="bg-slate-800 rounded-xl p-6 border border-slate-700">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h2 className="text-xl font-bold text-white flex items-center">
            <Zap className="w-5 h-5 mr-2" />
            Batch Refactoring
          </h2>
          <p className="text-slate-400">Process multiple files simultaneously</p>
        </div>
        <div className="flex space-x-2">
          <button
            onClick={generateBatchOperations}
            className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition-colors flex items-center"
          >
            <Settings className="w-4 h-4 mr-2" />
            Generate
          </button>
          <button
            onClick={startBatchProcessing}
            disabled={isRunning || operations.length === 0}
            className="px-4 py-2 bg-green-600 hover:bg-green-700 disabled:bg-green-400 text-white rounded-lg transition-colors flex items-center"
          >
            <Play className="w-4 h-4 mr-2" />
            Start Batch
          </button>
          <button
            onClick={stopBatchProcessing}
            disabled={!isRunning}
            className="px-4 py-2 bg-red-600 hover:bg-red-700 disabled:bg-red-400 text-white rounded-lg transition-colors flex items-center"
          >
            <Square className="w-4 h-4 mr-2" />
            Square
          </button>
        </div>
      </div>

      {/* Batch Settings */}
      <div className="bg-slate-700 rounded-lg p-4 mb-6">
        <h3 className="text-lg font-semibold text-white mb-4">Batch Settings</h3>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div>
            <label className="block text-sm text-slate-400 mb-2">Max Concurrent</label>
            <input
              type="number"
              value={batchSettings.maxConcurrent}
              onChange={(e) => setBatchSettings(prev => ({ ...prev, maxConcurrent: parseInt(e.target.value) }))}
              className="w-full bg-slate-600 border border-slate-500 rounded-lg px-3 py-2 text-white"
              min="1"
              max="10"
            />
          </div>
          <div>
            <label className="block text-sm text-slate-400 mb-2">Priority Order</label>
            <select
              value={batchSettings.priorityOrder}
              onChange={(e) => setBatchSettings(prev => ({ ...prev, priorityOrder: e.target.value as any }))}
              className="w-full bg-slate-600 border border-slate-500 rounded-lg px-3 py-2 text-white"
            >
              <option value="RISK_LEVEL">Risk Level</option>
              <option value="FILE_SIZE">File Size</option>
              <option value="ALPHABETICAL">Alphabetical</option>
            </select>
          </div>
          <div className="flex items-center space-x-2">
            <input
              type="checkbox"
              id="autoApprove"
              checked={batchSettings.autoApprove}
              onChange={(e) => setBatchSettings(prev => ({ ...prev, autoApprove: e.target.checked }))}
              className="w-4 h-4 text-blue-600 bg-slate-600 border-slate-500 rounded"
            />
            <label htmlFor="autoApprove" className="text-sm text-slate-300">Auto Approve</label>
          </div>
          <div className="flex items-center space-x-2">
            <input
              type="checkbox"
              id="stopOnError"
              checked={batchSettings.stopOnError}
              onChange={(e) => setBatchSettings(prev => ({ ...prev, stopOnError: e.target.checked }))}
              className="w-4 h-4 text-blue-600 bg-slate-600 border-slate-500 rounded"
            />
            <label htmlFor="stopOnError" className="text-sm text-slate-300">Square on Error</label>
          </div>
        </div>
      </div>

      {/* Batch Statistics */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
        <div className="bg-slate-700 rounded-lg p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-slate-400 text-sm">Total Operations</p>
              <p className="text-2xl font-bold text-white">{operations.length}</p>
            </div>
            <FileText className="w-8 h-8 text-blue-400" />
          </div>
        </div>

        <div className="bg-slate-700 rounded-lg p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-slate-400 text-sm">Completed</p>
              <p className="text-2xl font-bold text-green-400">{completedCount}</p>
            </div>
            <CheckCircle className="w-8 h-8 text-green-400" />
          </div>
        </div>

        <div className="bg-slate-700 rounded-lg p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-slate-400 text-sm">Failed</p>
              <p className="text-2xl font-bold text-red-400">{failedCount}</p>
            </div>
            <AlertTriangle className="w-8 h-8 text-red-400" />
          </div>
        </div>

        <div className="bg-slate-700 rounded-lg p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-slate-400 text-sm">Est. Time</p>
              <p className="text-2xl font-bold text-white">{Math.round(totalTime / 60)}m</p>
            </div>
            <Clock className="w-8 h-8 text-yellow-400" />
          </div>
        </div>
      </div>

      {/* Operations List */}
      <div className="space-y-3">
        {operations.map((operation) => (
          <div
            key={operation.id}
            className={`bg-slate-700 rounded-lg border border-slate-600 p-4 ${
              currentOperation === operation.id ? 'ring-2 ring-blue-500' : ''
            }`}
          >
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-4">
                <div className="flex items-center space-x-2">
                  {getStatusIcon(operation.status)}
                  <span className={`px-2 py-1 rounded-full text-xs font-medium border ${getStatusColor(operation.status)}`}>
                    {operation.status}
                  </span>
                </div>

                <div>
                  <h3 className="text-white font-medium">{operation.type.replace('_', ' ')}</h3>
                  <p className="text-slate-400 text-sm">{operation.filePath.split('/').pop()}</p>
                </div>

                <div className="flex items-center space-x-4 text-sm text-slate-400">
                  <span className={getRiskColor(operation.riskLevel)}>
                    {operation.riskLevel} Risk
                  </span>
                  <span>{Math.round(operation.estimatedTime / 60)}m</span>
                </div>
              </div>

              <div className="flex items-center space-x-2">
                {operation.status === 'RUNNING' && (
                  <div className="w-32 bg-slate-600 rounded-full h-2">
                    <div 
                      className="bg-blue-500 h-2 rounded-full transition-all duration-300"
                      style={{ width: `${operation.progress}%` }}
                    ></div>
                  </div>
                )}

                <div className="flex space-x-1">
                  <button className="p-1 text-slate-400 hover:text-white transition-colors">
                    <Eye className="w-4 h-4" />
                  </button>
                  <button className="p-1 text-slate-400 hover:text-white transition-colors">
                    <Edit3 className="w-4 h-4" />
                  </button>
                  <button className="p-1 text-slate-400 hover:text-red-400 transition-colors">
                    <Trash2 className="w-4 h-4" />
                  </button>
                </div>
              </div>
            </div>

            {operation.status === 'RUNNING' && (
              <div className="mt-3">
                <div className="flex justify-between text-sm text-slate-400 mb-1">
                  <span>Progress</span>
                  <span>{operation.progress}%</span>
                </div>
                <div className="w-full bg-slate-600 rounded-full h-2">
                  <div 
                    className="bg-blue-500 h-2 rounded-full transition-all duration-300"
                    style={{ width: `${operation.progress}%` }}
                  ></div>
                </div>
              </div>
            )}
          </div>
        ))}
      </div>

      {operations.length === 0 && (
        <div className="text-center py-8">
          <Zap className="w-16 h-16 text-slate-400 mx-auto mb-4" />
          <h3 className="text-lg font-semibold text-white mb-2">No Batch Operations</h3>
          <p className="text-slate-400">Generate batch operations to get started</p>
        </div>
      )}
    </div>
  );
}
