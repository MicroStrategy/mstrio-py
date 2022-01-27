from mstrio.connection import Connection
from mstrio.distribution_services import (CacheUpdateSubscription, Content,
                                          list_subscriptions, CacheType)


# create new cache update subscription
def cache_update_subscription_workflow(conn: "Connection") -> None:
    recipients_ids = ["recipient_id"]
    schedules_ids = ["schedule_id"]
    content_id = "content_id"
    content_type = Content.Type.REPORT
    content_prop = Content.Properties(
        format_type=Content.Properties.FormatType.EXCEL
    )

    content = Content(
        type=content_type,
        id=content_id,
        personalization=content_prop,
    )
    cache_update_sub = CacheUpdateSubscription.create(
        connection=conn, project_name=conn.project_name,
        name=f'Validation_{content_type.value}_{content_id}_CACHE',
        contents=content, schedules=schedules_ids,
        delivery_expiration_date='2025-12-31', send_now=True,
        recipients=recipients_ids, cache_cache_type=CacheType.RESERVED)

    # list cache update subscriptions
    cache_update_subs = [
        sub for sub in list_subscriptions(conn, project_name=conn.project_name)
        if isinstance(sub, CacheUpdateSubscription)
    ]
    for sub in cache_update_subs:
        print(sub)

    # trigger execution of cache update subscription
    cache_update_sub.execute()

    # show dictionary representation of cache update subscription
    print("\nDictionary representation of cache update subscription:")
    print(f"{cache_update_sub.to_dict()}\n")

    # change name of cache update subscription
    old_name = cache_update_sub.name
    new_name = f"{old_name} (Altered)"
    cache_update_sub.alter(name=new_name)
    print(f"Old name: '{old_name}'")
    print(f"New name: '{cache_update_sub.name}'\n")

    # change owner of cache update subscription
    new_owner_id = "new_owner_id"
    old_owner = cache_update_sub.owner
    cache_update_sub.alter(owner_id=new_owner_id)
    print(f"Old owner: '{old_owner.name}'")
    print(f"New owner: '{cache_update_sub.owner.name}'\n")

    # delete cache update subscription
    cache_update_sub.delete(force=True)
