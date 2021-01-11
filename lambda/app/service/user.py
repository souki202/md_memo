
def check_is_in_share_target(user_id: str, share_targets: str) -> bool:
    if not share_targets or not user_id:
        return False
    target_users = share_targets.replace(' ', '').split(',')
    return user_id in target_users