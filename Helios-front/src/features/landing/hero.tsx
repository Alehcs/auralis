import { motion } from 'motion/react';
import { Sun, Zap } from 'lucide-react';

export function Hero() {
  return (
    <div className="relative overflow-hidden rounded-2xl bg-gradient-to-br from-orange-600/20 via-purple-900/20 to-blue-900/20 border border-white/10 p-8 mb-6">
      <div className="absolute inset-0 opacity-20">
        <div className="absolute top-0 left-0 w-96 h-96 bg-orange-500 rounded-full blur-3xl" />
        <div className="absolute bottom-0 right-0 w-96 h-96 bg-blue-500 rounded-full blur-3xl" />
      </div>
      
      <div className="relative z-10">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6 }}
          className="flex items-center space-x-4 mb-4"
        >
          <div className="w-16 h-16 rounded-full bg-gradient-to-br from-orange-400 to-yellow-500 flex items-center justify-center animate-pulse">
            <Sun className="w-8 h-8 text-white" />
          </div>
          <div>
            <h1 className="text-4xl font-bold text-white mb-1">HeliosPipeline</h1>
            <p className="text-lg text-gray-300">Solar Activity Prediction & Space Weather Intelligence</p>
          </div>
        </motion.div>

        <div className="grid grid-cols-4 gap-4 mt-6">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.1 }}
            className="bg-white/5 backdrop-blur-sm rounded-lg p-4 border border-white/10"
          >
            <div className="flex items-center space-x-2 mb-2">
              <Zap className="w-4 h-4 text-yellow-400" />
              <span className="text-xs text-gray-400">Solar Activity</span>
            </div>
            <p className="text-2xl font-bold text-white">Medium</p>
          </motion.div>

          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.2 }}
            className="bg-white/5 backdrop-blur-sm rounded-lg p-4 border border-white/10"
          >
            <p className="text-xs text-gray-400 mb-2">Active Regions</p>
            <p className="text-2xl font-bold text-white">12</p>
          </motion.div>

          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.3 }}
            className="bg-white/5 backdrop-blur-sm rounded-lg p-4 border border-white/10"
          >
            <p className="text-xs text-gray-400 mb-2">Sunspot Number</p>
            <p className="text-2xl font-bold text-white">87</p>
          </motion.div>

          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.4 }}
            className="bg-white/5 backdrop-blur-sm rounded-lg p-4 border border-white/10"
          >
            <p className="text-xs text-gray-400 mb-2">Prediction Accuracy</p>
            <p className="text-2xl font-bold text-green-400">94.2%</p>
          </motion.div>
        </div>
      </div>
    </div>
  );
}
