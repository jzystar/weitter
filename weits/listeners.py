def push_weit_to_cache(sender, instance, created, **kwargs):
    if not created:
        return

    from weits.services import WeitService
    WeitService.push_weit_to_cache(instance)