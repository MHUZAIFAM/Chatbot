def update_item_memory(memory, item_id, question, limit):

    if item_id not in memory:
        memory[item_id] = []

    memory[item_id].append(question)

    if len(memory[item_id]) > limit:
        memory[item_id] = memory[item_id][-limit:]


def update_general_memory(memory, question, limit):

    memory.append(question)

    if len(memory) > limit:
        memory[:] = memory[-limit:]