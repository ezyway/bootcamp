import time
from typing import Iterator, Tuple, List, Optional
from metrics import MetricsStore

class BaseProcessor:
    """
    Base class for all processors.
    Provides a consistent interface with built-in observability.
    """
    
    def __init__(self):
        self.state = {}
        self.metrics_store = MetricsStore.get_instance()
        self.processor_tag = self.__class__.__name__
    
    def process(self, lines: Iterator[str]) -> Iterator[Tuple[List[str], str]]:
        """
        Override this in subclasses.
        Yield (tags, line) tuples for next routing step.
        """
        raise NotImplementedError
    
    def __call__(self, lines: Iterator[str]) -> Iterator[Tuple[List[str], str]]:
        """
        Wrapper that adds observability around processor execution.
        This method handles metrics collection, tracing, and error recording.
        """
        for line in lines:
            line_id = ""
            start_time = time.time()
            success = True
            
            try:
                # Start tracing for this line if enabled
                if self.metrics_store.trace_enabled:
                    line_id = self.metrics_store.start_trace(line)
                
                # Process the single line
                single_line_iter = iter([line])
                results = []

                # Process and collect outputs to add detailed trace steps
                for tags, processed_line in self.process(single_line_iter):
                    end_time = time.time()
                    processing_time = end_time - start_time
                    results.append((tags, processed_line))

                    # If tracing enabled, add detailed step info
                    if self.metrics_store.trace_enabled and line_id:
                        self.metrics_store.add_trace_step(
                            line_id=line_id,
                            processor_tag=self.processor_tag,
                            input_content=line,
                            output_content=processed_line,
                            output_tags=tags,
                            processing_time=processing_time
                        )

                # Yield after adding all trace steps
                for tags, processed_line in results:
                    yield tags, processed_line
                    
                # Complete trace for the final output
                if self.metrics_store.trace_enabled and line_id and results:
                    # Use last processed line content
                    final_content = results[-1][1]
                    self.metrics_store.complete_trace(line_id, final_content)
                    
            except Exception as e:
                success = False
                
                # Record the error
                self.metrics_store.record_error(self.processor_tag, e, line)
                
                # Re-raise the exception to maintain existing error handling behavior
                raise e
                
            finally:
                # Record metrics for this processor execution
                execution_time = time.time() - start_time
                self.metrics_store.record_processor_metrics(
                    self.processor_tag, 
                    execution_time, 
                    success
                )

    def set_processor_tag(self, tag: str):
        """Allow custom processor tagging (useful for pipeline config)"""
        self.processor_tag = tag


# Example: LineCounter using standardized BaseProcessor
class LineCounter(BaseProcessor):
    def __init__(self, tag: str = "default"):
        super().__init__()
        self.state["count"] = 0
        self.tag = tag
        # Set custom processor tag for metrics
        self.set_processor_tag(f"LineCounter_{tag}")

    def process(self, lines: Iterator[str]) -> Iterator[Tuple[List[str], str]]:
        for line in lines:
            self.state["count"] += 1
            yield [self.tag], f"{self.state['count']}: {line}"


# Example: Streamify helper for stateless functions
def streamify(fn, tag: str = "default"):
    """
    Wraps a stateless function into a BaseProcessor-compatible callable.
    """
    class StatelessProcessor(BaseProcessor):
        def __init__(self):
            super().__init__()
            self.set_processor_tag(f"Streamify_{fn.__name__ if hasattr(fn, '__name__') else 'anonymous'}")
            
        def process(self, lines: Iterator[str]) -> Iterator[Tuple[List[str], str]]:
            for line in lines:
                yield [tag], fn(line)
    
    return StatelessProcessor()
