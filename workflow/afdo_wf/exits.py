"""Public CLI exit contract and durable failure representation."""
from .common import StopRequested

EXIT_CODES = {
    'success': 0,
    'error': 1,
    'gate': 2,
    'identity': 3,
    'environment': 4,
    'correctness': 5,
    'board-unreachable': 6,
    'recovery-required': 7,
    'lock-timeout': 8,
    'usage': 64,
    'user-abort': 130,
}


def failure_reason(error):
    if isinstance(error, (StopRequested, KeyboardInterrupt)):
        return 'user-abort'
    reason = getattr(error, 'reason', 'error')
    return reason if reason in EXIT_CODES and reason != 'success' else 'error'


def failure_record(error):
    reason = failure_reason(error)
    return dict(status='failed', reason=reason, exit_code=EXIT_CODES[reason], error=str(error))
