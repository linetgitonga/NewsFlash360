from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils.text import Truncator
from .models import Post, Comment, Report
import logging

logger = logging.getLogger(__name__)


@receiver(post_save, sender=Post)
def create_post_summary(sender, instance, created, **kwargs):
    """
    Auto-generate a summary for the post if it doesn't have one
    """
    if not instance.summary and instance.content:
        # Create a simple summary by truncating the content
        # In a production system, you might want to use an AI-based summarization here
        instance.summary = Truncator(instance.content).words(30)
        # Use update to avoid triggering the signal again
        Post.objects.filter(pk=instance.pk).update(summary=instance.summary)
        logger.info(f"Generated summary for post {instance.pk}")


@receiver(post_save, sender=Report)
def handle_report_creation(sender, instance, created, **kwargs):
    """
    Process new report submissions
    """
    if created:
        # Log the report
        target = f"post '{instance.post.title}'" if instance.post else f"comment by {instance.comment.author}"
        logger.info(f"New {instance.reason} report by {instance.reporter} on {target}")
        
        # You could implement auto-moderation here
        # For example, flag content after a certain number of reports
        if instance.post:
            report_count = Report.objects.filter(post=instance.post, resolved=False).count()
            if report_count >= 5:  # Threshold for auto-flagging
                instance.post.status = 'flagged'
                instance.post.save(update_fields=['status'])
                logger.warning(f"Post {instance.post.pk} auto-flagged due to {report_count} reports")
        
        elif instance.comment:
            report_count = Report.objects.filter(comment=instance.comment, resolved=False).count()
            if report_count >= 3:  # Lower threshold for comments
                instance.comment.active = False
                instance.comment.save(update_fields=['active'])
                logger.warning(f"Comment {instance.comment.pk} auto-deactivated due to {report_count} reports")