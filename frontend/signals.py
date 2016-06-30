import logging

logger = logging.getLogger(__name__)


def document_save_handler(sender, **kwargs):
    raw = kwargs.get('raw', False)
    if raw:
        return
    instance = kwargs.get('instance')
    created = kwargs.get('created')

    logger.info("Document created/updated",
                extra={
                    'document': instance,
                    'doc_created': created,
                })