class ConversationMemory:

    def __init__(self, limit=6):

        # store conversation history
        self.history = []

        # maximum number of interactions to keep
        self.limit = limit


    # ---------------------------------------------------
    # Add interaction
    # ---------------------------------------------------

    def add(self, question, answer):

        self.history.append({
            "question": question,
            "answer": answer
        })

        # keep only recent memory
        if len(self.history) > self.limit:
            self.history = self.history[-self.limit:]


    # ---------------------------------------------------
    # Return memory summary
    # ---------------------------------------------------

    def summary(self):

        if not self.history:
            return ""

        summary_text = ""

        for item in self.history:

            q = item["question"]
            a = item["answer"][:500]   # prevent long prompts

            summary_text += f"User: {q}\n"
            summary_text += f"Assistant: {a}\n\n"

        return summary_text

    # ---------------------------------------------------
    # Return memory Last
    # ---------------------------------------------------

    def last(self):

        if not self.history:
            return None, None

        last_turn = self.history[-1]

        return last_turn["question"], last_turn["answer"]

    # ---------------------------------------------------
    # Clear memory
    # ---------------------------------------------------

    def clear(self):

        self.history = []