def retrieve(mail_store, msg_id):
    target = mail_store.get(msg_id)
    if not target:
        return [], "not_found"
    earlier = [m for m in mail_store.thread(target["thread_id"]) if m["timestamp"] < target["timestamp"]]
    if earlier:
        return earlier, "thread-walk"
    # Fallback only when the same-thread history is empty.
    words = [w.lower() for w in target["subject"].split() if len(w) > 3]
    return mail_store.search(words[:3]), "keyword"
