from langpoem import Graph, OpenAI, SQLiteMemory

def build_graph():
    graph = (
        Graph("SupportAgent")
            .llm(OpenAI())
            .memory(SQLiteMemory())
            .agent("planner")
                .prompt("Plan the task")
            .agent("coder")
                .prompt("Write code")
            .agent("reviewer")
                .prompt("Review output")
            .flow("planner >> coder >> reviewer")
            .build()
    )
    return graph
