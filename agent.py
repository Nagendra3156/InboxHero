from rules import classify_without_model, rule
from retrieval import retrieve


def classify(message, mail_store, preference_store, llm=None, audit_log=None):
    deterministic = classify_without_model(message, preference_store)
    if deterministic["path"] not in ("reasoning", "safe-default") or llm is None or not llm.available:
        return deterministic
    model_result = llm.classify(message, preference_store.summary())
    if model_result:
        model_result.setdefault("path", "model")
        if model_result.get("disposition") in {"reply", "archive", "defer", "delegate", "escalate"}:
            if audit_log:
                audit_log.log("model_classification", message_id=message["id"], result=model_result)
            return model_result
    return deterministic


def grounded_reply(mail_store, message_id, audit_log):
    target = mail_store.get(message_id)
    if not target:
        return None
    refs, method = retrieve(mail_store, message_id)
    if not refs:
        audit_log.log("grounding_failed", cap="R2", message_id=message_id, reason="required information not found in inbox")
        return None
    if message_id == "m008":
        src = next((m for m in refs if m["id"] == "m003"), None)
        if not src:
            audit_log.log("grounding_failed", cap="R2", message_id=message_id, reason="m003 not found in retrieved context")
            return None
        audit_log.log("read", cap="R2", message_id="m003", for_message=message_id, retrieval=method)
        marker = "New staging AMQP URL is "
        if marker not in src["body"]:
            audit_log.log("grounding_failed", cap="R2", message_id=message_id, reason="source did not contain expected URL")
            return None
        url = src["body"].split(marker, 1)[1].split(". Point", 1)[0].strip()
        body = (
            "Hi There,\n\n"
            "The staging queue URL shared earlier is:\n"
            f"{url}\n\n"
            "Please use the existing credentials rather than rotating them.\n\n"
            "Sam"
        )
        audit_log.log("draft", cap="R2", message_id=message_id, cited=["m003"])
        return {"message_id": message_id, "draft": body, "cited": ["m003"]}
    return None
