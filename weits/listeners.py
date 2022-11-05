def push_weit_to_cache(sender, instance, created, **kwargs):
    # we only push weit to cache when created, not updated
    if not created:
        return

    from weits.services import WeitService
    WeitService.push_weit_to_cache(instance)