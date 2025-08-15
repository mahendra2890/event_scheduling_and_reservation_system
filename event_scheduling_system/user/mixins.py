from .models import HistoryPoint


class HistoryLoggingMixin:
    """
    Mixin to provide history logging capability to any model.
    
    This mixin adds a log_history() method that can be used to manually
    log actions with full context (user, action, details).
    
    Usage:
        class MyModel(HistoryLoggingMixin, models.Model):
            pass
            
        # In serializer or view:
        instance.log_history(
            user=request.user,
            action='create',
            details={'field': 'value'}
        )
    """
    
    def log_history(self, user, action, details=None):
        """
        Log a history point for this instance.
        
        Args:
            user: The user who performed the action
            action: The action performed (e.g., 'create', 'update', 'delete')
            details: Optional dictionary with additional context
            
        Returns:
            HistoryPoint: The created history point instance
        """
        return HistoryPoint.log_action(
            user=user,
            action=action,
            obj=self,
            details=details or {}
        )
