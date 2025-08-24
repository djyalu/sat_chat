// 스택 오버플로우 디버깅 스크립트 v2 - 실제 호출 스택 추적
console.log('🔍 Stack Overflow Debug Script v2 Started');

// 1. 원본 함수들을 래핑해서 호출 패턴 추적
const originalConsoleLogs = [];
let callStack = [];
let maxStackDepth = 0;
let recursivePatterns = new Map();

// 함수 호출 추적기
function wrapFunction(obj, functionName, context = '') {
    if (!obj || !obj[functionName] || typeof obj[functionName] !== 'function') {
        console.log(`❌ Cannot wrap ${context}.${functionName} - not found`);
        return;
    }
    
    const original = obj[functionName];
    obj[functionName] = function(...args) {
        const callId = `${context}.${functionName}`;
        const depth = callStack.length;
        
        // 스택 깊이 추적
        callStack.push(callId);
        maxStackDepth = Math.max(maxStackDepth, depth);
        
        // 재귀 패턴 감지
        const stackStr = callStack.slice(-5).join(' → ');
        recursivePatterns.set(stackStr, (recursivePatterns.get(stackStr) || 0) + 1);
        
        console.log(`📞 [${depth}] ${callId}(${args.length} args)`);
        
        // 위험 수준 체크
        if (depth > 100) {
            console.error(`🚨 DANGER: Call stack depth ${depth} in ${callId}`);
            console.error('🔄 Recent calls:', stackStr);
            debugger; // 브라우저에서 멈춤
        }
        
        let result;
        try {
            result = original.apply(this, args);
        } catch (error) {
            console.error(`💥 Error in ${callId}:`, error);
            console.error('📚 Full call stack:', callStack.join(' → '));
            throw error;
        } finally {
            callStack.pop();
        }
        
        return result;
    };
    
    console.log(`✅ Wrapped ${context}.${functionName}`);
}

// 2. 주요 함수들 래핑
setTimeout(() => {
    console.log('🔧 Starting function wrapping...');
    
    // 전역 함수들
    if (window.loadClientAnalysis) wrapFunction(window, 'loadClientAnalysis', 'window');
    if (window.safeAnalysisExecution) wrapFunction(window, 'safeAnalysisExecution', 'window');
    
    // ClientMarineAnalyzer 클래스 메소드들
    if (window.clientAnalyzer || window.getClientAnalyzer) {
        const analyzer = window.clientAnalyzer || window.getClientAnalyzer();
        if (analyzer) {
            wrapFunction(analyzer, 'performCompleteAnalysis', 'ClientMarineAnalyzer');
            wrapFunction(analyzer, 'calculateEnhancedIndices', 'ClientMarineAnalyzer');
            wrapFunction(analyzer, 'processImageTiles', 'ClientMarineAnalyzer');
            wrapFunction(analyzer, 'calculateStatistics', 'ClientMarineAnalyzer');
            wrapFunction(analyzer, 'detectDebrisHotspots', 'ClientMarineAnalyzer');
            wrapFunction(analyzer, 'createIndexVisualization', 'ClientMarineAnalyzer');
            wrapFunction(analyzer, 'generateRealisticOceanData', 'ClientMarineAnalyzer');
            wrapFunction(analyzer, 'simulateMLPredictions', 'ClientMarineAnalyzer');
            wrapFunction(analyzer, 'initializeModel', 'ClientMarineAnalyzer');
        }
    }
    
    // Array prototype 메소드들 (의심되는 부분)
    const ArrayProto = Array.prototype;
    const originalReduce = ArrayProto.reduce;
    ArrayProto.reduce = function(callback, initialValue) {
        const depth = callStack.length;
        if (depth > 50) {
            console.warn(`⚠️ Array.reduce called at depth ${depth}, array length: ${this.length}`);
        }
        return originalReduce.apply(this, arguments);
    };
    
    // Math 함수들
    const originalMin = Math.min;
    const originalMax = Math.max;
    Math.min = function(...args) {
        if (args.length > 1000000) {
            console.warn(`⚠️ Math.min called with ${args.length} arguments`);
        }
        return originalMin.apply(this, args);
    };
    Math.max = function(...args) {
        if (args.length > 1000000) {
            console.warn(`⚠️ Math.max called with ${args.length} arguments`);
        }
        return originalMax.apply(this, args);
    };
    
    console.log('✅ Function wrapping completed');
}, 1000);

// 3. 주기적 상태 모니터링
setInterval(() => {
    console.log(`📊 Max stack depth: ${maxStackDepth}, Current: ${callStack.length}`);
    
    // 재귀 패턴 분석
    const suspiciousPatterns = Array.from(recursivePatterns.entries())
        .filter(([pattern, count]) => count > 10)
        .sort(([,a], [,b]) => b - a);
    
    if (suspiciousPatterns.length > 0) {
        console.warn('🔄 Suspicious recursive patterns detected:');
        suspiciousPatterns.forEach(([pattern, count]) => {
            console.warn(`  ${count}x: ${pattern}`);
        });
    }
}, 5000);

// 4. 오류 감지기
window.addEventListener('error', (event) => {
    if (event.message.includes('Maximum call stack size exceeded')) {
        console.error('💥 STACK OVERFLOW DETECTED!');
        console.error('📚 Call stack at time of overflow:', callStack.join(' → '));
        console.error('🔄 Recursive patterns:', Array.from(recursivePatterns.entries()));
        console.error('📊 Max depth reached:', maxStackDepth);
        
        // 스택 리셋
        callStack = [];
        maxStackDepth = 0;
        recursivePatterns.clear();
    }
});

console.log('🟢 Debug script v2 ready - will trace all function calls');