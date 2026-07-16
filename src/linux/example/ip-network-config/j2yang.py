def alter_context(context):
    if "data" not in context:
        return {"data": context}
    else:
        return context
