import os


def physical_core_estimate() -> int:
    """Logical CPUs usable by the process, assuming 2 hyper-threads per physical core.

    Inference libraries (torch) run up to 10x slower when given every hyper-thread.
    """
    return max(1, len(os.sched_getaffinity(0)) // 2)
