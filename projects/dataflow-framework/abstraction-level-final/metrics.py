import threading
import time
import traceback
from collections import deque, defaultdict
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
import os
import psutil  # For memory metrics

@dataclass
class TraceStep:
    """Individual step in a line's journey"""
    processor: str
    input_content: str
    output_content: str
    output_tags: List[str]
    timestamp: float
    processing_time: float

@dataclass
class TraceEntry:
    """Enhanced trace entry for a line's journey through the system"""
    line_id: str
    original_content: str
    final_content: str
    steps: List[TraceStep]
    path: List[str]  # sequence of processor tags visited
    all_tags: List[str]  # all output tags generated during journey
    start_timestamp: float
    end_timestamp: float
    total_time: float

@dataclass
class ErrorEntry:
    """Single error entry"""
    processor: str
    message: str
    stack_trace: str
    timestamp: float
    line_content: Optional[str] = None

@dataclass
class ProcessorMetrics:
    """Metrics for a single processor"""
    count: int = 0
    total_time: float = 0.0
    errors: int = 0
    avg_time: float = 0.0
    last_seen: Optional[float] = None
    memory_usage_mb: float = 0.0

class MetricsStore:
    """Thread-safe singleton store for all observability data"""
    
    _instance = None
    _lock = threading.Lock()
    
    def __init__(self, max_traces: int = 1000, max_errors: int = 100):
        self.max_traces = max_traces
        self.max_errors = max_errors
        
        # Metrics per processor
        self.metrics: Dict[str, ProcessorMetrics] = defaultdict(ProcessorMetrics)
        
        # Traces and errors
        self.traces: deque = deque(maxlen=max_traces)
        self.errors: deque = deque(maxlen=max_errors)
        
        # Configuration
        self.trace_enabled = self._get_trace_config()
        
        # Thread safety
        self.mutex = threading.Lock()
        
        # Enhanced line tracking for traces
        self._active_traces: Dict[str, dict] = {}  # line_id -> trace_info
        self._line_counter = 0
        
        # Memory tracking
        try:
            self._process = psutil.Process()
            self._start_memory = self._process.memory_info().rss / 1024 / 1024  # MB
        except Exception:
            self._process = None
            self._start_memory = 0.0

        # File queue tracking (for Level 8)
        self.current_file: Optional[str] = None
        # store (filename, timestamp)
        self._last_processed_files: deque = deque(maxlen=200)

    @classmethod
    def get_instance(cls, max_traces: int = 1000, max_errors: int = 100) -> 'MetricsStore':
        """Get singleton instance"""
        with cls._lock:
            if cls._instance is None:
                cls._instance = MetricsStore(max_traces, max_errors)
            return cls._instance
    
    def _get_trace_config(self) -> bool:
        """Check if tracing is enabled via environment variable"""
        return os.getenv('TRACE_ENABLED', 'false').lower() in ('true', '1', 'yes')
    
    def set_trace_enabled(self, enabled: bool):
        """Enable/disable tracing"""
        with self.mutex:
            self.trace_enabled = enabled
    
    def start_trace(self, line_content: str) -> str:
        """Start tracing a new line, return line_id"""
        if not self.trace_enabled:
            return ""
            
        with self.mutex:
            self._line_counter += 1
            line_id = f"line_{self._line_counter}"
            self._active_traces[line_id] = {
                'original_content': line_content,
                'steps': [],
                'path': [],
                'all_tags': [],
                'start_time': time.time()
            }
            return line_id
    
    def add_trace_step(self, line_id: str, processor_tag: str, input_content: str, 
                      output_content: str, output_tags: List[str], processing_time: float):
        """Add a detailed step to an active trace"""
        if not self.trace_enabled or not line_id:
            return
            
        with self.mutex:
            if line_id in self._active_traces:
                trace_info = self._active_traces[line_id]
                
                step = TraceStep(
                    processor=processor_tag,
                    input_content=input_content,
                    output_content=output_content,
                    output_tags=output_tags,
                    timestamp=time.time(),
                    processing_time=processing_time
                )
                
                trace_info['steps'].append(step)
                trace_info['path'].append(processor_tag)
                trace_info['all_tags'].extend(output_tags)
    
    def complete_trace(self, line_id: str, final_content: str):
        """Complete a trace and store it"""
        if not self.trace_enabled or not line_id:
            return
            
        with self.mutex:
            if line_id in self._active_traces:
                trace_info = self._active_traces.pop(line_id)
                end_time = time.time()
                total_time = end_time - trace_info['start_time']
                
                trace_entry = TraceEntry(
                    line_id=line_id,
                    original_content=trace_info['original_content'],
                    final_content=final_content,
                    steps=trace_info['steps'],
                    path=trace_info['path'],
                    all_tags=list(set(trace_info['all_tags'])),  # Remove duplicates
                    start_timestamp=trace_info['start_time'],
                    end_timestamp=end_time,
                    total_time=total_time
                )
                self.traces.append(trace_entry)
    
    def record_processor_metrics(self, processor_tag: str, execution_time: float, success: bool = True):
        """Record metrics for a processor execution"""
        with self.mutex:
            metrics = self.metrics[processor_tag]
            metrics.count += 1
            metrics.total_time += execution_time
            metrics.avg_time = metrics.total_time / metrics.count
            metrics.last_seen = time.time()
            
            # Update memory usage
            try:
                if self._process is not None:
                    current_memory = self._process.memory_info().rss / 1024 / 1024  # MB
                    metrics.memory_usage_mb = current_memory - self._start_memory
            except Exception:
                pass  # Ignore memory tracking errors
            
            if not success:
                metrics.errors += 1
    
    def record_error(self, processor_tag: str, error: Exception, line_content: Optional[str] = None):
        """Record an error"""
        with self.mutex:
            error_entry = ErrorEntry(
                processor=processor_tag,
                message=str(error),
                stack_trace=traceback.format_exc(),
                timestamp=time.time(),
                line_content=line_content
            )
            self.errors.append(error_entry)
            
            # Also update processor error count
            self.metrics[processor_tag].errors += 1
    
    def get_stats(self) -> Dict[str, Any]:
        """Get current statistics"""
        with self.mutex:
            return {
                processor: asdict(metrics)
                for processor, metrics in self.metrics.items()
            }
    
    def get_traces(self, limit: int = 100, search: str = "", processor_filter: str = "", 
                   tag_filter: str = "") -> List[Dict[str, Any]]:
        """Get recent traces with search and filter capabilities"""
        with self.mutex:
            traces = list(self.traces)
            
            # Apply filters
            if search:
                search_lower = search.lower()
                traces = [
                    t for t in traces 
                    if (search_lower in t.original_content.lower() or 
                        search_lower in t.final_content.lower() or
                        any(search_lower in step.input_content.lower() or 
                            search_lower in step.output_content.lower() 
                            for step in t.steps))
                ]
            
            if processor_filter:
                traces = [t for t in traces if processor_filter in t.path]
            
            if tag_filter:
                traces = [t for t in traces if tag_filter in t.all_tags]
            
            # Get most recent and convert to dict
            recent_traces = traces[-limit:] if traces else []
            return [asdict(trace) for trace in recent_traces]
    
    def get_errors(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get recent errors"""
        with self.mutex:
            errors = list(self.errors)[-limit:]
            return [asdict(error) for error in errors]
    
    def get_memory_stats(self) -> Dict[str, float]:
        """Get current memory statistics"""
        try:
            if self._process is None:
                return {
                    "current_memory_mb": 0,
                    "peak_memory_mb": 0, 
                    "memory_percent": 0,
                    "start_memory_mb": self._start_memory,
                    "memory_growth_mb": 0
                }
            memory_info = self._process.memory_info()
            peak = 0
            if hasattr(memory_info, 'peak_wset'):
                peak = memory_info.peak_wset / 1024 / 1024
            return {
                "current_memory_mb": memory_info.rss / 1024 / 1024,
                "peak_memory_mb": peak,
                "memory_percent": self._process.memory_percent(),
                "start_memory_mb": self._start_memory,
                "memory_growth_mb": (memory_info.rss / 1024 / 1024) - self._start_memory
            }
        except Exception:
            return {
                "current_memory_mb": 0,
                "peak_memory_mb": 0, 
                "memory_percent": 0,
                "start_memory_mb": self._start_memory,
                "memory_growth_mb": 0
            }
    
    def get_processors(self) -> List[Dict[str, Any]]:
        """Get list of all processors with their basic info"""
        with self.mutex:
            processors = []
            for processor_tag, metrics in self.metrics.items():
                processors.append({
                    "name": processor_tag,
                    "count": metrics.count,
                    "errors": metrics.errors,
                    "avg_time": metrics.avg_time,
                    "last_seen": metrics.last_seen,
                    "status": "active" if metrics.last_seen and (time.time() - metrics.last_seen) < 60 else "idle"
                })
            return sorted(processors, key=lambda x: x["name"])
    
    def clear_metrics(self):
        """Clear all metrics (useful for testing)"""
        with self.mutex:
            self.metrics.clear()
            self.traces.clear()
            self.errors.clear()
            self._active_traces.clear()
            self._line_counter = 0
            self.current_file = None
            self._last_processed_files.clear()

    # ------------------ File queue tracking API (Level 8) ------------------
    def set_current_file(self, filename: Optional[str]):
        """Set the filename currently being processed (or None)."""
        with self.mutex:
            self.current_file = filename
    
    def record_processed_file(self, filename: str):
        """Record a file that finished processing successfully with timestamp."""
        with self.mutex:
            self._last_processed_files.append((filename, time.time()))
            # clear current file if it matches
            if self.current_file == filename:
                self.current_file = None
    
    def get_file_stats(self, last_n: int = 10) -> Dict[str, Any]:
        """Return file-related stats for dashboard consumption."""
        with self.mutex:
            last = list(self._last_processed_files)[-last_n:]
            return {
                "current_file": self.current_file,
                "last_processed": [
                    {"filename": fn, "timestamp": ts} for fn, ts in reversed(last)
                ]
            }

    def list_last_processed(self, n: int = 10) -> List[Tuple[str, float]]:
        with self.mutex:
            return list(self._last_processed_files)[-n:]
